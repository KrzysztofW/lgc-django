#!/usr/bin/python3
# https://pynative.com/python-mysql-tutorial/
import mysql.connector
from datetime import datetime
from migration_common import em, lgc_5_connect
import pdb

print('fixing file description...')
try:
    lgc_v5 = lgc_5_connect()
    lgc_v5_update = lgc_5_connect()

except Exception as e:
    print(e)
    print('exiting...')
    exit()

cursor5 = lgc_v5.cursor()
cursor5.execute("SELECT id,comments FROM lgc_person")
cursor5_update = lgc_v5_update.cursor()

row = cursor5.fetchone()
while row is not None:
    if row[1] == None or row[1].find('&quot;') < 0:
        row = cursor5.fetchone()
        continue

    print('fixing id:', row[0])
    comments = row[1].replace('&quot;', '"')
    sql_update_query = """UPDATE `lgc_person` SET comments = %s WHERE id = %s"""
    sql_update_tuple = (comments, row[0])
    try:
        result = cursor5_update.execute(sql_update_query, sql_update_tuple)
        lgc_v5_update.commit()
    except mysql.connector.Error as error :
        print('Failed fixing file id:', row[0])
        print("{}".format(error))
        print('exiting...')
        exit()

    row = cursor5.fetchone()
