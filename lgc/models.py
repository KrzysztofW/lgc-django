from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import ugettext_lazy as _
from django.utils import translation
from django.contrib.auth import get_user_model
from django.db import models
from datetime import date
import os, pdb
from django.conf import settings
from django_countries.fields import CountryField
from users import models as user_models
import common.validators as validators
import logging

log = logging.getLogger('lgc')
User = get_user_model()

class Currencies(models.Model):
    rate_eur = models.FloatField(_('EUR'), default=0)
    rate_usd = models.FloatField(_('USD'), default=0)
    rate_cad = models.FloatField(_('CAD'), default=0)
    rate_gbp = models.FloatField(_('GBP'), default=0)

    class Meta:
        abstract = True

class Settings(Currencies):
    pass

PROCESS_CHOICES = (
    ('', '---------'),
    ('OD', 'Obtention de docs/légalisation'),
    ('AP', 'Apprenti'),
    ('CR', 'Carte de résident'),
    ('CDS', 'Changement de statut'),
    ('CDE', "Changement d'employeur"),
    ('CEU', 'Conjoint UE'),
    ('CFR', 'Conjoint Fr'),
    ('CON', 'Consultation'),
    ('DCE', 'DCEM'),
    ('DDD', 'DDD UE'),
    ('DI', 'Détaché ICT'),
    ('DIM', 'Détaché ICT Mobile'),
    ('DAT', 'Dispense AT – 3 mois'),
    ('NAT', 'Nationalité'),
    ('SAL', 'Salarié'),
    ('PT1', 'Passeport talent 1°'),
    ('PT2', 'Passeport talent 2°'),
    ('PT3', 'Passeport talent 3°'),
    ('PT4', 'Passeport talent 4°'),
    ('PT8', 'Passeport talent 8°'),
    ('PT9', 'Passeport talent 9°'),
    ('PTA', 'Passeport talent – Autre'),
    ('PSI', 'PSI'),
    ('STA', 'Stagiaire'),
    ('SI', 'Stagiaire ICT'),
    ('SIM', 'Stagiaire ICT mobile'),
    ('URS', 'URSSAF/CPAM'),
    ('VIR', 'Visiteur'),
    ('VIS', 'Visa'),
    ('AUT', 'Autres'),
)

PREFECTURE_CHOICES = (
    ('', '---------'),
    ('AIN', "Ain (01)"),
    ('AIS', "Aisne (02)"),
    ('ALL', "Allier (03)"),
    ('ALP', "Alpes Maritimes (06)"),
    ('BOU', "Bouches du Rhône (13)"),
    ('CAL', "Calvados (14)"),
    ('CHA', "Charente (16)"),
    ('CHE', "Cher (18)"),
    ('COT', "Côte d'or (21)"),
    ('COA', "Côtes d'Armor (22)"),
    ('DOU', "Doubs (25)"),
    ('DRO', "Drôme (26)"),
    ('EUR', "Eure (27)"),
    ('EUL', "Eure et Loire (28)"),
    ('FIN', "Finistère (29)"),
    ('GAR', "Gard (30)"),
    ('HG', "Haute – Garonne (31)"),
    ('GER', "Gers (32)"),
    ('GIR', "Gironde (33)"),
    ('HER', "Hérault (34)"),
    ('ILL', "Ille et Vilaine (35)"),
    ('IND', "Indre et Loire (37)"),
    ('ISE', "Isère (38)"),
    ('LAN', "Landes (40)"),
    ('LEC', "Loir et Cher (41)"),
    ('LA', "Loire Atlantique (44)"),
    ('LOI', "Loiret (45)"),
    ('LOT', "Lot-et-Garonne (47)"),
    ('MAI', "Maine et Loire (49)"),
    ('HM', "Haute-Marne (52)"),
    ('MEU', "Meurthe et Moselle (54)"),
    ('MOS', "Moselle (57)"),
    ('NOR', "Nord (59)"),
    ('OIS', "Oise (60)"),
    ('PAS', "Pas-de-Calais (62)"),
    ('PUY', "Puy-de-dôme (63)"),
    ('PYR', "Pyrénées Atlantiques (64)"),
    ('BAS', "Bas-Rhin (67)"),
    ('HR', "Haut-Rhin (68)"),
    ('RHO', "Rhône-Alpes (69)"),
    ('SAO', "Saône et Loire (71)"),
    ('SAR', "Sarthe (72)"),
    ('SAV', "Savoie (73)"),
    ('HS', "Haute-Savoie (74)"),
    ('PAR', "London (75)"),
    ('SM', "Seine Maritime (76)"),
    ('SEM', "Seine et Marne (77)"),
    ('YVE', "Yvelines (78)"),
    ('DEU', "Deux-Sèvres (79)"),
    ('SOM', "Somme (80)"),
    ('TAR', "Tarn et Garonne (82)"),
    ('VAR', "Var (83)"),
    ('VAU', "Vaucluse (84)"),
    ('VIE', "Vienne (86)"),
    ('HV', "Haute-Vienne (87)"),
    ('TER', "Territoire de Belfort (90)"),
    ('ESS', "Essonne (91)"),
    ('HAS', "Hauts de Seine (92)"),
    ('SEI', "Seine St Denis (93)"),
    ('VM', "Val de Marne (94)"),
    ('VDO', "Val d'Oise (95)"),
    ('NOU', "Nouvelle Calédonie"),
    ('LA ', "La réunion (974)"),
)

