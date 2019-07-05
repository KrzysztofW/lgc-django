#!/usr/bin/python3

import mysql.connector
from datetime import datetime
from migration_common import lgc_5_connect, lgc_4_1_connect
import pdb

print('importing users...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
except Exception as e:
    print(e)
    exit()

cursor4 = lgc_4_1.cursor()
cursor5 = lgc_v5.cursor()
""" old:
 0 | nom         | varchar(50)  | NO
 1 | prenom      | varchar(50)  | NO
 2 | login       | varchar(100) | YES
 3 | passwd      | varchar(40)  | NO
 4 | admin       | char(2)      | YES
 5 | email       | varchar(100) | YES
 6 | email2      | varchar(100) | YES
 7 | connexion   | timestamp    | NO
 8 | verrou      | smallint(5)  | YES
 9 | verrou_ts   | timestamp    | NO
10 | ext_admin   | char(2)      | YES
11 | function    | varchar(10)  | YES
12 | facturation | char(2)      | YES
13 | csv_cols    | varchar(25)  | YES
14 | stats       | char(2)      | YES

new:
| id                   | int(11)      | NO   | PRI | NULL    | auto_increment |
| password             | varchar(128) | NO   |     | NULL    |                |
| last_login           | datetime(6)  | YES  |     | NULL    |                |
| is_superuser         | tinyint(1)   | NO   |     | NULL    |                |
| first_name           | varchar(50)  | NO   |     | NULL    |                |
| last_name            | varchar(50)  | NO   |     | NULL    |                |
| is_staff             | tinyint(1)   | NO   |     | NULL    |                |
| is_active            | tinyint(1)   | NO   |     | NULL    |                |
| date_joined          | datetime(6)  | NO   |     | NULL    |                |
| email                | varchar(254) | NO   | UNI | NULL    |                |
| username             | varchar(1)   | YES  |     | NULL    |                |
| role                 | varchar(2)   | NO   |     | NULL    |                |
| billing              | tinyint(1)   | NO   |     | NULL    |                |
| token                | varchar(64)  | NO   |     | NULL    |                |
| token_date           | datetime(6)  | YES  |     | NULL    |                |
| password_last_update | date         | YES  |     | NULL    |                |
| status               | varchar(2)   | NO   |     | NULL    |                |
| language             | varchar(2)   | NO   |     | NULL    |                |
| company              | varchar(50)  | NO   |     | NULL    |                |
| show_invoice_notifs  | tinyint(1)   | NO   |     | NULL    |                |
+----------------------+--------------+------+-----+---------+----------------+
"""

cursor4.execute("SELECT * FROM user")
row = cursor4.fetchone()
now = datetime.now()
formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

while row is not None:
    sql_insert_query = """INSERT INTO `users_user`
    (`password`, `is_superuser`, `first_name`, `last_name`, `is_staff`,
    `is_active`, `date_joined`, `email`, `role`, `billing`,
    `token`, `status`, `language`, `company`, `show_invoice_notifs`)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    if row[11] == 'cons':
        role = 'CO'
    elif row[11] == 'assi':
        role = 'JU'
    else:
        role = ''
    if row[4] == 'on':
        is_staff = 1
    else:
        is_staff = 0
    if row[12] == 'on':
        billing = 1
    else:
        billing = 0
    if row[5] == 'btissam.bougrine@example.com':
        show_invoice_notifs = 1
    else:
        show_invoice_notifs = 0
    insert_tuple = ('', 0, row[1], row[0], is_staff,
                    1, formatted_date, row[5], role, billing,
                    '', 'A', 'FR', '', show_invoice_notifs)

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        print(sql_insert_query%insert_tuple)
        print('Failed inserting record into users_user table, nom:', row[1])
        print("{}".format(error))
        exit()
    row = cursor4.fetchone()

