from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.db import models
from datetime import date
from django_countries.fields import CountryField

def check_dates(start, end, what):
    if start and end and end <= start:
        raise ValidationError(_("End date of %s cannot be earlier than start date"%(what)))

class Person(models.Model):
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
    # process?

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

class Process(models.Model):
    PROCESS_CHOICES = (
        ('OB', 'Obtention de docs/légalisation'),
        ('AP', 'Apprenti'),
        ('CA', 'Carte de résident'),
        ('CHS', 'Changement de statut'),
        ('CHE', "Changement d'employeur"),
        ('COUE', 'Conjoint UE'),
        ('COFR', 'Conjoint Fr'),
        ('CO', 'Consultation'),
        ('DC', 'DCEM/TIR'),
        ('DD', 'DDD UE'),
        ('ICT', 'Détaché ICT'),
        ('ICTM', 'Détaché ICT Mobile'),
        ('DI', 'Dispense AT – 3 mois'),
        ('NA', 'Nationalité'),
        ('SA', 'Salarié'),
        ('PT1', 'Passeport talent 1°'),
        ('PT2', 'Passeport talent 2°'),
        ('PT3', 'Passeport talent 3°'),
        ('PT4', 'Passeport talent 4°'),
        ('PT5', 'Passeport talent 8°'),
        ('PT6', 'Passeport talent 9°'),
        ('PT7', 'Passeport talent – Autre'),
        ('PS', 'PSI'),
        ('ST', 'Stagiaire'),
        ('STICT', 'Stagiaire ICT'),
        ('STICTM', 'Stagiaire ICT mobile'),
        ('UR', 'URSSAF/CPAM'),
        ('VI', 'Visiteur'),
        ('VISA', 'Visa'),
        ('AU', 'Autres'),
    )
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
