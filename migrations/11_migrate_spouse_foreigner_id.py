#!/usr/bin/python3
# https://pynative.com/python-mysql-tutorial/
import mysql.connector
from datetime import datetime
from migration_common import em, lgc_5_connect, lgc_4_1_connect
import pdb

print('migrating spouse foreigner ID...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()

except Exception as e:
    print(e)
    print('exiting...')
    exit()

cursor4 = lgc_4_1.cursor()
cursor5 = lgc_v5.cursor()
cursor4.execute("SELECT id, no_etr_conj FROM personne where no_etr_conj is not null")

row = cursor4.fetchone()
cnt = 0
while row is not None:
    try:
        no_etr = int(row[1])
    except:
        print("failed to convert no_etr_conj `%s' id:%d"%(row[1], row[0]))
        row = cursor4.fetchone()
        continue

    sql_update_query = "UPDATE `lgc_person` SET spouse_foreigner_id = " + row[1] + " WHERE id = " + str(row[0])
    try:
        result = cursor5.execute(sql_update_query)
        lgc_v5.commit()
        cnt += 1
    except mysql.connector.Error as error :
        print('Failed fixing file id:', row[0])
        print("{}".format(error))
        print('exiting...')
        exit()

    row = cursor4.fetchone()

print('Successfully imported %d entries\n'%cnt)
