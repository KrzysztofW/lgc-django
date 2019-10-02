#!/usr/bin/python3
# https://pynative.com/python-mysql-tutorial/
import mysql.connector
from datetime import datetime
from migration_common import em, lgc_5_connect, lgc_4_1_connect
import pdb

print('fixing file states...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()

except Exception as e:
    print(e)
    print('exiting...')
    exit()

cursor4 = lgc_4_1.cursor()
cursor5 = lgc_v5.cursor()
cursor4.execute("SELECT * FROM personne")

row = cursor4.fetchone()
while row is not None:
    state = row[42]
    """what's needed to be fixed:"""
    #if state == 'actif':
    #    state = 'A'
    #elif state == 'inactif':
    #    state = 'P'
    #elif state == 'clos':
    #    state = 'C'
    #else:
    #    state = ''

    if state != 'inactif':
        row = cursor4.fetchone()
        continue

    print('fixing file id:', row[0])
    sql_update_query = "UPDATE `lgc_person` SET state = 'I' WHERE id = " + str(row[0])
    try:
        result = cursor5.execute(sql_update_query)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        print('Failed fixing file id:', row[0])
        print("{}".format(error))
        print('exiting...')
        exit()

    row = cursor4.fetchone()
