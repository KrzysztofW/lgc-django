#!/usr/bin/python3

from tcp_socket import TcpClient, TcpServer
from lgc_types import LGCError, ReqAction, ReqType
import sys
import json
import os
import mysql.connector
import time
import datetime
import codecs
import smtplib
from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

lgc_url = "https://www.example.com"

def read_template(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

def send_email(first_name, last_name, email, token, lang):
    lang = lang.lower()
    file_tpl_txt = "message_employee_" + lang + ".txt"
    file_tpl_html = "message_employee_" + lang + ".html"

    if lang == "fr":
        url = lgc_url
    else:
        url = lgc_url + '/' + lang
    url += "/lgc?token=" + token

    try:
        tpl = read_template(file_tpl_txt)
        message_txt = tpl.substitute(PERSON_NAME=first_name + " " + last_name,
                                     TOKEN=token, URL=url)
        tpl = read_template(file_tpl_html)
        message_html = tpl.substitute(PERSON_NAME=first_name + " " + last_name,
                                      TOKEN=token, URL=url)

        msg = MIMEMultipart('alternative')
        msg['From'] = "Office <no-reply@example.com>"
        msg['To'] = email
        msg['Subject'] = "Initiate a case"
        msg.attach(MIMEText(message_txt, 'plain'))
        msg.attach(MIMEText(message_html, 'html'))

        s = smtplib.SMTP(host='localhost', port=25)
        s.send_message(msg)
        return LGCError.OK
    except:
        return LGCError.MAILFAIL

def db_delete_resps(cursor, req_id):
    sql = "DELETE from kwav_lgc_resp WHERE id=%s"
    sql_data = (req_id, )

    cursor.execute(sql, sql_data)

def db_insert_resps(cursor, req_id, resps):
    sql = "INSERT INTO kwav_lgc_resp (id, resp) VALUES (%s, %s)"

    for r in resps:
        if r == "":
            continue
        sql_data = (req_id, r)
        cursor.execute(sql, sql_data)

def db_insert_user(cursor, token, req_type, lang, email, first_name, last_name,
                   company):
    sql = ("INSERT INTO kwav_lgc_user (first_name, last_name, company, "
           "email, token, token_ts, lang, role) VALUES "
           "(%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s)")
    sql_data = (first_name, last_name, company, email, token, lang,
                req_type)
    print(sql)
    print(sql_data)
    cursor.execute(sql, sql_data)
    return cursor.lastrowid

def db_update_user(cursor, token, req_type, lang, email, first_name, last_name,
                   company):
    sql = ("UPDATE kwav_lgc_user SET first_name=%s, "
           "last_name=%s, company=%s, token=%s, "
           "token_ts=CURRENT_TIMESTAMP, lang=%s, role=%s "
           "WHERE email=%s")
    sql_data = (first_name, last_name, company, token, lang, req_type, email)

    cursor.execute(sql, sql_data)
    sql = "SELECT id from kwav_lgc_user where email=%s"
    sql_data = (email, )

    cursor.execute(sql, sql_data)
    row = cursor.fetchone()
    if len(row) != 1:
        raise ValueError
    return row[0]

def db_delete_user(cursor, email):
    sql = "DELETE from kwav_lgc_user WHERE email=%s"
    sql_data = (email, )

    cursor.execute(sql, sql_data)

def db_commit_and_close(cursor, mydb):
    mydb.commit()
    cursor.close()
    mydb.close()

def lgc_insert_to_db(req_type, action, lang, email, first_name, last_name,
                     company, resps, relations = None):
    req_id = -1

    if len(resps) == 0:
        return LGCError.INVALID_DATA

    if (req_type != ReqType.CASE and req_type != ReqType.HR):
        return LGCError.INVALID_DATA

    if (action != ReqAction.ADD and action != ReqAction.UPDATE and
        action != ReqAction.DELETE):
        return LGCError.INVALID_DATA

    token = codecs.encode(os.urandom(32), 'hex').decode()
    # check for collisions

    mydb = mysql.connector.connect(
        host="localhost", database="database",
        user="database", passwd="XXXXXXXXXXX"
    )

    cursor = mydb.cursor()
    try:
        if action == ReqAction.ADD:
            req_id = db_insert_user(cursor, token, req_type, lang, email,
                                    first_name, last_name, company)
            db_insert_resps(cursor, req_id, resps)
        elif action == ReqAction.UPDATE:
            try:
                req_id = db_update_user(cursor, token, req_type, lang, email,
                                        first_name, last_name, company)
            except:
                req_id = db_insert_user(cursor, token, req_type, lang, email,
                                        first_name, last_name, company)
            db_delete_resps(cursor, req_id)
            db_insert_resps(cursor, req_id, resps)
        elif action == ReqAction.DELETE:
            db_delete_user(cursor, email)
        else:
            return LGCError.INVALID_DATA
    except Exception as e:
        print(e)
        return LGCError.DB_ERROR
    finally:
        db_commit_and_close(cursor, mydb)

    return send_email(first_name, last_name, email, token, lang)

def worker(data):
    print("got: ", data)
    #file_name = data.rstrip()
    #with open(os.path.join("/tmp/1_bis", file_name), "w") as f:
    #    f.write(data)
    #    f.close()
    #    return ack
    #return "NACK"
    j = json.loads(data)
    try:
        req_type = j[0]
        action = j[1]
        lang = j[2]['lang']
        email = j[2]['email']
        first_name = j[2]['first_name']
        last_name = j[2]['last_name']
        company = j[2]['company']
        responsible = []
        relation = []

        for r in j[2]['responsible']:
            responsible.append(r)
        for r in j[2]['relations']:
            relation.append(r)

        return lgc_insert_to_db(req_type, action, lang, email, first_name,
                                last_name, company, responsible, relations)
    except:
        print("parsing error")
        return LGCError.INVALID_DATA

if __name__ == '__main__':
    s = TcpServer(worker, "0.0.0.0")
    s.allow_from(['62.23.92.52', '127.0.0.1', '93.26.146.27'])
    while True:
        data = s.run()
