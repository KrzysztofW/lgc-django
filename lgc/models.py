from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.db import models
from datetime import date
from django_countries.fields import CountryField

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
    ('PT1', 'Passeport talent 1°'),
    ('PT2', 'Passeport talent 2°'),
    ('PT3', 'Passeport talent 3°'),
    ('PT4', 'Passeport talent 4°'),
    ('PT5', 'Passeport talent 8°'),
    ('PT6', 'Passeport talent 9°'),
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

def check_dates(start, end, what):
    if start and end and end <= start:
        raise ValidationError(_("End date of %s cannot be earlier than start date"%(what)))

class Person(models.Model):
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

    id = models.AutoField(primary_key=True)
    creation_date = models.DateTimeField(auto_now_add = True)
    first_name = models.CharField(max_length=50, default="")
    last_name = models.CharField(max_length=50, default="")
    email = models.EmailField(max_length=50, default="", blank=True)
    foreigner_id = models.PositiveIntegerField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    citizenship = CountryField(blank=True, null=True)
    passeport_expiry = models.DateField(blank=True, null=True, default=None)
    passeport_nationality = CountryField(blank=True, null=True)
    home_entity = models.CharField(max_length=50, default="", blank=True)
    home_entity_address = models.TextField(max_length=100, default="", blank=True)
    home_entity_country = CountryField(blank=True, null=True)
    host_entity = models.CharField(max_length=50, default="", blank=True)
    host_entity_address = models.TextField(max_length=100, default="", blank=True)
    host_entity_country = CountryField(blank=True, null=True)
    process = models.CharField(max_length=3, default="", choices=PROCESS_CHOICES)

    work_authorization = models.BooleanField(default=False)
    work_authorization_start = models.DateField(blank=True, null=True)
    work_authorization_end = models.DateField(blank=True, null=True)

    spouse_first_name = models.CharField(max_length=50, default="", blank=True)
    spouse_last_name = models.CharField(max_length=50, default="", blank=True)
    spouse_birth_date = models.DateField(blank=True, null=True)
    spouse_citizenship = CountryField(blank=True, null=True)
    spouse_passeport_expiry = models.DateField(blank=True, null=True, default=None)
    spouse_passeport_nationality = CountryField(blank=True, null=True)

    local_address = models.TextField(max_length=100, default="", blank=True)
    foreign_address = models.TextField(max_length=100, default="", blank=True)
    local_phone_number = models.TextField(max_length=100, default="", blank=True)
    foreign_phone_number = models.TextField(max_length=100, default="", blank=True)
    # prefecture OFII competent
    # consulat_competant
    # direccte_competente
    # sous-prefecture
    # juridiction specifique
    responsible = models.ManyToManyField(User, null=True, blank=True)
    start_date = models.DateField(blank=True, null=True)

    # state
    comments = models.TextField(max_length=100, default="", blank=True)

    email_sent_date = models.DateField(blank=True, null=True)
    data_storage_confirmed = models.BooleanField(default=False)

    def clean_bar(self):
        return self.cleaned_data['birth_date'] or None

    def clean(self):
        wa_start = self.work_authorization_start
        wa_end = self.work_authorization_end

        check_dates(wa_start, wa_end, _("work authorization"))
        return super(Person, self).clean()

    # treat Null birth dates as equal
    def validate_unique(self, exclude=None):
        super(Person, self).validate_unique(exclude)
        if self.birth_date == None and Person.objects.exclude(id=self.id).filter(first_name=self.first_name, last_name=self.last_name, birth_date__isnull=True).exists():
            # FR trans must be : Un object Person avec ces champs First name, Last name et Birth date existe déjà.
            raise ValidationError(_("A person with this First name, Last name and Birth date already exists."))

    class Meta:
        unique_together = ('first_name', 'last_name', 'birth_date')

class VisaResidencePermit(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)
    isSpouse = models.BooleanField(default=False)

    def clean(self):
        check_dates(self.start, self.end, _("residence permit"))
        return super(VisaResidencePermit, self).clean()

class ArchiveBox(models.Model):
    person = models.ManyToManyField(Person)
    number = models.PositiveIntegerField()

class AT(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def clean(self):
        check_dates(self.start, self.end, _("AT"))
        return super(AT, self).clean()

class Child(models.Model):
    parent = models.ForeignKey(Person, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default="", blank=True)
    last_name = models.CharField(max_length=50, default="", blank=True)
    birth_date = models.DateField(blank=True, null=True)
    passeport_expiry = models.DateField(blank=True, null=True)
    passeport_nationality = CountryField(blank=True, null=True)

class ProcessType(models.Model):
    persons = models.ManyToManyField(Person)
    #id = models.AutoField(primary_key=True)
    # ondelete => set to none
    #name = models.CharField(max_length=6, default="", choices=PROCESS_CHOICES,
    #unique=True)
    name = models.CharField(max_length=50, default="", unique=True)

    #generic_name = models.BooleanField(default=True)

class Moderation(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE,
                                  primary_key=True)
