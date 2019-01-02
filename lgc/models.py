from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.db import models
from datetime import date
from .countries import Countries

def check_dates(start, end, what):
    if start and end and end <= start:
        raise forms.ValidationError(_("End time of %s cannot be earlier than start time"%(what)))

class Person(models.Model):
    id = models.AutoField(primary_key=True)
    creation_date = models.DateTimeField(auto_now_add = True)
    countries = Countries
    first_name = models.CharField(max_length=50, default="")
    last_name = models.CharField(max_length=50, default="")
    email = models.EmailField(max_length=50, default="", blank=True)
    foreigner_id = models.PositiveIntegerField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    citizenship = models.CharField(max_length=40,
                                   choices=countries.COUNTRY_CHOICES,
                                   default="", blank=True)
    passeport_expiry = models.DateField(blank=True, null=True, default=None)
    passeport_nationality = models.CharField(max_length=40,
                                             choices=countries.COUNTRY_CHOICES,
                                             default="", blank=True)
    home_entity = models.CharField(max_length=50, default="", blank=True)
    home_entity_addr = models.TextField(max_length=100, default="", blank=True)

    host_entity = models.CharField(max_length=50, default="", blank=True)
    host_entity_addr = models.TextField(max_length=100, default="", blank=True)
    work_authorization = models.BooleanField(default=False, blank=True)
    work_authorization_start = models.DateField(blank=True, null=True)
    work_authorization_end = models.DateField(blank=True, null=True)

    residence_permit_start = models.DateField(blank=True, null=True)
    residence_permit_end = models.DateField(blank=True, null=True)

    def clean_bar(self):
        return self.cleaned_data['birth_date'] or None

    def clean(self):
        cleaned_data = super(Person, self).clean()
        if not cleaned_data:
            return cleaned_data
        wa_start = cleaned_data.get("work_authorization_start")
        wa_end = cleaned_data.get("work_authorization_end")
        rp_start = cleaned_data.get("residence_permit_start")
        rp_end = cleaned_data.get("residence_permit_end")

        check_dates(wa_start, wa_end, _("work authorization"))
        check_dates(rp_start, rp_end, _("residence permit"))
        return cleaned_data

    # treat Null birth dates as equal
    def validate_unique(self, exclude=None):
        super(Person, self).validate_unique(exclude)
        if self.birth_date == None and Person.objects.exclude(id=self.id).filter(first_name=self.first_name, last_name=self.last_name, birth_date__isnull=True).exists():
            # FR trans must be : Un object Person avec ces champs First name, Last name et Birth date existe déjà.
            raise ValidationError(_("Person with this First name, Last name and Birth date already exists."))

    class Meta:
        unique_together = ('first_name', 'last_name', 'birth_date')

class Child(models.Model):
    countries = Countries
    parent = models.ForeignKey(Person, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, default="", blank=True)
    last_name = models.CharField(max_length=50, default="", blank=True)
    birth_date = models.DateField(blank=True, null=True)
    passeport_expiry = models.DateField(blank=True, null=True)
    passeport_nationality = models.CharField(max_length=40,
                                             choices=countries.COUNTRY_CHOICES,
                                             default="", blank=True)
    def clean(self):
        cleaned_data = super(Child, self).clean()
        start = cleaned_data.get("_start")
        end = cleaned_data.get("_end")

        check_dates(start, end, _(""))
        return cleaned_data

class Process(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, default="", unique=True)
    generic = models.BooleanField(default=False)
    persons = models.ManyToManyField(Person)
