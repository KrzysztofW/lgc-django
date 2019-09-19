#!/usr/bin/python3
# https://pynative.com/python-mysql-tutorial/
import mysql.connector
from datetime import datetime
from migration_common import em, lgc_5_connect, lgc_4_1_connect
import pdb

print('importing files...')
"""
   | Field            | Type         | Null | Key | Default | Extra          |
   +------------------+--------------+------+-----+---------+----------------+
 0 | id               | smallint(5)  | NO   | PRI | NULL    | auto_increment |
 1 | nom              | varchar(50)  | NO   | MUL | NULL    |                |
 2 | prenom           | varchar(50)  | NO   |     | NULL    |                |
 3 | no_etr           | varchar(50)  | YES  |     | NULL    |                |
 4 | no_gvs           | varchar(50)  | YES  |     | NULL    |                |
 5 | date_naiss       | date         | YES  |     | NULL    |                |
 6 | nationalite      | varchar(50)  | YES  |     | NULL    |                |
 7 | ste_orig         | varchar(50)  | YES  |     | NULL    |                |
 8 | ste_orig_adr     | varchar(100) | YES  |     | NULL    |                |
 9 | ste_acc          | varchar(50)  | YES  |     | NULL    |                |
10 | ste_acc_adr      | varchar(100) | YES  |     | NULL    |                |
11 | proc             | varchar(50)  | YES  |     | NULL    |                |
12 | proc_rnv         | tinyint(1)   | YES  |     | NULL    |                |
13 | date_pe          | date         | YES  |     | NULL    |                |
14 | nom_conj         | varchar(50)  | YES  |     | NULL    |                |
15 | prenom_conj      | varchar(50)  | YES  |     | NULL    |                |
16 | no_etr_conj      | varchar(50)  | YES  |     | NULL    |                |
17 | dnc              | date         | YES  |     | NULL    |                |
18 | date_pce         | date         | YES  |     | NULL    |                |
19 | tel_bureau_etr   | varchar(20)  | YES  |     | NULL    |                |
20 | tel_maison_etr   | varchar(20)  | YES  |     | NULL    |                |
21 | telecopie_etr    | varchar(20)  | YES  |     | NULL    |                |
22 | tel_portable_etr | varchar(20)  | YES  |     | NULL    |                |
23 | email_etr        | varchar(100) | YES  |     | NULL    |                |
24 | adr_perso_etr    | varchar(100) | YES  |     | NULL    |                |
25 | tel_bureau_fr    | varchar(20)  | YES  |     | NULL    |                |
26 | tel_maison_fr    | varchar(20)  | YES  |     | NULL    |                |
27 | telecopie_fr     | varchar(20)  | YES  |     | NULL    |                |
28 | tel_portable_fr  | varchar(20)  | YES  |     | NULL    |                |
29 | email_fr         | varchar(100) | YES  |     | NULL    |                |
30 | adr_perso_fr     | varchar(100) | YES  |     | NULL    |                |
31 | date_ef          | date         | YES  |     | NULL    |                |
32 | date_vd          | date         | YES  |     | NULL    |                |
33 | date_vf          | date         | YES  |     | NULL    |                |
34 | date_vlstsd      | date         | YES  |     | NULL    |                |
35 | date_vlstsf      | date         | YES  |     | NULL    |                |
36 | vlsts_relstop    | tinyint(1)   | YES  |     | NULL    |                |
37 | date_decannu     | date         | YES  |     | NULL    |                |
38 | decannu_relstop  | tinyint(1)   | YES  |     | NULL    |                |
39 | secu             | varchar(10)  | YES  |     | NULL    |                |
40 | date_ss          | date         | YES  |     | NULL    |                |
41 | formulaire       | varchar(10)  | YES  |     | NULL    |                |
42 | etat             | varchar(10)  | YES  |     | NULL    |                |
43 | date_d           | date         | YES  |     | NULL    |                |
44 | date_reouverture | date         | YES  |     | NULL    |                |
45 | description      | text         | YES  |     | NULL    |                |
46 | honoraires       | decimal(6,2) | YES  |     | NULL    |                |
47 | facture          | tinyint(1)   | YES  |     | NULL    |                |
"""
citizenship_mapping = {
    'a':'',
    'afriquesud':'ZA',
    'albanaise':'AL',
    'algérie':'DZ',
    'algérien':'DZ',
    'algérienne':'DZ',
    'allemand':'DE',
    'allemande':'DE',
    'am':'',
    'americaaine':'US',
    'americaine-brésilienne':'US',
    'american':'US',
    'amréicaine':'US',
    'améicaine':'US',
    'amér':'US',
    'amércaiene':'US',
    'amércaine':'US',
    'américain':'US',
    'américain-colombien':'',
    'américaine':'US',
    'américainothailandaise':'US',
    'américainr':'US',
    'américiane':'US',
    'anglais':'UK',
    'anglaise':'UK',
    'angolaise':'AO',
    'argentin':'AR',
    'argentine':'AR',
    'arménie':'AM',
    'arménienne':'AM',
    'asutralienne':'AU',
    'australian':'AU',
    'australie':'AU',
    'australien':'AU',
    'australienne':'AU',
    'autralienne':'AU',
    'autrichien':'AT',
    'autrichienne':'AT',
    'autstralienne':'AU',
    'azerbaidjanaise':'AZ',
    'azerbaijan':'AZ',
    'bahamas':'BS',
    'bahrein':'BH',
    'bangladaise':'BD',
    'barbadienne':'BB',
    'barhain':'BH',
    'belarus':'BY',
    'belge':'BE',
    'belgique':'BE',
    'beninoise':'BJ',
    'bielorruse':'BY',
    'bielorusse':'BY',
    'birmane':'MM',
    'bolivienne':'BO',
    'brasilienne':'BR',
    'braésilienne':'BR',
    'bresilienne': 'BR',
    'britanique':'UK',
    'britannique':'UK',
    'brésil':'BR',
    'brésilenne':'BR',
    'brésilien':'BR',
    'brésilienne':'BR',
    'brésilinne':'BR',
    'brésillienne':'BR',
    'bulgare':'BG',
    'burkinabe':'BF',
    'burkinabese':'BF',
    'burnikabaise':'BF',
    'burundaise':'BI',
    'bénin':'BJ',
    'c':'',
    'cameroun':'CM',
    'camerounais':'CM',
    'camerounaise':'CM',
    'cameroune':'CM',
    'canada':'CA',
    'canadien':'CA',
    'canadienne':'CA',
    'canadienne-italienne':'IT',
    'canadolibanaise':'CA',
    'candienne':'CA',
    'centreafricaine':'CF',
    'chilien':'CL',
    'chilienne':'CL',
    'china':'CN',
    'chine':'CN',
    'chinois':'CN',
    'chinoise':'CN',
    'chinsoire':'CN',
    'chypriote':'CY',
    'colombie':'CO',
    'colombien':'CO',
    'colombienne':'CO',
    'comorienne':'KM',
    'congolais':'CG',
    'congolaise':'CG',
    'coreedusud':'KR',
    'coreennedusud':'KR',
    'coréen':'KR',
    'coréenne':'KR',
    'costarica':'CR',
    'costaricain':'CR',
    'costaricaine':'CR',
    'croate':'HR',
    'croatie':'HR',
    'cubaine':'CU',
    'danois':'DK',
    'danoise':'DK',
    'djibouti':'DJ',
    'djiboutienne':'DJ',
    'dominicaine':'DM',
    'eau':'',
    'egypte':'EG',
    'egyptienne':'EG',
    'equateur':'EC',
    'equatorienne':'EC',
    'espagnol':'ES',
    'espagnole':'ES',
    'espoagnole':'ES',
    'etat-unis':'US',
    'etats-unis':'US',
    'ethiopienne':'ET',
    'finlandaise':'FR',
    'fr':'FR',
    'france':'FR',
    'franco-marocaine':'FR',
    'franco-tunisienne':'FR',
    'français':'FR',
    'française':'FR',
    'gabonaise':'GA',
    'georgien':'GE',
    'georgienne':'GE',
    'géorgienne':'GE',
    'ghanéenne':'GH',
    'grecque':'GR',
    'greque':'GR',
    'guatemala':'GT',
    'guatémaltèque':'GT',
    'guinéenne':'GN',
    'haitienne':'HT',
    'hollandais':'NL',
    'hollandaise':'NL',
    'hondurienne':'HN',
    'hongkong':'HK',
    'hongkongais':'HK',
    'hongrois':'HU',
    'hongroise':'HU',
    'in':'IN',
    'inde':'IN',
    'indi':'IN',
    'india':'IN',
    'indien':'IN',
    'indiene':'IN',
    'indienne':'IN',
    'indiennne':'IN',
    'indiienne':'IN',
    'indonesie':'ID',
    'indonesienne':'ID',
    'indonésien':'ID',
    'indonésiene':'ID',
    'irakien':'IQ',
    'irakienne':'IQ',
    'iranien':'IQ',
    'iranienne':'IR',
    'iranienne-irakienne':'IR',
    'iraquien':'IQ',
    'iraquienne':'IQ',
    'irlandais':'IE',
    'irlandaise':'IE',
    'irlando-américaine':'IE',
    'israelien':'IL',
    'israelienne':'IL',
    'istraelienne':'IL',
    'italie':'IT',
    'italien':'IT',
    'italienne':'IT',
    'ivoirienne':'CI',
    'ivorien':'CI',
    'ivorienne':'CI',
    'jamaicaine':'JM',
    'jamaique':'JM',
    'japon':'JP',
    'japonais':'JP',
    'japonaise':'JP',
    'japonnaise':'JP',
    'jordanienne':'JO',
    'kazahkstan':'KZ',
    'kazak':'KZ',
    'kazakh':'KZ',
    'kazakhe':'KZ',
    'kazakhs':'KZ',
    'kenyane':'KE',
    'kenyanne':'KE',
    'kirgizhistainne':'KG',
    'koréenne':'KR',
    'koreenne':'KR',
    'kowetienne':'KW',
    'kuwait':'KW',
    'laotienne':'LA',
    'lettone':'LT',
    'liban':'LB',
    'libanaire':'LB',
    'libanais':'LB',
    'libanaise':'LB',
    'libannaise':'LB',
    'lituanie':'LT',
    'lituanienne':'LT',
    'llibanaise':'LB',
    'luxembourg':'LU',
    'lybienne':'LB',
    'macedoine':'MK',
    'macédonienne':'MK',
    'madagascar':'MG',
    'malais':'MY',
    'malaise':'MY',
    'malaisien':'MY',
    'malaisienne':'MY',
    'malaysia':'MY',
    'malaysian':'MY',
    'malaysie':'MY',
    'malaysien':'MY',
    'malaysienne':'MY',
    'malgache':'MG',
    'malien':'ML',
    'malienne':'ML',
    'maltais':'MT',
    'maltaise':'MT',
    'maorcaine':'MA',
    'maroc':'MA',
    'marocain':'MA',
    'marocaine':'MO',
    'marocetcanadienne':'CA',
    'maurcienne':'MU',
    'maurice':'MU',
    'mauricien':'MU',
    'mauricienne':'MU',
    'mauritanienne':'MU',
    'mauritien':'MU',
    'mauritienne':'MU',
    'mexicain':'MX',
    'mexicaine':'MX',
    'mexique':'MX',
    'moldave':'MD',
    'mon':'',
    'mongole':'MN',
    'montegrene':'ME',
    'neerlandaise':'NL',
    'neo-zélandaise':'NZ',
    'neozelandaise':'NZ',
    'newzealand':'NZ',
    'nicaraguayen':'NI',
    'nigeria':'NG',
    'nigérian':'NG',
    'nigériane':'NG',
    'nigérianne':'NG',
    'nigérienne':'NG',
    'nigerienne':'NG',
    'norvégienne':'NO',
    'norvegienne':'NO',
    'nz':'NZ',
    'néerlandais':'NL',
    'néo-zélandais':'NZ',
    'néozélandais':'NZ',
    'népalais':'NP',
    'népalaise':'NP',
    'ouganda':'UG',
    'ougandaise':'UG',
    'ouzbek':'UZ',
    'ouzbèque':'UZ',
    'pakistan':'PK',
    'pakistanais':'PK',
    'pakistanaise':'PK',
    'palestinien':'PS',
    'palestinienne':'PS',
    'paraguay':'PY',
    'paraguayenne':'PY',
    'peruvienne':'PE',
    'péruvienne':'PE',
    'philiinne':'PH',
    'phililppine':'PH',
    'philipin':'PH',
    'philipine':'PH',
    'philipines':'PH',
    'philipinne':'PH',
    'philippin':'PH',
    'philippine':'PH',
    'philippines':'PH',
    'phillipinne':'PH',
    'phillippines':'PH',
    'phlippine':'PH',
    'polonais':'PL',
    'polonaise':'PL',
    'polonnais':'PL',
    'portugais':'PT',
    'portugais-americain':'PT',
    'portugaise':'PT',
    'portugaise-brésilienne':'PT',
    'portuguaise':'PT',
    'roumain':'RO',
    'roumaine':'RO',
    'roumanie':'RO',
    'rsa':'ZA',
    'russe':'RU',
    'russie':'RU',
    'rwandaise':'RW',
    'salvador':'SV',
    'salvadorien':'SV',
    'salvadorienne':'SV',
    'saoudien':'SA',
    'saoudienne':'SA',
    'senegalais':'SN',
    'serbe':'RS',
    'singapoour':'SG',
    'singapore':'SG',
    'singaporienne':'SG',
    'singapour':'SG',
    'singapoure':'SG',
    'singapourien':'SG',
    'singapourienne':'SG',
    'sinpagour':'SG',
    'slovaque':'SK',
    'slovene':'SI',
    'soudanais':'SD',
    'soudanaise':'SD',
    'soudienne':'SA',
    'spanish':'ES',
    'sri-lankaise':'LK',
    'sud-africain':'ZA',
    'sud-africaine':'ZA',
    'sud-corréenne':'KR',
    'sud-coréen':'KR',
    'sud-coréenne':'KR',
    'sudafricain':'ZA',
    'sudafricaine':'ZA',
    'sudafricainegrecque':'GR',
    'sudcoréenne':'KR',
    'suedoise':'SE',
    'suisse':'CH',
    'surinamienne':'SR',
    'suédois':'SE',
    'swaziland':'SZ',
    'swazilandaise':'SZ',
    'syrien':'SY',
    'syrienne':'SY',
    'sénégalaise':'SN',
    'taiwan':'TW',
    'taiwanaise':'TW',
    'tawainese':'TW',
    'tchadienne':'TD',
    'tchèque':'CZ',
    'tchèqye':'CZ',
    'thailandais':'TH',
    'thailandaise':'TH',
    'togolaise':'TG',
    'trinidadien':'TT',
    'trinidadienne':'TT',
    'tunisie':'TN',
    'tunisien':'TN',
    'tunisienne':'TN',
    'tunsienne':'TN',
    'turc':'TR',
    'turkménistan':'TM',
    'turque':'TR',
    'turquie':'TR',
    'uae':'AE',
    'uk':'UK',
    'ukraine':'UA',
    'ukrainian':'UA',
    'ukrainien':'UA',
    'ukrainienne':'UA',
    'ukranienne':'UA',
    'uruguay':'UY',
    'uruguayenne':'UY',
    'us':'US',
    'us-iranienne':'US',
    'usa':'US',
    'usetroumaine':'RO',
    'venezuela':'VE',
    'venezuelien':'VE',
    'venezuellienne':'VE',
    'venezuélienne':'VE',
    'vénézuélienne':'VE',
    'vénézuelienne':'VE',
    'vénezuelien':'VE',
    'vientamienne':'VN',
    'vietnamieene':'VN',
    'vietnamien':'VN',
    'vietnamienne':'VN',
    'yemenite':'YE',
    'zimbabwéenne':'ZW',
    'égyptien':'EG',
    'égyptiene':'EG',
    'étasunienne':'US',
    'états-unienne':'US',
    'étatstunienne':'US',
    'étatsunienne':'US',
    'étatsunnienne':'US',
}

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