SUBPREFECTURE_CHOICES = (
    ('', '---------'),
    ('MAR', "Marseille (13)"),
    ('AIX', "Aix en Provence (13)"),
    ('IST', "Istres (13)"),
    ('ST', "St Brieuc (22)"),
    ('LAN', "Lannion (22)"),
    ('BES', "Besançon (25)"),
    ('PON', "Pontarlier (25)"),
    ('QUI', "Quimper (29)"),
    ('BRE', "Brest (29)"),
    ('MON', "Montpellier (34)"),
    ('BEZ', "Béziers (34)"),
    ('NA', "Nantes (44)"),
    ('SA', "Saint-Nazaire (44)"),
    ('ANG', "Angers (49)"),
    ('SEG', "Segré (49)"),
    ('SAU', "Saumur (49)"),
    ('CHO', "Cholet(49)"),
    ('MET', "Metz (57)"),
    ('FOR', "Forbach (57)"),
    ('LIL', "Lille (59)"),
    ('VAL', "Valenciennes (59)"),
    ('CAM', "Cambrai (59)"),
    ('DOU', "Douai (59)"),
    ('BEA', "Beauvais (60)"),
    ('COM', "Compiègne (60)"),
    ('CR', "Creil (60)"),
    ('BAY', "Bayonne (64)"),
    ('PAU', "Pau (64)"),
    ('COL', "Colmar (68)"),
    ('MUL', "Mulhouse (68)"),
    ('ROU', "Rouen (76)"),
    ('LEH', "Le Havre (76)"),
    ('DIE', "Dieppe (76)"),
    ('MEL', "Melun (77)"),
    ('TOR', "Torcy (77)"),
    ('PRO', "Provins (77)"),
    ('MEA', "Meaux (77)"),
    ('FON', "Fontainebleau (77)"),
    ('VER', "Versailles (78)"),
    ('ST ', "St Germain en Laye (78)"),
    ('RAM', "Rambouillet (78)"),
    ('EVR', "Evry (91)"),
    ('ETA', "Etampes (91)"),
    ('PAL', "Palaiseau (91)"),
    ('NAN', "Nanterre (92)"),
    ('BOU', "Boulogne-Billancourt (92)"),
    ('ANT', "Antony (92)"),
    ('BOB', "Bobigny (93) "),
    ('SAI', "Saint Denis (93)"),
    ('LER', "Le Raincy (93)"),
    ('CRE', "Créteil (94)"),
    ('NOG', "Nogent-sur-Marne (94)"),
    ('LAY', "L'hay les Roses (94)"),
    ('CER', "Cergy (95)"),
    ('SAR', "Sarcelles  (95)"),
    ('ARG', "Argenteuil (95)"),
)

# the first two characters must match a real country code
JURISDICTION_SPECIFIQUE_CHOICES = (
    ('', '---------'),
    ('DEB', "Berlin (Allemagne)"),
    ('DEF', "Francfort (Allemagne)"),
    ('BRB', "Brasilia (Brésil)"),
    ('BRR', "Rio de Janeiro (Brésil)"),
    ('BRS', "Sao Paulo (Brésil)"),
    ('CAM', "Montréal (Canada)"),
    ('CAT', "Toronto (Canada)"),
    ('CAV', "Vancouver (Canada)"),
    ('CNP', "Pékin (Chine)"),
    ('CNS', "Shanghai (Chine)"),
    ('CNC', "Canton (Chine)"),
    ('CNW', "Wuhan (Chine)"),
    ('CNCH', "Chengdu (Chine)"),
    ('CNSH', "Shenyang (Chine)"),
    ('CNH', "Hong Kong (Chine)"),
    ('AEA', "Abou Dhabi ( Emirats Arabes Unis)"),
    ('AED', "Dubai (Emirats Arabes Unis)"),
    ('USA', "Atlanta (USA)"),
    ('USB', "Boston (USA)"),
    ('USC', "Chicago (USA)"),
    ('USH', "Houston (USA)"),
    ('USL', "Los Angeles (USA)"),
    ('USM', "Miami (USA)"),
    ('USN', "New York (USA)"),
    ('USNO', "Nouvelle Orléans (USA)"),
    ('USSA', "San Francisco (USA)"),
    ('USW', "Washington, DC (USA)"),
    ('INB', "Bangalore (Inde)"),
    ('INBO', "Bombay (Inde)"),
    ('INK', "Kolkatta (Inde)"),
    ('INP', "Pondichery (Inde)"),
    ('INN', "New Delhi (Inde)"),
    ('ILT', "Tel Aviv (Israel)"),
    ('ILJ', "Jérusalem (Israel)"),
    ('NGL', "Lagos (Nigéria) "),
    ('NGA', "Abuja (Nigéria)"),
    ('RUM', "Moscou (Russie)"),
    ('RUS', "St Petersbourg (Russie)"),
    ('RUI', "Iekaterinebourg (Russie)"),
    ('CHG', "Génève (Suisse)"),
    ('CHZ', "Zurich (Suisse)"),
    ('TRI', "Istanboul (Turquie)"),
    ('TRA', "Ankara (Turquie)"),
)

CONSULATE_CHOICES = (
    ('', '---------'),
    ('ZA', "Afrique Du Sud"),
    ('DE', "Allemagne"),
    ('DZ', "Algérie"),
    ('AO', "Angola"),
    ('AR', "Argentine"),
    ('SA', "Arabie Saoudite"),
    ('AM', "Arménie"),
    ('AU', "Australie"),
    ('AT', "Autriche"),
    ('BH', "Bahreïn"),
    ('BD', "Bangladesh"),
    ('BE', "Belgique"),
    ('BO', "Bolivie"),
    ('BR', "Brésil"),
    ('CA', "Canada"),
    ('CL', "Chili"),
    ('CN', "Chine"),
    ('CO', "Colombie"),
    ('KR', "Corée Du Sud"),
    ('CI', "Côte d'Ivoire"),
    ('CR', "Costa rica"),
    ('DK', "Danemark"),
    ('EG', "Egypte"),
    ('ES', "Espagne"),
    ('AE', "Emirats Arabes Unis"),
    ('EC', "Équateur"),
    ('US', "États-unis"),
    ('GH', "Ghana"),
    ('HU', "Hongrie"),
    ('IN', "Inde"),
    ('ID', "Indonésie"),
    ('IE', "Irlande"),
    ('IQ', "Irak"),
    ('IL', "Israël"),
    ('IT', "Italie"),
    ('JP', "Japon"),
    ('KZ', "Kazakhstan"),
    ('KE', "Kenya"),
    ('KW', "Kowait"),
    ('LB', "Liban"),
    ('MK', "Macédoine"),
    ('MO', "Maroc"),
    ('MU', "Maurice"),
    ('MX', "Mexique"),
    ('NG', "Nigéria"),
    ('NZ', "Nouvelle-Zélande"),
    ('PK', "Pakistan"),
    ('PE', "Perou"),
    ('PH', "Philippines"),
    ('PL', "Pologne"),
    ('QA', "Qatar"),
    ('CZ', "République Tchèque"),
    ('UK', "Royaume-Uni"),
    ('RU', "Russie"),
    ('SG', "Singapour"),
    ('SK', "Slovaquie"),
    ('SI', "Slovénie"),
    ('SE', "Suède"),
    ('CH', "Suisse"),
    ('TW', "Taiwan"),
    ('TZ', "Tanzanie"),
    ('TN', "Tunisie"),
    ('TR', "Turquie"),
    ('UA', "Ukraine"),
    ('VN', "Vietnam"),
)

