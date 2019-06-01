#!/usr/bin/python3

import mysql.connector
from datetime import datetime
import pdb

try:
    lgc_4_1 = mysql.connector.connect(
        host="localhost",
        user="lgc",
        passwd="zqooe872Fjdhe",
        database='lgc_4_1'
    )

    lgc_v5 = mysql.connector.connect(
        host="localhost",
        user="lgc",
        passwd="zqooe872Fjdhe",
        database='lgc_v5'
    )
except Exception as e:
    print(e)
    exit()

cursor4 = lgc_4_1.cursor()
cursor5 = lgc_v5.cursor()
cursor4.execute("SELECT * FROM boite_archive")
row = cursor4.fetchone()
while row is not None:
    sql_insert_query = """INSERT INTO `lgc_archivebox`
    (`number`, `person_id`
    )
    values (%s, %s)"""

    insert_tuple = (row[1], row[0])
    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting record into expiration table, id:', row[0])
        print("{}".format(error))
    row = cursor4.fetchone()
