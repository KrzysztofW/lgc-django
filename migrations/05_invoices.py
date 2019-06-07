#!/usr/bin/python3

import mysql.connector
from datetime import datetime
from migration_common import client_country_mapping, em, lgc_5_connect, lgc_4_1_connect
import pdb

print('importing invoices...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
    lgc_4_1_fp = lgc_4_1_connect()
    lgc_4_1_p = lgc_4_1_connect()
    lgc_4_1_c = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
except Exception as e:
    print(e)
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
+-------------------+------------------+------+-----+---------+----------------+
"""

cursor4.execute("SELECT * FROM facture")
row = cursor4.fetchone()

while row is not None:
    cursor_fp.execute("SELECT * FROM facture_personne where id_facture=%d"%(row[0]))
    row_fp = cursor_fp.fetchone()
    if row_fp == None or len(row_fp) == 0:
        print('id fact:', row[0], 'cannot find the corresponding facture_personne')
        exit()
    id_personne = row_fp[1]

    cursor_p.execute("SELECT * FROM personne where id=%d"%(id_personne))
    row_p = cursor_p.fetchone()
    if row_p == None or len(row_p) == 0:
        print('id fact:', row[0], 'cannot find the corresponding person')
        exit()

    payment_option = row[15]
    if payment_option == 'vir':
        payment_option = 'BT'
    elif payment_option == 'es':
        payment_option = 'CA'
    elif payment_option == 'cb':
        payment_option = 'CB'
    elif payment_option == 'ch':
        payment_option = 'CH'
    else:
        payment_option = ''

    state = row[31]
    if state == 0:
        state = 'P'
    elif state == 1:
        state = 'T'
    elif state == 2:
        state = 'D'
    elif state == 3:
        state = 'C'
    if row[29]:
        state = 'V'
    country = row[14].lower()
    for c in client_country_mapping:
        if country in c or c in country:
            country = client_country_mapping[c]
            break
    else:
        country = ''

    # fix client id
    client_id = row[4]
    if row[4] == 59:
        client_id = 46
    elif row[4] == 156:
        client_id = 105
    elif row[4] == 446:
        client_id = 426
    elif row[4] == 491:
        client_id = 435
    elif row[4] == 590:
        client_id = 585
    elif row[4] == 641:
        client_id = 494
    elif row[4] == 789:
        client_id = 741
    elif row[4] == 711 or row[4] == 712 or 746:
        client_id = None
    elif row[4] == 281:
        client_id = 271

    sql_insert_query = """INSERT INTO `lgc_invoice`
    (`first_name`, `last_name`, `company`, `email`, `phone_number`,
    `cell_phone_number`, `siret`, `vat`, `address`, `post_code`,
    `city`, `country`,
    `version`, `number`, `type`, `invoice_date`, `modification_date`,
    `payment_option`, `currency`, `po`, `po_date`, `po_first_name`,
    `po_last_name`, `po_email`, `po_rate`, `company_option`, `language`,
    `invoice_description`, `various_expenses`, `state`, `already_paid`, `with_regard_to`,
    `total`, `client_id`, `person_id`, `already_paid_desc`
    )
    values (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s
    )"""

    if int(row[8]) == 0:
        siret = ''
    else:
        siret = str(row[8])
    insert_tuple = (row[6], row[5], row[10], row[7], '',
                    '', siret, row[9], row[11], row[12],
                    row[13], country,
                    0, row[0], 'I', row[1], row[2],
                    payment_option, row[22], em(row[16]), row[17], row[19],
                    row[18], row[20], row[21], 'L' if row[24] == 0 else 'F', row[23].upper(),
                    row[30].decode('windows-1252').encode('utf8'), row[28], state, row[26], row_p[2] + ' ' + row_p[1],
                    0, #total,
                    client_id, id_personne, em(row[27])
    )

    try:
        result = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting record into invoice table, id:', row[0])
        print("{}".format(error))
        exit()
    row = cursor4.fetchone()