DIRECCTE_CHOICES = (
    ('', '---------'),
    ('AIN', "Ain (01)"),
    ('AIS', "Aisne (02)"),
    ('ALL', "Allier (03)"),
    ('AL', "Alpes-de-Haute-Provence (04)"),
    ('HAL', "Hautes-Alpes (05)"),
    ('ALP', "Alpes Maritimes (06)"),
    ('ARD', "Ardèche (07)"),
    ('BO', "Bouches du Rhône (13)"),
    ('CAL', "Calvados (14)"),
    ('CHA', "Charente (16)"),
    ('CHE', "Cher (18)"),
    ('BOU', "Bourgogne (21)"),
    ('DOU', "Doubs (25)"),
    ('EU', "Eure (27)"),
    ('EUR', "Eure et Loire (28)"),
    ('FIN', "Finistère (29)"),
    ('GAR', "Gard (30)"),
    ('HGA', "Haute Garonne (31)"),
    ('GIR', "Gironde (33)"),
    ('HER', "Hérault (34)"),
    ('ILL', "Ille-et-Vilaine (35)"),
    ('IND', "Indre (36)"),
    ('IEL', "Indre et Loire (37)"),
    ('ISE', "Isère (38)"),
    ('LAN', "Landes (40)"),
    ('LEC', "Loir et Cher (41)"),
    ('HLO', "Haute Loire (43)"),
    ('LOA', "Loire Atlantique (44)"),
    ('LOI', "Loiret (45)"),
    ('LOT', "Lot (46)"),
    ('MAI', "Maine et Loire (49)"),
    ('MAN', "Manche (50)"),
    ('MA', "Marne (51)"),
    ('HMA', "Haute Marne (52)"),
    ('MEM', "Meurthe et Moselle (54)"),
    ('MEU', "Meuse (55)"),
    ('MOR', "Morbihan (56)"),
    ('MOS', "Moselle (57)"),
    ('NOR', "Nord (59)"),
    ('OIS', "Oise (60)"),
    ('PAS', "Pas de Calais (62)"),
    ('PUY', "Puy-de-Dôme (63)"),
    ('PYR', "Pyrénées Atlantiques"),
    ('(64', "(64)"),
    ('BAS', "Bas-Rhin (67)"),
    ('HRH', "Haut-Rhin (68)"),
    ('RHO', "Rhône (69)"),
    ('HS', "Haute-Saône (70)"),
    ('SAO', "Saône et Loire (71)"),
    ('SAR', "Sarthe (72)"),
    ('SAV', "Savoie (73)"),
    ('HSA', "Haute-Savoie (74)"),
    ('PAR', "London (75)"),
    ('SM', "Seine-Maritime (76)"),
    ('SEM', "Seine-et-Marne (77)"),
    ('YVE', "Yvelines (78)"),
    ('DEU', "Deux-Sèvres (79)"),
    ('SOM', "Somme (80)"),
    ('TAR', "Tarn (81) "),
    ('TEG', "Tarn-et-Garonne (82)"),
    ('VAR', "Var (83)"),
    ('VAU', "Vaucluse (84)"),
    ('VIE', "Vienne (86)"),
    ('HVI', "Haute-Vienne (87)"),
    ('YON', "Yonne (89)"),
    ('TER', "Territoire de Belfort (90)"),
    ('ESS', "Essonne (91)"),
    ('HDS', "Hauts-de-Seine (92)"),
    ('SEI', "Seine-St-Denis (93)"),
    ('VDM', "Val-de-Marne (94)"),
    ('VAL', "Val-d’Oise (95)"),
    ('REU', "Réunion (97)"),
    ('GUA', "Guadeloupe (97)"),
    ('MAR', "Martinique (972)"),
    ('NOU', "Nouvelle Calédonie (988)"),
)

EXPIRATION_TYPE_WP = 'WP'
EXPIRATION_TYPE_SWP = 'SWP'
EXPIRATION_TYPE_VLS  = 'VLS-TS'
EXPIRATION_TYPE_SVLS = 'SVLS-TS'
EXPIRATION_TYPE_CST  = 'CST'
EXPIRATION_TYPE_SCST = 'SCST'
EXPIRATION_TYPE_CSP = 'CSP'
EXPIRATION_TYPE_SCSP = 'SCSP'
EXPIRATION_TYPE_APS = 'APS'
EXPIRATION_TYPE_SAPS = 'SAPS'
EXPIRATION_TYPE_DCEM = 'DCEM'

work_permit = _('Work Permit')
vls_ts = _('Visa or Residence Permit (VLS-TS)')
cst = _('Visa or Residence Permit (CST)')
csp = _('Visa or Residence Permit (CSP)')
aps = _('Visa or Residence Permit (APS)')
dcem = 'VLS-TS/DCEM'

s_work_permit = _('Spouse Work Permit')
s_vls_ts = _('Spouse Visa or Residence Permit (VLS-TS)')
s_cst = _('Spouse Visa or Residence Permit (CST)')
s_csp = _('Spouse Visa or Residence Permit (CSP)')
s_aps = _('Spouse Visa or Residence Permit (APS)')

compact_s_work_permit = _('Spouse WP')
compact_s_vls_ts = _('Spouse VLS-TS')
compact_s_cst = _('Spouse CST')
compact_s_csp = _('Spouse CSP')
compact_s_aps = _('Spouse APS')

