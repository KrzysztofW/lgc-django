#!/usr/bin/python3
# https://pynative.com/python-mysql-tutorial/
import mysql.connector
import pdb
from migration_common import client_country_mapping as country_mapping

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
cursor4.execute("SELECT * FROM client")
row = cursor4.fetchone()

while row is not None:
    if row[14]:
        country = row[14].lower()
        for c in country_mapping:
            if country in c or c in country:
                country = country_mapping[c]
                break
    else:
        country = ''
    if row[19]:
        billing_country = row[19].lower()
        try:
            billing_country = country_mapping[billing_country]
        except:
            print('')
    else:
        billing_country = ''
    siret = str(row[8])
    vat = row[9]

    if row[12] == None:
        post_code = ''
    else:
        post_code = row[12]

    if row[17] == None:
        billing_post_code = ''
    else:
        billing_post_code = row[17]

    if siret == '0':
        siret = None
    if vat == '':
        vat = None

    sql_insert_query = """INSERT INTO `lgc_client`
    (`id`, `first_name`, `last_name`, `company`, `email`, `phone_number`,
    `cell_phone_number`, `siret`, `vat`, `address`, `post_code`, `city`,
    `country`, `billing_company`, `billing_address`, `billing_post_code`,
    `billing_city`, `billing_country`)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

    insert_tuple = (row[0], row[3], row[2], row[10], row[7], row[4], row[5], siret,
                    vat,
                    row[11],
                    post_code,
                    row[13],
                    country,
                    row[15], row[16], billing_post_code, row[18], billing_country)
    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        if error.errno == 1062:
            print('duplicated client id:', row[0], 'first_name:', row[3], 'last_name:',
                  row[2], 'company:', row[10])
        else:
            print("Failed inserting record into client table {}".format(error))
            exit()
    row = cursor4.fetchone()
