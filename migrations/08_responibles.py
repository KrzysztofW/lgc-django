#!/usr/bin/python3

import mysql.connector
from datetime import datetime
from migration_common import lgc_5_connect, lgc_4_1_connect
import pdb

print('importing responsibles...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
    lgc_v5_user = lgc_5_connect()
except Exception as e:
    print(e)
    exit()

cursor4 = lgc_4_1.cursor()
cursor5 = lgc_v5.cursor()
cursor5_user = lgc_v5_user.cursor()
cursor4.execute("SELECT * FROM responsable")
row = cursor4.fetchone()

while row is not None:
    try:
        first_name, last_name = row[1].split('.')
    except:
        first_name = last_name = row[1]

    cursor5_user.execute("SELECT id FROM users_user where last_name like '%%%s%%'"%(last_name))
    row_user = cursor5_user.fetchone()
    if row_user == None or len(row_user) != 1:
            cursor5_user.execute("SELECT id FROM users_user where first_name like '%%%s%%'"%(first_name))
            row_user = cursor5_user.fetchone()
            if row_user == None or len(row_user) != 1:
                print('user:', row[1], 'cannot find the corresponding user')
                exit()

    user_id = row_user[0]

    sql_insert_query = """INSERT INTO `lgc_person_responsible`
    (`person_id`, `user_id`) values (%s, %s)"""

    insert_tuple = (row[0], user_id)
    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        if error.errno == 1062:
            print('duplicated responsible:', row[1], 'for the same file:', row[0])
        else:
            print('Failed inserting record into lgc_person_responsible table, nom:', row[1])
            print("{}".format(error))
            exit()
    row = cursor4.fetchone()