PERSON_EXPIRATIONS_CHOICES = (
    (EXPIRATION_TYPE_WP, work_permit),
    (EXPIRATION_TYPE_VLS, vls_ts),
    (EXPIRATION_TYPE_CST, cst),
    (EXPIRATION_TYPE_CSP, csp),
    (EXPIRATION_TYPE_APS, aps),
)

PERSON_SPOUSE_EXPIRATIONS_CHOICES = (
    (EXPIRATION_TYPE_SWP, s_work_permit),
    (EXPIRATION_TYPE_SVLS, s_vls_ts),
    (EXPIRATION_TYPE_SCST, s_cst),
    (EXPIRATION_TYPE_SCSP, s_csp),
    (EXPIRATION_TYPE_SAPS, s_aps),
)

PERSON_SPOUSE_EXPIRATIONS_CHOICES_SHORT = (
    (EXPIRATION_TYPE_SWP, work_permit),
    (EXPIRATION_TYPE_SVLS, vls_ts),
    (EXPIRATION_TYPE_SCST, cst),
    (EXPIRATION_TYPE_SCSP, csp),
    (EXPIRATION_TYPE_SAPS, aps),
)

PERSON_EXPIRATIONS_CHOICES_COMPACT = (
    (EXPIRATION_TYPE_SWP, compact_s_work_permit),
    (EXPIRATION_TYPE_SVLS, compact_s_vls_ts),
    (EXPIRATION_TYPE_SCST, compact_s_cst),
    (EXPIRATION_TYPE_SCSP, compact_s_csp),
    (EXPIRATION_TYPE_SAPS, compact_s_aps),
    (EXPIRATION_TYPE_DCEM, dcem),
)

EXPIRATION_CHOICES_DCEM = (
    (EXPIRATION_TYPE_DCEM, dcem),
)
EXPIRATION_CHOICES = PERSON_EXPIRATIONS_CHOICES + PERSON_SPOUSE_EXPIRATIONS_CHOICES

def get_expiration_list():
    return [(i[0]) for i in PERSON_EXPIRATIONS_CHOICES]

def get_spouse_expiration_list():
    return [(i[0]) for i in PERSON_SPOUSE_EXPIRATIONS_CHOICES]

FILE_STATE_ACTIVE  = 'A'
FILE_STATE_PENDING = 'P'
FILE_STATE_CLOSED  = 'C'

FILE_STATE_CHOICES = (
    (FILE_STATE_ACTIVE, _('Active')),
    (FILE_STATE_PENDING, _('Pending')),
    (FILE_STATE_CLOSED, _('Closed')),
)

def check_dates(start, end, what):
    if start and end and end <= start:
        raise ValidationError(_("End date of %s cannot be earlier than start date"%(what)))

class PersonInfo(models.Model):
    is_private = models.BooleanField(_('Private File'), default=False)
    version = models.PositiveIntegerField(default=0)
    creation_date = models.DateTimeField(_('Creation Date'), auto_now_add=True)
    first_name = models.CharField(_('First name'), max_length=50, validators=[validators.alpha])
    last_name = models.CharField(_('Last name'), max_length=50, validators=[validators.alpha])
    email = models.EmailField('Email', max_length=60, null=True)
    foreigner_id = models.BigIntegerField(_('Foreigner ID'), blank=True, null=True,
                                          validators=[MinValueValidator(0)])
    birth_date = models.DateField(_('Birth Date'), null=True)
    citizenship = CountryField(_('Citizenship'), blank=True, null=True)
    passport_expiry = models.DateField(_('Passport Expiry'), blank=True,
                                       null=True, default=None)
    passport_nationality = CountryField(_('Passport Nationality'), blank=True,
                                        null=True)
    home_entity = models.CharField(_('Home entity'), max_length=50,
                                   default='', blank=True, validators=[validators.alphanum])
    home_entity_address = models.TextField(_('Home Entity address'),
                                           max_length=100, default='',
                                           blank=True)
    host_entity = models.CharField(_('Host entity'), max_length=50,
                                   default='', blank=True, validators=[validators.alphanum])
    host_entity_address = models.TextField(_('Host Entity address'),
                                           max_length=100, default='',
                                           blank=True)

    spouse_first_name = models.CharField(_('Spouse First Name'),
                                         max_length=50, default='',
                                         blank=True, validators=[validators.alpha])
    spouse_last_name = models.CharField(_('Spouse Last Name'),
                                        max_length=50, default='',
                                        blank=True, validators=[validators.alpha])
    spouse_birth_date = models.DateField(_('Spouse Birth Date'), blank=True,
                                         null=True)
    spouse_citizenship = CountryField(_('Spouse Citizenship'), blank=True,
                                      null=True)
    spouse_passport_expiry = models.DateField(_('Spouse Passport Expiry'),
                                              blank=True, null=True,
                                              default=None)
    spouse_passport_nationality = CountryField(_('Spouse Passport Nationality'),
                                               blank=True, null=True)

    local_address = models.TextField(_('Local Address'), max_length=100,
                                     default='', blank=True)

    local_phone_number = models.CharField(_('Local Phone Number'),
                                          max_length=50, default='',
                                          blank=True)

    foreign_address = models.TextField(_('Foreign Address'), max_length=100,
                                       default='', blank=True)
    foreign_country = CountryField(_('Foreign Country'), blank=True,
                                   null=True)
    foreign_phone_number = models.CharField(_('Foreign Phone Number'),
                                            max_length=50, default='',
                                            blank=True)
    modified_by = models.ForeignKey(User, verbose_name=_('Modified by'),
                                    on_delete=models.SET_NULL, null=True)
    modification_date = models.DateTimeField(_('Modification date'), auto_now_add=True)

    class Meta:
        abstract = True

    def validate_unique(self, exclude=None):
        super().validate_unique()
        if self.birth_date == None and Person.objects.exclude(id=self.id).filter(first_name=self.first_name, last_name=self.last_name, birth_date__isnull=True).exists():
            raise ValidationError(_("A person with this First Name, Last Name and Birth Date already exists."))

    def __str__(self):
        if self.first_name != '' or self.last_name != '':
            return self.first_name + ' ' + self.last_name
        return ''
    def save(self, *args, **kwargs):
        self.modification_date = timezone.now()
        return super().save(*args, **kwargs)

