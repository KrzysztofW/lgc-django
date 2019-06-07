#!/usr/bin/python3

import mysql.connector
from datetime import datetime
from migration_common import lgc_5_connect, lgc_4_1_connect
import pdb, os, sys, django

sys.path.append("..")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lgc_base.settings")
django.setup()
from lgc.models import Invoice

print('importing items...')

try:
    lgc_4_1 = lgc_4_1_connect()
    lgc_4_1_tarif = lgc_4_1_connect()
    lgc_v5 = lgc_5_connect()
    lgc_v5_invoice = lgc_5_connect()
except Exception as e:
    print(e)
    exit()

cursor4 = lgc_4_1.cursor()
cursor4_tarif = lgc_4_1_tarif.cursor()
cursor5 = lgc_v5.cursor()
cursor5_invoice = lgc_v5_invoice.cursor()

cursor4.execute("SELECT * FROM diligence")
row = cursor4.fetchone()
while row is not None:
    cursor4_tarif.execute('select * from tarif_dil where id_dil=%d'%(row[0]))
    row_tarif = cursor4_tarif.fetchone()
    if row_tarif == None or len(row_tarif) == 0:
        print('id diligence:', row[0], 'cannot find the corresponding tarif_dill')
        exit()

    sql_insert_query = """INSERT INTO `lgc_item`
    (`id`, `description`, `title`, `rate_eur`, `rate_usd`, `rate_cad`, `rate_gbp`)
    values (%s, %s, %s, %s, %s, %s, %s)"""

    insert_tuple = (row[0], row[3].decode('windows-1252').encode('utf8'), row[2], row_tarif[2], row_tarif[3], row_tarif[4], row_tarif[5])

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting record into lgc_item table, id:', row[0])
        print("{}".format(error))
        exit()
    row = cursor4.fetchone()

print('importing disbursements...')
cursor4.execute("SELECT * FROM debours")
row = cursor4.fetchone()
while row is not None:
    sql_insert_query = """INSERT INTO `lgc_disbursement`
    (`id`, `description`, `rate`, `title`, `currency`)
    values (%s, %s, %s, %s, %s)"""

    insert_tuple = (row[0], row[5].decode('iso-8859-1').encode('utf8'), row[3], row[2],
                    row[4])

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting record into lgc_disbursement table, id:', row[0])
        print("{}".format(error))
        exit()
    row = cursor4.fetchone()

print('importing invoice items...')
cursor4.execute("SELECT * FROM operation_facture where type=0")
row = cursor4.fetchone()
while row is not None:
    cursor5_invoice.execute('select id from lgc_invoice where number=%d'%(row[2]))
    row_invoice = cursor5_invoice.fetchone()
    if row_invoice == None or len(row_invoice) == 0:
        print('id operation_facture:', row[0], 'invoice number:', row[2],
              'cannot find the corresponding invoice')
        exit()

    sql_insert_query = """INSERT INTO `lgc_invoiceitem`
    (`item_id`, `description`, `rate`, `quantity`, `vat`, `invoice_id`)
    values (%s, %s, %s, %s, %s, %s)"""

    insert_tuple = (row[3], row[4].decode('windows-1252').encode('utf8'), row[6],
                    row[5], row[7], row_invoice[0])

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        print(sql_insert_query%insert_tuple)
        print('Failed inserting record into lgc_invoiceitem table, id_op:', row[3])
        print("{}".format(error))
        exit()
    row = cursor4.fetchone()

print('importing invoice disbursements...')
cursor4.execute("SELECT * FROM operation_facture where type=1")
row = cursor4.fetchone()
while row is not None:
    cursor5_invoice.execute('select id from lgc_invoice where number=%d'%(row[2]))
    row_invoice = cursor5_invoice.fetchone()
    if row_invoice == None or len(row_invoice) == 0:
        print('id operation_facture:', row[0], 'invoice number:', row[2],
              'cannot find the corresponding invoice')
        exit()

    if row[8]:
        margin = True
    else:
        margin = False
    sql_insert_query = """INSERT INTO `lgc_invoicedisbursement`
    (`disbursement_id`, `description`, `rate`, `quantity`, `vat`, `margin`,
    `invoice_id`)
    values (%s, %s, %s, %s, %s, %s, %s)"""

    insert_tuple = (row[3], row[4].decode('windows-1252').encode('utf8'), row[6],
                    row[5], row[7], margin, row_invoice[0])

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        print(sql_insert_query%insert_tuple)
        print('Failed inserting record into lgc_invoicedisbursement table, id_op:', row[3])
        print("{}".format(error))
        exit()
    row = cursor4.fetchone()

print('fill total column of all invoices...')
for invoice in Invoice.objects.all():
    if invoice.total == 0:
        invoice.total = round(invoice.get_total + invoice.get_vat, 2)
        invoice.save()
        #print('set invoice id:%d total:%f'%(invoice.id, invoice.total))
