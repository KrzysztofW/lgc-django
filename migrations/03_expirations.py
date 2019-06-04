#!/usr/bin/python3

import mysql.connector
from datetime import datetime
from migration_common import lgc_5_connect, lgc_4_1_connect
import pdb

print('importing expirations...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
except Exception as e:
    print(e)
    exit()

cursor4 = lgc_4_1.cursor()
cursor5 = lgc_v5.cursor()

cursor4.execute("SELECT * FROM apt")
row = cursor4.fetchone()
while row is not None:
    sql_insert_query = """INSERT INTO `lgc_expiration`
    (`type`, `start_date`, `end_date`, `enabled`, `person_id`)
    values (%s, %s, %s, %s, %s)"""

    insert_tuple = ('WP', row[1], row[2], not row[4], row[0])
    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting apt record into expiration table, id:', row[0])
        print("{}".format(error))
        exit()
    row = cursor4.fetchone()

cursor4.execute("SELECT * FROM cs")
row = cursor4.fetchone()
while row is not None:
    sql_insert_query = """INSERT INTO `lgc_expiration`
    (`type`, `start_date`, `end_date`, `enabled`, `person_id`)
    values (%s, %s, %s, %s, %s)"""

    insert_tuple = ('CST', row[1], row[2], not row[4], row[0])

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback()
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting cs record into expiration table, id:', row[0])
        print("{}".format(error))
    row = cursor4.fetchone()

cursor4.execute("SELECT * FROM cse")
row = cursor4.fetchone()
while row is not None:
    sql_insert_query = """INSERT INTO `lgc_expiration`
    (`type`, `start_date`, `end_date`, `enabled`, `person_id`)
    values (%s, %s, %s, %s, %s)"""

    insert_tuple = ('SCST', row[1], row[2], not row[4], row[0])

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback()
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting cse record into expiration table, id:', row[0])
        print("{}".format(error))
    row = cursor4.fetchone()


"""
mysql> desc enfant;
+----------------------------------+-------------+------+-----+---------+-------+
| Field                            | Type        | Null | Key | Default | Extra |
+----------------------------------+-------------+------+-----+---------+-------+
| id_parent                        | smallint(5) | NO   | PRI | NULL    |       |
| prenom                           | varchar(50) | NO   | PRI | NULL    |       |
| date_naiss                       | date        | YES  |     | NULL    |       |
| date_exp_passeport_enfant        | date        | YES  |     | NULL    |       |
| date_exp_document_voyage         | date        | YES  |     | NULL    |       |
| date_exp_document_voyage_relstop | tinyint(1)  | YES  |     | NULL    |       |
+----------------------------------+-------------+------+-----+---------+-------+

lgc_child
+----------------------+-------------+------+-----+---------+----------------+
| Field                | Type        | Null | Key | Default | Extra          |
+----------------------+-------------+------+-----+---------+----------------+
| id                   | int(11)     | NO   | PRI | NULL    | auto_increment |
| first_name           | varchar(50) | NO   |     | NULL    |                |
| birth_date           | date        | YES  |     | NULL    |                |
| passport_expiry      | date        | YES  |     | NULL    |                |
| passport_nationality | varchar(2)  | YES  |     | NULL    |                |
| expiration_id        | int(11)     | YES  | MUL | NULL    |                |
| person_id            | int(11)     | NO   | MUL | NULL    |                |
+----------------------+-------------+------+-----+---------+----------------+
"""
cursor4.execute("SELECT * FROM enfant")
row = cursor4.fetchone()
while row is not None:
    if row[4]:
        sql_insert_query = """INSERT INTO `lgc_expiration`
        (`type`, `end_date`, `enabled`, `person_id`)
        values (%s, %s, %s, %s)"""

        insert_tuple = ('DCEM', row[4], not row[5], row[0])
        try:
            result  = cursor5.execute(sql_insert_query, insert_tuple)
            lgc_v5.commit()
        except mysql.connector.Error as error :
            #lgc_v5.rollback() #rollback if any exception occured
            #print(sql_insert_query%insert_tuple)
            print('Failed inserting child record into expiration table (DCEM), id:', row[0])
            print("{}".format(error))
            exit()
        expiration_id = cursor5.lastrowid
    else:
        expiration_id = None

    sql_insert_query = """INSERT INTO `lgc_child`
    (`first_name`, `birth_date`, `passport_expiry`, `expiration_id`, `person_id`)
    values (%s, %s, %s, %s, %s)"""

    insert_tuple = (row[1], row[2], row[3], expiration_id, row[0])
    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting record into lgc_child table, id:', row[0])
        print("{}".format(error))

    row = cursor4.fetchone()