class Person(PersonInfo):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                null=True, blank=True,
                                related_name='person_user_set')

    # Préfecture / OFII compétent
    prefecture = models.CharField(_('Prefecture'),
                                  max_length=3, default='',
                                  choices=PREFECTURE_CHOICES, blank=True)
    # Sous-Préfecture
    subprefecture = models.CharField(_('Subprefecture'),
                                     max_length=3, default='',
                                     choices=SUBPREFECTURE_CHOICES,
                                     blank=True)
    consulate = models.CharField(_('Consulate'), max_length=3, default='',
                                choices=CONSULATE_CHOICES, blank=True)
    # Direccte compétente
    direccte = models.CharField('DIRECCTE', max_length=3,
                                default='', choices=DIRECCTE_CHOICES,
                                blank=True)
    # Juridiction spécifique
    jurisdiction = models.CharField(_('Jurisdiction'), max_length=4,
                                    default='',
                                    choices=JURISDICTION_SPECIFIQUE_CHOICES,
                                    blank=True)
    info_process = models.CharField(_('Immigration Process'), max_length=3, default='',
                                    choices=PROCESS_CHOICES)
    work_permit = models.BooleanField(_('Work Permit Required'), default=False)
    responsible = models.ManyToManyField(User, blank=True,
                                         verbose_name=_('Persons in charge'),
                                         related_name='person_resp_set')
    start_date = models.DateField(_('Start Date'), blank=True, null=True)

    state = models.CharField(_('State'), max_length=3,
                             default=FILE_STATE_ACTIVE,
                             choices=FILE_STATE_CHOICES)
    comments = models.TextField(_('Comments'), max_length=100, default='',
                                blank=True)

    class Meta:
        unique_together = ('first_name', 'last_name', 'birth_date',
                           'is_private', 'home_entity', 'host_entity')

PERSON_DOC_LINK_DIR = os.path.join(settings.MEDIA_ROOT, 'files')

def copy_doc_path_attributes(src, dst):
    dst.birth_date = src.birth_date
    dst.first_name = src.first_name
    dst.last_name = src.last_name
    dst.home_entity = src.home_entity
    dst.host_entity = src.host_entity
    dst.is_private = src.is_private

def get_person_doc_path(person):
    directory = person.first_name + '_' + person.last_name
    if person.birth_date:
        directory += '_' + str(person.birth_date)
    if person.home_entity:
        directory += '_' + person.home_entity
    if person.host_entity:
        directory += '_' + person.host_entity
    if person.is_private:
        directory += '_private'
    return directory

def rename_person_doc_dir(old_obj, new_obj):
    old_path = os.path.join(PERSON_DOC_LINK_DIR, get_person_doc_path(old_obj))
    new_path = os.path.join(PERSON_DOC_LINK_DIR, get_person_doc_path(new_obj))

    if old_path == new_path:
        return

    try:
        log.debug("renaming: `%s' into `%s'", old_path, new_path)
        os.rename(old_path, new_path)
    except Exception as e:
        log.error("renaming failed: `%s' into `%s' (%s)", old_path, new_path,
                  e)

def delete_person_doc(person, doc):
    link = os.path.join(PERSON_DOC_LINK_DIR, get_person_doc_path(person),
                        doc.filename)
    doc_file = os.path.join(settings.MEDIA_ROOT, doc.document.name)
    link_dirname = os.path.dirname(link)

    # remove the link
    try:
        os.remove(link)
    except:
        pass

    os.remove(doc_file)
    doc.delete()

    # remove the directories if empty
    try:
        os.rmdir(os.path.dirname(doc.document.path))
        os.rmdir(link_dirname)
    except:
        pass

def create_doc_directory(instance, filename):
    person = instance.person
    src = os.path.join('file_ids', str(person.id), filename)
    link_file_src = os.path.join('..', '..', src)
    link_dst = os.path.join(PERSON_DOC_LINK_DIR,
                            get_person_doc_path(person), filename)
    try:
        os.mkdir(PERSON_DOC_LINK_DIR)
    except:
        pass
    try:
        os.mkdir(os.path.dirname(link_dst))
    except:
        pass
    try:
        os.mkdir(os.path.dirname(src))
    except:
        pass
    try:
        os.symlink(link_file_src, link_dst)
    except Exception as e:
        log.error(e)

    return src

class Document(models.Model):
    document = models.FileField(_('File'), upload_to=create_doc_directory)
    uploaded_date = models.DateTimeField(_('Uploaded'), auto_now_add=True)
    uploaded_by = models.ForeignKey(User, verbose_name=_('Uploaded by'),
                                    on_delete=models.SET_NULL, null=True)
    description = models.CharField(_('Description'), max_length=50, default='')
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                               related_name='document_set')

    @property
    def filename(self):
        return os.path.basename(self.document.name)

    @property
    def file_exists(self):
        return os.path.isfile(self.document.path)

class ExpirationCommon(models.Model):
    label = _('Visas / Residence Permits / Work Permits')
    type = models.CharField(max_length=7, default='', choices=EXPIRATION_CHOICES + EXPIRATION_CHOICES_DCEM)
    start_date = models.DateField(null=True, default=None)
    end_date = models.DateField()
    enabled = models.BooleanField(default=True)

    def clean(self, model_class=None):
        check_dates(self.start_date, self.end_date, self.label)
        return super().clean()

    class Meta:
        abstract = True

class Expiration(ExpirationCommon):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

