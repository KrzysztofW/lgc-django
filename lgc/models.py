from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.utils import translation
from django.contrib.auth import get_user_model
from django.db import models
from datetime import date
from django_countries.fields import CountryField
User = get_user_model()

alpha = RegexValidator(r'^[^0-9`;:_{}()$^~"\%&*#!?.,\\<>|@/]*$',
                       _('Numbers and special characters are not allowed.'))

PROCESS_CHOICES = (
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
    ('PT1', 'Passport talent 1°'),
    ('PT2', 'Passport talent 2°'),
    ('PT3', 'Passport talent 3°'),
    ('PT4', 'Passport talent 4°'),
    ('PT5', 'Passport talent 8°'),
    ('PT6', 'Passport talent 9°'),
    ('PTA', 'Passport talent – Autre'),
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

SOUS_PREFECTURE_CHOICES = (
    ('', '----'),
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

JURIDICTION_SPECIFIQUE_CHOICES = (
    ('', '----'),
    ('BER', "Berlin (Allemagne)"),
    ('FRA', "Francfort (Allemagne)"),
    ('BRA', "Brasilia (Brésil)"),
    ('RIO', "Rio de Janeiro (Brésil)"),
    ('SAO', "Sao Paulo (Brésil)"),
    ('MON', "Montréal (Canada)"),
    ('TOR', "Toronto (Canada)"),
    ('VAN', "Vancouver (Canada)"),
    ('PEK', "Pékin (Chine)"),
    ('SHA', "Shanghai (Chine)"),
    ('CAN', "Canton (Chine)"),
    ('WUH', "Wuhan (Chine)"),
    ('CHE', "Chengdu (Chine)"),
    ('SHE', "Shenyang (Chine)"),
    ('HON', "Hong Kong (Chine)"),
    ('ABO', "Abou Dhabi ( Emirats Arabes Unis)"),
    ('DUB', "Dubai (Emirats Arabes Unis)"),
    ('ATL', "Atlanta (USA)"),
    ('BOS', "Boston (USA)"),
    ('CHI', "Chicago (USA)"),
    ('HOU', "Houston (USA)"),
    ('LOS', "Los Angeles (USA)"),
    ('MIA', "Miami (USA)"),
    ('NY', "New York (USA)"),
    ('NOU', "Nouvelle Orléans (USA)"),
    ('SAN', "San Francisco (USA)"),
    ('WAS', "Washington, DC (USA)"),
    ('BAN', "Bangalore (Inde)"),
    ('BOM', "Bombay (Inde)"),
    ('KOL', "Kolkatta (Inde)"),
    ('PON', "Pondichery (Inde)"),
    ('NEW', "New Delhi (Inde)"),
    ('TEL', "Tel Aviv (Israel)"),
    ('JER', "Jérusalem (Israel)"),
    ('LAG', "Lagos (Nigéria) "),
    ('ABU', "Abuja (Nigéria)"),
    ('MOS', "Moscou (Russie)"),
    ('ST ', "St Petersbourg (Russie)"),
    ('IEK', "Iekaterinebourg (Russie)"),
    ('GEN', "Génève (Suisse)"),
    ('ZUR', "Zurich (Suisse)"),
    ('IST', "Istanboul (Turquie)"),
    ('ANK', "Ankara (Turquie)"),
)

CONSULAT_CHOICES = (
    ('', '----'),
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
    ('', '----'),
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

VISA_RP_CHOICES = (
    ('', '----'),
    ('VLS', 'VLS-TS'),
    ('CST', 'CST'),
    ('CSP', 'CSP'),
    ('APS', 'APS'),
)

FILE_STATE_ACTIVE  = 'A'
FILE_STATE_PENDING = 'P'
FILE_STATE_CLOSED  = 'C'

FILE_STATE_CHOICES = (
    (FILE_STATE_ACTIVE, _('Active')),
    (FILE_STATE_PENDING, _('Pending')),
    (FILE_STATE_CLOSED, _('Closed')),
)

class AccountCommon(models.Model):
    creation_date = models.DateTimeField(_('Creation date'), auto_now_add=True)
    first_name = models.CharField(_('First name'), max_length=50, default="", validators=[alpha])
    last_name = models.CharField(_('Last name'), max_length=50, default="", validators=[alpha])
    email = models.EmailField(_('Email'), max_length=50, null=True, blank=True, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                null=True, blank=True,
                                related_name='person_user_set')

    class Meta:
        abstract = True

    def __str__(self):
        if self.first_name != '' or self.last_name != '':
            return self.first_name + ' ' + self.last_name
        return ''

def check_dates(start, end, what):
    if start and end and end <= start:
        raise ValidationError(_("End date of %s cannot be earlier than start date"%(what)))

class PersonInfo(models.Model):
    foreigner_id = models.PositiveIntegerField(_('Foreigner ID'), blank=True,
                                               null=True)
    birth_date = models.DateField(_('Birth Date'), null=True)
    citizenship = CountryField(_('Citizenship'), blank=True, null=True)
    passport_expiry = models.DateField(_('Passport Expiry'), blank=True,
                                       null=True, default=None)
    passport_nationality = CountryField(_('Passport Nationality'), blank=True,
                                        null=True)
    home_entity = models.CharField(_('Home entity'), max_length=50,
                                   default='', blank=True)
    home_entity_address = models.TextField(_('Home Entity address'),
                                           max_length=100, default='',
                                           blank=True)
    host_entity = models.CharField(_('Host entity'), max_length=50,
                                   default='', blank=True)
    host_entity_address = models.TextField(_('Host Entity address'),
                                           max_length=100, default='',
                                           blank=True)

    spouse_first_name = models.CharField(_('Spouse First Name'),
                                         max_length=50, default='',
                                         blank=True, validators=[alpha])
    spouse_last_name = models.CharField(_('Spouse First Name'),
                                        max_length=50, default='',
                                        blank=True, validators=[alpha])
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
    prefecture = models.CharField('Préfecture / OFII compétent',
                                  max_length=3, default='',
                                  choices=PREFECTURE_CHOICES, blank=True)
    sous_prefecture = models.CharField('Sous-Préfecture',
                                       max_length=3, default='',
                                       choices=SOUS_PREFECTURE_CHOICES,
                                       blank=True)

    consulat = models.CharField('Préfecture / OFII compétent',
                                       max_length=3, default='',
                                       choices=CONSULAT_CHOICES, blank=True)
    direccte = models.CharField('Direccte compétente', max_length=3,
                                default='', choices=DIRECCTE_CHOICES,
                                blank=True)

    juridiction = models.CharField('Juridiction spécifique', max_length=3,
                                   default='',
                                   choices=JURIDICTION_SPECIFIQUE_CHOICES,
                                   blank=True)
    class Meta:
        abstract = True

    def validate_unique(self, exclude=None):
        super().validate_unique()
        if self.birth_date == None and Person.objects.exclude(id=self.id).filter(first_name=self.first_name, last_name=self.last_name, birth_date__isnull=True).exists():
            raise ValidationError(_("A person with this First Name, Last Name and Birth Date already exists."))

class Person(PersonInfo, AccountCommon):
    id = models.AutoField(primary_key=True)
    # prefecture OFII competent
    # consulat_competant
    # direccte_competente
    # sous-prefecture
    # juridiction specifique
    process = models.CharField(_('Process'), max_length=3, default='',
                               choices=PROCESS_CHOICES)
    responsible = models.ManyToManyField(User,
                                         verbose_name=_('Persons in charge'),
                                         blank=True,
                                         related_name='person_resp_set')
    modified_by = models.ForeignKey(User, verbose_name=_('Modified by'),
                                    on_delete=models.CASCADE,
                                    related_name='person_modified_by_set')
    start_date = models.DateField(_('Start Date'), blank=True, null=True)

    state = models.CharField(_('State'), max_length=3,
                             default=FILE_STATE_ACTIVE,
                             choices=FILE_STATE_CHOICES)
    comments = models.TextField(_('Comments'), max_length=100, default='',
                                blank=True)
    # transform empty to None (not sure to need that)
    #def clean_bar(self):
    #    return self.cleaned_data['birth_date'] or None

    class Meta:
        unique_together = ('first_name', 'last_name', 'birth_date')

    def validate_unique(self, exclude=None):
        super().validate_unique()
        if self.birth_date == None and Person.objects.exclude(id=self.id).filter(first_name=self.first_name, last_name=self.last_name, birth_date__isnull=True).exists():
            raise ValidationError(_('A person with this First Name, Last Name and Birth Date already exists.'))

class AuthorizationsCommon(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    enabled = models.BooleanField(default=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        abstract = True

    def clean(self, model_class=None):
        check_dates(self.start_date, self.end_date, self.label)
        return super().clean()

class VisaResidencePermitCommon(models.Model):
    type = models.CharField(max_length=3, default='', choices=VISA_RP_CHOICES)
    class Meta:
        abstract = True

class VisaResidencePermit(AuthorizationsCommon, VisaResidencePermitCommon):
    label = _('residence permit')

class ModerationVisaResidencePermit(AuthorizationsCommon,
                                    VisaResidencePermitCommon):
    pass

class SpouseVisaResidencePermit(AuthorizationsCommon,
                                VisaResidencePermitCommon):
    label = _("spouse's residence permit")

class ModerationSpouseVisaResidencePermit(AuthorizationsCommon,
                                          VisaResidencePermitCommon):
    pass

class WorkPermit(AuthorizationsCommon):
    label = _('work permit')

class ModerationWorkPermit(WorkPermit):
    pass

class SpouseWorkPermit(AuthorizationsCommon):
    label = _("spouse's work permit")

class ModerationSpouseWorkPermit(SpouseWorkPermit):
    pass

class ArchiveBox(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    number = models.PositiveIntegerField(_('Number'))

class ChildCommon(models.Model):
    first_name = models.CharField(max_length=50, null=False,
                                  validators=[alpha])
    last_name = models.CharField(max_length=50, default='', blank=True,
                                 validators=[alpha])
    birth_date = models.DateField(blank=True, null=True)
    passport_expiry = models.DateField(blank=True, null=True)
    passport_nationality = CountryField(blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    class Meta:
        abstract = True

class Child(ChildCommon):
    pass

class ModerationChild(ChildCommon):
    pass

class ProcessStage(models.Model):
    name_fr = models.CharField(_('French Name'), max_length=50, unique=True)
    name_en = models.CharField(_('English Name'), max_length=50, unique=True)

    def __str__(self):
        if translation.get_language() == 'fr':
            return self.name_fr
        else:
            return self.name_en

class Process(models.Model):
    name = models.CharField(max_length=50, validators=[alpha], unique=True)
    stages = models.ManyToManyField(ProcessStage, verbose_name=_('Stages'))

class PersonProcess(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    current_stage = models.ForeignKey(ProcessStage, on_delete=models.CASCADE)