now = datetime.now()
formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

row = cursor4.fetchone()
while row is not None:
    if not row[23] and not row[29]:
        email = None
    elif not row[23]:
        email = row[29]
    else:
        email = row[23]

    if not row[25] and not row[26]:
        phone = ''
    elif not row[25]:
        phone = row[26]
    else:
        phone = row[25]
    if not row[19] and not row[20]:
        f_phone = ''
    elif not row[19]:
        f_phone = row[20]
    else:
        f_phone = row[19]

    state = row[42]
    if state == 'actif':
        state = 'A'
    elif state == 'inactif':
        state = 'P'
    elif state == 'clos':
        state = 'C'
    else:
        state = ''

    if row[11] == "carte_bleue_europeenne":
        proc = 'CBE'
    elif row[11] == "casier_judiciaire":
        proc = 'OD'
    elif row[11] == "commercant":
        proc = 'COM'
    elif row[11] == "competences_et_talents":
        proc = 'COT'
    elif row[11] == "detachement":
        proc = 'DET'
    elif row[11] == "intro_salarie_hn":
        proc = 'SAL'
    elif row[11] == "prestataire_service":
        proc = 'PSI'
    elif row[11] == "salarie_mission-detache":
        proc = 'SED'
    elif row[11] == "salarie_mission-salarie":
        proc = 'SES'
    elif row[11] == "stage_information":
        proc = 'STA'
    elif row[11] == "stage_professionnel":
        proc = 'STA'
    elif row[11] == "tir":
        proc = 'TIR'
    elif row[11] == 'apostille_legalisation':
        proc = 'OD'
    elif row[11] == 'apprenti':
        proc = 'AP'
    elif row[11] == 'carte_resident':
        proc = 'CR'
    elif row[11] == 'changement_de_status':
        proc = 'CDS'
    elif row[11] == 'changement_employeur':
        proc = 'CDE'
    elif row[11] == 'conjoint_europeen':
        proc = 'CEU'
    elif row[11] == 'conjoint_francais':
        proc = 'CFR'
    elif row[11] == 'consultation':
        proc = 'CON'
    elif row[11] == 'dcem':
        proc = 'DCE'
    elif row[11] == 'declaration_detachement_europeen':
        proc = 'DDD'
    elif row[11] == 'detache_ICT':
        proc = 'DI'
    elif row[11] == 'detache_ICT_mobile':
        proc = 'DIM'
    elif row[11] == 'dispense_AT_90j':
        proc = 'DAT'
    elif row[11] == 'nationalite':
        proc = 'NAT'
    elif row[11] == 'intro_salarie':
        proc = 'SAL'
    elif row[11] == 'passeport_talent_L313_20_1':
        proc = 'PT1'
    elif row[11] == 'passeport_talent_L313_20_2':
        proc = 'PT2'
    elif row[11] == 'passeport_talent_L313_20_3':
        proc = 'PT3'
    elif row[11] == 'passeport_talent_L313_20_4':
        proc = 'PT4'
    elif row[11] == 'passeport_talent_L313_20_8':
        proc = 'PT8'
    elif row[11] == 'passeport_talent_autre':
        proc = 'PTA'
    elif row[11] == 'stagiaire':
        proc = 'STA'
    elif row[11] == 'stagiaire_ICT':
        proc = 'SI'
    elif row[11] == 'stagiaire_ICT_mobile':
        proc = 'SIM'
    elif row[11] == 'URSSAF_CPAM':
        proc = 'URS'
    elif row[11] == 'visiteur':
        proc = 'VIR'
    elif row[11] == 'visa':
        proc = 'VIS'
    else:
        proc = 'AUT'

    no_etr = None
    comments = em(row[45])
    if row[3]:
        try:
            no_etr = int(row[3])
        except:
            print("failed to convert no_etr `%s' id:%d"%(row[3], row[0]))
            if comments:
                comments += '\n'
            comments += 'No étranger: ' + row[3]

    if row[6]:
        citizenship = row[6].lower()
        found = False
        for c in citizenship_mapping:
            if citizenship in c or c in citizenship:
                citizenship = citizenship_mapping[c]
                found = True
                break
        if not found:
            print("failed to convert citizenship `%s' id:%d"%(row[6], row[0]))
            print('exiting...')
            exit(1)
    else:
        citizenship = ''
    if row[43]:
        creation_date = row[43]
    else:
        creation_date = formatted_date

    sql_insert_query = """INSERT INTO `lgc_person`
    (`id`,`first_name`, `last_name`, `email`, `foreigner_id`,
    `birth_date`, `citizenship`, `passport_expiry`, `home_entity`, `home_entity_address`,
    `host_entity`, `host_entity_address`, `spouse_first_name`, `spouse_last_name`, `spouse_birth_date`,
    `spouse_citizenship`, `spouse_passport_expiry`, `local_address`, `local_phone_number`, `foreign_address`,
    `foreign_country`, `foreign_phone_number`, `modification_date`, `info_process`, `work_permit`,
    `start_date`, `state`, `comments`, `version`, `creation_date`,
    `prefecture`, `subprefecture`, `consulate`, `direccte`, `jurisdiction`,
    `is_private`)
    values (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s,
    %s
    )"""

    insert_tuple = (row[0], row[2], row[1], email, no_etr,
                    row[5], citizenship, row[13], em(row[7]), em(row[8]),
                    em(row[9]), em(row[10]), em(row[15]), em(row[14]), row[17],
                    '', row[18], em(row[30]), phone, em(row[24]),
                    '', f_phone, formatted_date, proc, 0,
                    row[43], state, comments, 0, creation_date,
                    '', '', '', '', '',
                    0
    )

    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting record into person table, id:', row[0])
        if error.errno == 1062:
            print('duplicated file id:', row[0], 'first_name:', row[2], 'last_name:',
                  row[1])
        else:
            print("{}".format(error))
            print('exiting...')
            exit()

    # import VLS-TS expiration
    if row[35] == None:
        # end date cannot be null
        row = cursor4.fetchone()
        continue
    sql_insert_query = """INSERT INTO `lgc_expiration`
    (`type`, `start_date`, `end_date`, `enabled`, `person_id`)
    values (%s, %s, %s, %s, %s)"""
    insert_tuple = ('VLS-TS', row[34], row[35], not row[36], row[0])
    try:
        result  = cursor5.execute(sql_insert_query, insert_tuple)
        lgc_v5.commit()
    except mysql.connector.Error as error :
        #lgc_v5.rollback() #rollback if any exception occured
        #print(sql_insert_query%insert_tuple)
        print('Failed inserting VLS-TS record into expiration table, id:', row[0])
        print("{}".format(error))
        print('exiting...')
        exit()

    row = cursor4.fetchone()
