#!/usr/bin/python3

import mysql.connector
from datetime import datetime
from migration_common import client_country_mapping, em, lgc_5_connect, lgc_4_1_connect
import pdb

print('fixing invoice billing country...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
    lgc_4_1_fp = lgc_4_1_connect()
    lgc_4_1_p = lgc_4_1_connect()
    lgc_4_1_c = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
except Exception as e:
    print(e)
    print('exiting...')
    exit()

cursor4 = lgc_4_1.cursor()
cursor_fp = lgc_4_1_fp.cursor()
cursor_p = lgc_4_1_p.cursor()
cursor_c = lgc_4_1_c.cursor()
cursor5 = lgc_v5.cursor()

"""
mysql> desc facture;
+-----------------+-------------------------------+------+-----+---------+----------------+
| Field           | Type                          | Null | Key | Default | Extra          |
+-----------------+-------------------------------+------+-----+---------+----------------+
 0 | id              | smallint(5) unsigned zerofill | NO   | PRI | NULL    | auto |
 1 | date            | date                          | NO   |     | NULL    |            |
 2 | date_modif      | date                          | YES  |     | NULL    |            |
 3 | date_validation | date                          | YES  |     | NULL    |            |
 4 | id_client       | smallint(5) unsigned zerofill | NO   | MUL | NULL    |            |
 5 | nom_client      | varchar(50)                   | YES  |     | NULL    |            |
 6 | prenom_client   | varchar(50)                   | YES  |     | NULL    |            |
 7 | email_client    | varchar(100)                  | YES  |     | NULL    |            |
 8 | siret_client    | decimal(20,0)                 | YES  |     | NULL    |            |
 9 | vat_client      | varchar(30)                   | YES  |     | NULL    |            |
10 | societe_client  | varchar(50)                   | YES  |     | NULL    |            |
11 | adresse_client  | varchar(100)                  | YES  |     | NULL    |            |
12 | CP_client       | varchar(10)                   | YES  |     | NULL    |            |
13 | ville_client    | varchar(50)                   | YES  |     | NULL    |            |
14 | pays_client     | varchar(50)                   | YES  |     | NULL    |            |
15 | mode            | varchar(30)                   | YES  |     | NULL    |            |
16 | PO              | varchar(20)                   | YES  |     | NULL    |            |
17 | date_po         | date                          | YES  |     | NULL    |            |
18 | nom_po          | varchar(20)                   | YES  |     | NULL    |            |
19 | prenom_po       | varchar(20)                   | YES  |     | NULL    |            |
20 | email_po        | varchar(100)                  | YES  |     | NULL    |            |
21 | montant_po      | decimal(9,2)                  | YES  |     | NULL    |            |
22 | devise          | varchar(5)                    | YES  |     | NULL    |            |
23 | langue          | varchar(3)                    | YES  |     | NULL    |            |
24 | info_societe    | tinyint(1)                    | YES  |     | NULL    |            |
25 | proc            | varchar(50)                   | YES  |     | NULL    |            |
26 | deja_regle      | decimal(8,2)                  | YES  |     | NULL    |            |
27 | deja_regle_desc | varchar(100)                  | YES  |     | NULL    |            |
28 | frais_divers    | tinyint(1)                    | YES  |     | NULL    |            |
29 | valide          | tinyint(1)                    | YES  |     | NULL    |            |
30 | description     | blob                          | YES  |     | NULL    |            |
31 | a_facturer      | tinyint(1)                    | YES  |     | NULL    |            |
+-----------------+-------------------------------+------+-----+---------+----------------+
mysql> desc lgc_invoice;
+-------------------+------------------+------+-----+---------+----------------+
| Field             | Type             | Null | Key | Default | Extra          |
+-------------------+------------------+------+-----+---------+----------------+
| first_name        | varchar(50)      | NO   |     | NULL    |                |
| last_name         | varchar(50)      | NO   |     | NULL    |                |
| company           | varchar(50)      | NO   |     | NULL    |                |
| phone_number      | varchar(50)      | NO   |     | NULL    |                |
| cell_phone_number | varchar(50)      | NO   |     | NULL    |                |
| address           | longtext         | NO   |     | NULL    |                |
| post_code         | varchar(10)      | NO   |     | NULL    |                |
| city              | varchar(50)      | NO   |     | NULL    |                |
| country           | varchar(2)       | NO   |     | NULL    |                |
| id                | int(11)          | NO   | PRI | NULL    | auto_increment |
| version           | int(10) unsigned | NO   |     | NULL    |                |
| number            | int(10) unsigned | NO   | MUL | NULL    |                |
| type              | varchar(1)       | NO   |     | NULL    |                |
| invoice_date      | date             | NO   |     | NULL    |                |
| modification_date | date             | YES  |     | NULL    |                |
| payment_option    | varchar(2)       | NO   |     | NULL    |                |
| currency          | varchar(3)       | NO   |     | NULL    |                |
| email             | varchar(50)      | YES  |     | NULL    |                |
| siret             | varchar(14)      | YES  |     | NULL    |                |
| vat               | varchar(50)      | YES  |     | NULL    |                |
| po                | varchar(50)      | NO   |     | NULL    |                |
| po_date           | date             | YES  |     | NULL    |                |
| po_first_name     | varchar(50)      | NO   |     | NULL    |                |
| po_last_name      | varchar(50)      | NO   |     | NULL    |                |
| po_email          | varchar(50)      | YES  |     | NULL    |                |
| po_rate           | double           | YES  |     | NULL    |                |
| company_option    | varchar(1)       | NO   |     | NULL    |                |
| language          | varchar(2)       | NO   |     | NULL    |                |
| invoice_description| longtext        | NO   |     | NULL    |                |
| various_expenses  | tinyint(1)       | NO   |     | NULL    |                |
| state             | varchar(1)       | NO   |     | NULL    |                |
| already_paid      | double           | NO   |     | NULL    |                |
| with_regard_to    | varchar(50)      | NO   |     | NULL    |                |
| total             | double           | NO   |     | NULL    |                |
| client_id         | int(11)          | YES  | MUL | NULL    |                |
| modified_by_id    | int(11)          | YES  | MUL | NULL    |                |
| person_id         | int(11)          | YES  | MUL | NULL    |                |
| process_id        | int(11)          | YES  | UNI | NULL    |                |
| already_paid_desc | varchar(50)      | NO   |     | NULL    |                |
| last_modified_date| date             | NO   |     | NULL    |                |
+-------------------+------------------+------+-----+---------+----------------+
"""

cursor4.execute("SELECT * FROM facture")
row = cursor4.fetchone()

while row is not None:
    if row[14] != '':
        row = cursor4.fetchone()
        continue

    print('fixing invoice id:', row[0])
    sql_update_query = "UPDATE `lgc_invoice` SET country = '' WHERE number = " + str(row[0])
    try:
        result = cursor5.execute(sql_update_query)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        print('Failed fixing invoice id:', row[0])
        print("{}".format(error))
        print('exiting...')
        exit()
    row = cursor4.fetchone()