class ArchiveBox(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    number = models.PositiveIntegerField(_('Number'))

class ChildCommon(models.Model):
    first_name = models.CharField(verbose_name=_('First name'), max_length=50,
                                  validators=[validators.alpha])
    birth_date = models.DateField(_('Birth date'), blank=True, null=True)
    passport_expiry = models.DateField(_('Passport expiry'), blank=True, null=True)
    passport_nationality = CountryField(_('Passport nationality'), blank=True, null=True)

    class Meta:
        abstract = True

class Child(ChildCommon):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    expiration = models.ForeignKey(Expiration, related_name='child_set',
                                   on_delete=models.SET_NULL,
                                   default=None, null=True)

class ProcessStage(models.Model):
    name_fr = models.CharField(_('French Name'), max_length=50, unique=True)
    name_en = models.CharField(_('English Name'), max_length=50, unique=True)
    noinvoice_alert = models.BooleanField(_('Generates an alert'), default=False)

    def __str__(self):
        if translation.get_language() == 'fr':
            return self.name_fr
        else:
            return self.name_en

class Process(models.Model):
    name_fr = models.CharField(_('French Name'), max_length=50, unique=True)
    name_en = models.CharField(_('English Name'), max_length=50, unique=True)
    stages = models.ManyToManyField(ProcessStage, verbose_name=_('Stages'))

    def __str__(self):
        if translation.get_language() == 'fr':
            return self.name_fr
        else:
            return self.name_en

class PersonProcess(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                               related_name='personprocess_set')
    process = models.ForeignKey(Process, null=True, on_delete=models.SET_NULL)
    name_fr = models.CharField(_('Name'), max_length=50, default='',
                               blank=True)
    name_en = models.CharField(_('Name'), max_length=50, default='',
                               blank=True)
    active = models.BooleanField(_('Active'), default=True)
    consulate = models.CharField(_('Consulate'), max_length=3, default='',
                                 choices=CONSULATE_CHOICES, blank=True)
    # Préfecture / OFII compétent
    prefecture = models.CharField(_('Prefecture'),
                                  max_length=3, default='',
                                  choices=PREFECTURE_CHOICES, blank=True)
    no_billing = models.BooleanField(_('No billing for this process'),
                                     default=False)
    alert_on = models.BooleanField(default=False)

    invoice = None
    quotation = None
    credit_note = None

    @property
    def get_quotation(self):
        if self.quotation:
            return self.quotation
        quotes = Invoice.objects.filter(process=self).filter(type=QUOTATION).all()
        length = len(quotes)

        if length:
            if length > 1:
                log.error('process %d has more than one quotation', self.id)
            self.quotation = quotes[0]
            return quotes[0]
        return None

    @property
    def get_invoice(self):
        if self.invoice:
            return self.invoice
        invoices = Invoice.objects.filter(process=self).filter(type=INVOICE).all()
        length = len(invoices)

        if length:
            if length > 1:
                log.error('process %d has more than one invoice', self.id)
            self.invoice = invoices[0]
            return invoices[0]
        return None

    @property
    def get_credit_note(self):
        if self.credit_note:
            return self.credit_note
        credit_notes = Invoice.objects.filter(process=self).filter(type=CREDIT).all()
        length = len(credit_notes)

        if length:
            if length > 1:
                log.error('process %d has more than one credit note', self.id)
            self.credit_note = credit_notes[0]
            return credit_notes[0]
        return None

class PersonProcessStage(models.Model):
    person_process = models.ForeignKey(PersonProcess,
                                       related_name="stages",
                                       on_delete=models.CASCADE)
    name_fr = models.CharField(_('French Name'), max_length=50, default='',
                               blank=True)
    name_en = models.CharField(_('English Name'), max_length=50, default='',
                               blank=True)
    is_specific = models.BooleanField(default=False)
    validation_date = models.DateField(blank=True, null=True)
    stage_comments = models.TextField(max_length=100, default='', blank=True)

class AbstractClient(models.Model):
    first_name = models.CharField(_('First name'), max_length=50,
                                  validators=[validators.alpha], blank=True)
    last_name = models.CharField(_('Last name'), max_length=50,
                                 validators=[validators.alpha], blank=True)
    company = models.CharField(_('Company'), max_length=50, blank=True)
    email = models.EmailField('Email', max_length=60, null=True, blank=True)
    phone_number = models.CharField(_('Local Phone Number'), max_length=50,
                                    blank=True)
    cell_phone_number = models.CharField(_('Cell Phone Number'), max_length=50,
                                         blank=True)
    siret = models.CharField('SIRET', max_length=14, blank=True, null=True,
                             validators=[validators.siret])
    vat = models.CharField(_('VAT Number'), max_length=50, null=True,
                           blank=True, unique=True)
    address = models.TextField(_('Address'), max_length=100, blank=True)
    post_code = models.CharField(_('Post Code'), max_length=10, blank=True)
    city = models.CharField(_('City'), max_length=50, blank=True)
    country = CountryField(_('Country'), blank=True)

    class Meta:
        abstract = True

class Client(AbstractClient):
    id = models.AutoField(primary_key=True)
    billing_company = models.CharField(_('Company'), max_length=50, blank=True)
    billing_address = models.TextField(_('Address'), max_length=100, blank=True)
    billing_post_code = models.CharField(_('Post Code'), max_length=10, blank=True)
    billing_city = models.CharField(_('City'), max_length=50, blank=True)
    billing_country = CountryField(_('Country'), blank=True)

    class Meta:
        unique_together = ('first_name', 'last_name', 'company')

INVOICE = 'I'
QUOTATION = 'Q'
CREDIT = 'C'

INVOICE_CHOICES = (
    (INVOICE, _('Invoice')),
    (QUOTATION, _('Quotation')),
    (CREDIT, _('Credit Note')),
)
CURRENCY_CHOICES = (
    ('EUR', _('Euro')),
    ('USD', _('Dollar')),
    ('GBP', _('Pound')),
    ('CAD', _('Canadian Dollar')),
)
INVOICE_STATE_CANCELED = 'C'
INVOICE_STATE_TOBEDONE = 'T'
INVOICE_STATE_DONE = 'D'
INVOICE_STATE_PENDING = 'P'
INVOICE_STATE_PAID = 'V'

INVOICE_STATE_CHOICES = (
    (INVOICE_STATE_PENDING, _('Pending')),
    (INVOICE_STATE_TOBEDONE, _('To be done')),
    (INVOICE_STATE_DONE, _('Done')),
    (INVOICE_STATE_CANCELED, _('Canceled')),
    (INVOICE_STATE_PAID, _('Paid')),
)
INVOICE_PAYMENT_CHOICES = (
    ('', '---------'),
    ('CB', _('Credit card')),
    ('CH', _('Check')),
    ('BT', _('Bank transfer')),
    ('CA', _('Cash')),
)
INVOICE_COMPANY_CHOICES = (
    ('L', _('Home')),
    ('F', _('Host')),
)
VAT_CHOICES = (
    (0.0, 0),
    (20.0, 20),
)

class BillingGlobalSettings(models.Model):
    next_invoice_number = models.PositiveIntegerField(_('Next Invoice Number'))
    next_quotation_number = models.PositiveIntegerField(_('Next Quotation Number'))

class Invoice(AbstractClient):
    total_items = 0.
    total_items_vat = 0.
    total_disbursements = 0.
    total_disbursements_vat = 0.

    id = models.AutoField(primary_key=True)
    version = models.PositiveIntegerField(default=0)
    client = models.ForeignKey(Client, null=True, on_delete=models.SET_NULL)
    number = models.PositiveIntegerField()
    type = models.CharField(max_length=1, default='I', choices=INVOICE_CHOICES)
    person = models.ForeignKey(Person, null=True, on_delete=models.SET_NULL,
                               related_name='invoice_set')
    process = models.ForeignKey(PersonProcess, on_delete=models.SET_NULL,
                                null=True, related_name='invoice_set')

    invoice_date = models.DateField(_('Invoice Date'))
    modification_date = models.DateField(_('Modification Date'), null=True)
    modified_by = models.ForeignKey(User, verbose_name=_('Modified by'),
                                    on_delete=models.SET_NULL, null=True)
    last_modified_date = models.DateField(auto_now_add=True)
    payment_option = models.CharField(max_length=2, default='TR', blank=True,
                                      choices=INVOICE_PAYMENT_CHOICES)
    currency = models.CharField(_('Currency'), max_length=3, default='EUR',
                                choices=CURRENCY_CHOICES)
    email = models.EmailField('Email', max_length=60, null=True, blank=True)
    siret = models.CharField('SIRET', max_length=14, blank=True, null=True,
                             validators=[validators.siret])
    vat = models.CharField(_('VAT Number'), max_length=50, null=True,
                           blank=True)

    """Autorisations"""
    po = models.CharField('PO', max_length=50, blank=True)
    po_date = models.DateField(_('Date'), null=True, blank=True)
    po_first_name = models.CharField(_('First name'), max_length=50,
                                     validators=[validators.alpha], blank=True)
    po_last_name = models.CharField(_('Last name'), max_length=50,
                                    validators=[validators.alpha], blank=True)
    po_email = models.EmailField('Email', max_length=60, null=True, blank=True)
    po_rate = models.FloatField(_('Rate'), null=True, blank=True)

    company_option = models.CharField(_('Company'), max_length=1, default='L',
                                      choices=INVOICE_COMPANY_CHOICES)
    language = models.CharField(max_length=2, choices=user_models.LANGUAGE_CHOICES,
                                default=user_models.EN)

    invoice_description = models.TextField(_('Description'), max_length=50,
                                           blank=True)
    various_expenses = models.BooleanField(_('Include Various Expenses'), default=False)
    state = models.CharField(_('State'), max_length=1, default=INVOICE_STATE_PENDING,
                             choices=INVOICE_STATE_CHOICES)
    already_paid = models.DecimalField(_('Already Paid'), default=0, max_digits=8,
                                       decimal_places=2)
    already_paid_desc = models.CharField(_('Description'), max_length=50, blank=True)
    with_regard_to = models.CharField(_('With regard to'), max_length=100,
                                      validators=[validators.alpha], blank=True)
    total = models.DecimalField(_('Total'), default=0, max_digits=8, decimal_places=2)

    def validate_unique(self, exclude=None):
        super().validate_unique()
        if self.process_id == None:
            return
        if self.type == INVOICE:
            objs = Invoice.objects.filter(type=INVOICE, process_id=self.process_id)
            if len(objs) > 1:
                raise ValidationError(_('The process has already an invoice.'))

        elif self.type == QUOTATION:
           objs = Invoice.objects.filter(type=QUOTATION, process_id=self.process_id)
           if len(objs) > 1:
               raise ValidationError(_('The process has already a quotation.'))

        elif self.type == CREDIT:
           objs = Invoice.objects.filter(type=CREDIT, process_id=self.process_id)
           if len(objs) > 1:
               raise ValidationError(_('The process has already a credit note.'))

    @property
    def person_first_name(self):
        if self.person == None:
            return None
        return self.person.first_name

    @property
    def person_last_name(self):
        if self.person == None:
            return None
        return self.person.last_name

    @property
    def person_home_entity(self):
        if self.person == None:
            return None
        return self.person.home_entity

    @property
    def person_host_entity(self):
        if self.person == None:
            return None
        return self.person.host_entity

    @property
    def get_process(self):
        if not self.process:
            return None
        if translation.get_language() == 'fr':
            return self.process.name_fr
        return self.process.name_en

    @property
    def entity_info(self):
        if self.person == None:
            return None
        if self.person.home_entity:
            return self.person.home_entity
        return self.person.host_entity

    @property
    def get_client_id(self):
        if self.client:
            return self.client.id
        return None

    @property
    def client_info(self):
        if self.company:
            return self.company
        return self.first_name + ' ' + self.last_name

    @property
    def person_info(self):
        if self.person == None:
            return None
        if self.person.first_name and self.person.last_name:
            return self.person.first_name + ' ' + self.person.last_name
        return ''


    @property
    def validated(self):
        return self.state == INVOICE_STATE_PAID

    @property
    def to_be_done(self):
        return self.state == INVOICE_STATE_TOBEDONE

    def get_item_total(self, obj):
        total = round(obj.quantity * obj.rate, 2)
        obj_vat = float(obj.vat) / 100.
        vat = round(total * obj_vat, 2)
        vat = total * obj_vat

        """Save the first item's VAT to compute various expenses."""
        if not hasattr(self, 'item_vat'):
            self.item_vat = obj_vat
        return total, vat

    def get_disbursement_total(self, obj):
        quantity_rate = round(obj.quantity * obj.rate, 2)
        obj_vat = float(obj.vat) / 100.
        total = quantity_rate
        if obj.margin:
            total *= 1 + 0.2
        total = round(total, 2)
        vat = round(total * obj_vat, 2)
        vat = round(total * obj_vat, 2)
        return total, vat

    def _get_various_expenses(self):
        self.set_total_items()
        if not hasattr(self, 'item_vat'):
            return 0, 0
        ve = self.total_items * 0.05
        if ve > 100:
            ve = 100
        vat = ve * self.item_vat
        return ve, vat

    @property
    def get_various_expenses(self):
        ve, vat = self._get_various_expenses()
        return ve

    @property
    def get_various_expenses_vat(self):
        ve, vat = self._get_various_expenses()
        return vat

    @property
    def get_various_expenses_plus_vat(self):
        ve, vat = self._get_various_expenses()
        return ve + vat

    @property
    def remaining_balance(self):
        return self.total - self.already_paid

    def set_total_items(self):
        if self.total_items:
            return
        total = 0.
        total_vat = 0.
        for i in self.item_set.all():
            total, total_vat = self.get_item_total(i)
            self.total_items += total
            self.total_items_vat += total_vat
        self.total_items = round(self.total_items, 2)
        self.total_items_vat = round(self.total_items_vat, 2)

    def set_total_disbursements(self):
        if self.total_disbursements:
            return
        total = 0.
        total_vat = 0.
        for i in self.disbursement_set.all():
            total, total_vat = self.get_disbursement_total(i)
            self.total_disbursements += total
            self.total_disbursements_vat += total_vat
        if self.various_expenses:
            ve, ve_vat = self._get_various_expenses()
            self.total_disbursements += ve
            self.total_disbursements_vat += ve_vat
        self.total_disbursements = round(self.total_disbursements, 2)
        self.total_disbursements_vat = round(self.total_disbursements_vat, 2)

    @property
    def get_total_items(self):
        self.set_total_items()
        return self.total_items

    @property
    def get_total_items_vat(self):
        self.set_total_items()
        return self.total_items_vat

    @property
    def get_total_items_plus_vat(self):
        self.set_total_items()
        return round(self.total_items_vat + self.total_items, 2)

    @property
    def get_total_disbursements(self):
        self.set_total_disbursements()
        return self.total_disbursements

    @property
    def get_total_disbursements_vat(self):
        self.set_total_disbursements()
        return self.total_disbursements_vat

    @property
    def get_total_disbursements_plus_vat(self):
        self.set_total_disbursements()
        return round(self.total_disbursements +
                     self.total_disbursements_vat, 2)

    @property
    def get_total_disbursements_no_various_expenses(self):
        ve = self.get_various_expenses
        return round(self.total_disbursements - ve, 2)

    @property
    def get_total_disbursements_plus_vat_no_various_expenses(self):
        ve, vat = self._various_expenses()
        return round(self.get_total_disbursements_plus_vat - ve - vat, 2)

    @property
    def get_total_plus_vat(self):
        self.set_total_items()
        self.set_total_disbursements()
        ret = (self.total_items + self.total_items_vat +
               self.total_disbursements + self.total_disbursements_vat)
        ret = round(ret, 2)
        if ret != float(self.total):
            pdb.set_trace()
            log.error('invalid total: stored:%f, computed:%f, id:%d',
                      self.total, ret, self.id)

        return ret

    @property
    def get_total(self):
        self.set_total_items()
        self.set_total_disbursements()
        return round(self.total_items + self.total_disbursements, 2)

    @property
    def get_vat(self):
        self.set_total_items()
        self.set_total_disbursements()
        ret = self.total_items_vat + self.total_disbursements_vat
        return round(ret, 2)

    @property
    def validation_date(self):
        if self.state == INVOICE_STATE_PAID:
            return self.modification_date
        return None

    class Meta:
        unique_together = ('number', 'type')

class DisbursementCommon(models.Model):
    id = models.AutoField(primary_key=True)
    disbursement_id = models.CharField(_('ID'), default='', max_length=9)
    description = models.TextField(_('Description'), max_length=50)
    rate = models.FloatField(_('Rate'), default=0)

    class Meta:
        abstract = True

class Disbursement(DisbursementCommon):
    disbursement_id = None
    title = models.CharField(_('Title'), max_length=50, unique=True)
    currency = models.CharField(_('Currency'), max_length=3, default='EUR',
                                choices=CURRENCY_CHOICES)

class InvoiceDisbursement(DisbursementCommon):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                related_name='disbursement_set')
    quantity = models.PositiveIntegerField(_('Quantity'), default=0)
    vat = models.FloatField(_('VAT'), default=0, choices=VAT_CHOICES)
    margin = models.BooleanField(_('20% margin'), default=False)

