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

class HR(models.Model):
    first_name = models.CharField(max_length=50, default="", blank=True)
    last_name = models.CharField(max_length=50, default="", blank=True)
    email = models.EmailField(max_length=50, default="", blank=True)
    societe = models.CharField(max_length=50, default="", blank=True)
    is_admin = models.BooleanField(default=False)
    GDPR_accepted_date = models.DateField(blank=True, null=True)
    GDPR_refused_date = models.DateField(blank=True, null=True)
    email_sent = models.DateField(blank=True, null=True)
    disabled = models.BooleanField(default=False)

class CommonPersonInfo(models.Model):
    creation_date = models.DateTimeField(auto_now_add = True)
    first_name = models.CharField(max_length=50, default="")
    last_name = models.CharField(max_length=50, default="")
    email = models.EmailField(max_length=50, default="", blank=True)
    foreigner_id = models.PositiveIntegerField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    citizenship = CountryField(blank=True, null=True)
    passport_expiry = models.DateField(blank=True, null=True, default=None)
    passport_nationality = CountryField(blank=True, null=True)
    home_entity = models.CharField(max_length=50, default="", blank=True)
    home_entity_address = models.TextField(max_length=100, default="", blank=True)
    home_entity_country = CountryField(blank=True, null=True)
    host_entity = models.CharField(max_length=50, default="", blank=True)
    host_entity_address = models.TextField(max_length=100, default="", blank=True)
    host_entity_country = CountryField(blank=True, null=True)

    work_authorization = models.BooleanField(default=False)
    work_authorization_start = models.DateField(blank=True, null=True)
    work_authorization_end = models.DateField(blank=True, null=True)

    spouse_first_name = models.CharField(max_length=50, default="", blank=True)
    spouse_last_name = models.CharField(max_length=50, default="", blank=True)
    spouse_birth_date = models.DateField(blank=True, null=True)
    spouse_citizenship = CountryField(blank=True, null=True)
    spouse_passport_expiry = models.DateField(blank=True, null=True, default=None)
    spouse_passport_nationality = CountryField(blank=True, null=True)

    local_address = models.TextField(max_length=100, default="", blank=True)
    foreign_address = models.TextField(max_length=100, default="", blank=True)
    local_phone_number = models.TextField(max_length=100, default="", blank=True)
    foreign_phone_number = models.TextField(max_length=100, default="", blank=True)

    class Meta:
        unique_together = ('first_name', 'last_name', 'birth_date')
        abstract = True

    def clean_bar(self):
        return self.cleaned_data['birth_date'] or None

    def clean(self):
        wa_start = self.work_authorization_start
        wa_end = self.work_authorization_end

        check_dates(wa_start, wa_end, _("work authorization"))
        return super().clean()

    def validate_unique(self, child_obj):
        super().validate_unique(exclude=None)
        if self.birth_date == None and child_obj.objects.exclude(id=self.id).filter(first_name=self.first_name, last_name=self.last_name, birth_date__isnull=True).exists():
            raise ValidationError(_("A person with this First name, Last name and Birth date already exists."))

class Employee(CommonPersonInfo):
    HR = models.ManyToManyField(HR, blank=True)
    societe = models.CharField(max_length=50, default="", blank=True)
    GDPR_accepted_date = models.DateField(blank=True, null=True)
    GDPR_refused_date = models.DateField(blank=True, null=True)
    email_sent = models.DateField(blank=True, null=True)
    disabled = models.BooleanField(default=False)

    # treat Null birth dates as equal
    def validate_unique(self, exclude=None):
        super().validate_unique(Employee)

def check_dates(start, end, what):
    if start and end and end <= start:
        raise ValidationError(_("End date of %s cannot be earlier than start date"%(what)))

class Person(CommonPersonInfo):
    #id = models.AutoField(primary_key=True)
    # XXX the file should normally be deleted if the employee is deleted
    employee = models.OneToOneField(Employee, on_delete=models.SET_NULL,
                                    null=True, default=None, blank=True)
    # prefecture OFII competent
    # consulat_competant
    # direccte_competente
    # sous-prefecture
    # juridiction specifique
    process = models.CharField(max_length=3, default="", choices=PROCESS_CHOICES)
    responsible = models.ManyToManyField(User, blank=True)
    start_date = models.DateField(blank=True, null=True)

    # state
    comments = models.TextField(max_length=100, default="", blank=True)

    def validate_unique(self, exclude=None):
        super().validate_unique(Person)

class VisaResidencePermitCommon(models.Model):
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)
    isSpouse = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def clean(self, model_class=None):
        check_dates(self.start, self.end, _("residence permit"))
        return super(model_class, self).clean()

class VisaResidencePermit(VisaResidencePermitCommon):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def clean(self):
        return super(self, model_class=VisaResidencePermit).clean()

class EmployeeVisaResidencePermit(VisaResidencePermitCommon):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def clean(self):
        return super(self, model_class=EmployeeVisaResidencePermit).clean()

class ArchiveBox(models.Model):
    person = models.ManyToManyField(Person)
    number = models.PositiveIntegerField()

class WorkPermit(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)

    def clean(self):
        check_dates(self.start, self.end, _("WP"))
        return super(WorkPermit, self).clean()

class ChildCommon(models.Model):
    first_name = models.CharField(max_length=50, default="", blank=True)
    last_name = models.CharField(max_length=50, default="", blank=True)
    birth_date = models.DateField(blank=True, null=True)
    passport_expiry = models.DateField(blank=True, null=True)
    passport_nationality = CountryField(blank=True, null=True)

    class Meta:
        abstract = True

class Child(ChildCommon):
    parent = models.ForeignKey(Person, on_delete=models.CASCADE)

class EmployeeChild(ChildCommon):
    parent = models.ForeignKey(Employee, on_delete=models.CASCADE)

#class Process(models.Model):
#    person = models.ForeignKey(Person, on_delete=models.CASCADE)
#    name = models.CharField(max_length=3, default="", choices=PROCESS_CHOICES)

#class ProcessStage(models.Model):
#    name = models.CharField(max_length=50, default="", unique=True)
#
class ProcessType(models.Model):
    persons = models.ManyToManyField(Person)
    #stages = models.ManyToManyField(Stage)
    # ondelete => not allowed if used
    name = models.CharField(max_length=50, default="", unique=True)
