#!/usr/bin/python3

import mysql.connector
from migration_common import lgc_5_connect

print('removing existing database...')

try:
    lgc_v5 = lgc_5_connect()
except Exception as e:
    print(e)
    exit()

cursor5 = lgc_v5.cursor()
cursor5.execute("delete FROM lgc_person_responsible")
cursor5.execute("delete FROM lgc_disbursementdocument")
cursor5.execute("delete FROM lgc_invoicedisbursement")
cursor5.execute("delete FROM lgc_invoiceitem")
cursor5.execute("delete FROM lgc_disbursement")
cursor5.execute("delete FROM lgc_item")
cursor5.execute("delete FROM lgc_invoice")
cursor5.execute("delete FROM lgc_client")
cursor5.execute("delete FROM lgc_child")
cursor5.execute("delete FROM lgc_expiration")
cursor5.execute("delete FROM lgc_archivebox")
cursor5.execute("delete FROM lgc_document")
cursor5.execute("delete FROM lgc_personprocessstage")
cursor5.execute("delete FROM lgc_personprocess")
cursor5.execute("delete FROM lgc_person")
cursor5.execute("delete FROM employee_expiration")
cursor5.execute("delete FROM employee_employee")
cursor5.execute("delete FROM employee_child")
cursor5.execute("delete FROM users_user_responsible")
cursor5.execute("delete FROM users_user_hr_employees")
cursor5.execute("delete FROM users_user where is_superuser=0")
lgc_v5.commit()

print("don't forget to: rm -rf  /home/partage/LGC-documents/*")