class ItemCommon(models.Model):
    id = models.AutoField(primary_key=True)
    item_id = models.CharField(_('ID'), default='', max_length=9)
    description = models.TextField(_('Description'), max_length=50)
    class Meta:
        abstract = True

class Item(Currencies, ItemCommon):
    item_id = None
    title = models.CharField(_('Title'), max_length=50, unique=True)

class InvoiceItem(ItemCommon):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                related_name='item_set')
    rate = models.FloatField(_('Rate'), default=0)
    quantity = models.PositiveIntegerField(_('Quantity'), default=0)
    vat = models.FloatField(_('VAT'), default=0, choices=VAT_CHOICES)

def create_disbursement_directory(instance, filename):
    invoice = instance.invoice
    subdir = str((int(invoice.id / 100)) * 100).zfill(3)
    dst = os.path.join('disbursement_receipts', subdir, str(invoice.id), filename)

    try:
        os.mkdir(os.path.dirname(dst))
    except:
        pass
    return dst

class DisbursementDocument(models.Model):
    document = models.FileField(_('File'), upload_to=create_disbursement_directory)
    description = models.CharField(_('Description'), max_length=50, default='')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,
                                related_name='document_set')

    @property
    def filename(self):
        return os.path.basename(self.document.name)

    @property
    def file_exists(self):
        return os.path.isfile(self.document.path)
