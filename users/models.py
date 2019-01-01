from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                primary_key=True)
    JURISTE =    'JU'
    CONSULTANT = 'CO'
    ROLE_CHOICES = (
        (JURISTE,    'Juriste'),
        (CONSULTANT, 'Consultant'),
    )
    role = models.CharField(max_length=2, choices=ROLE_CHOICES,
                            default=JURISTE)
    billing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username, "role:", self.role, "billing:", str(self.billing)

    def save(self, force_insert=False, *args, **kwargs):
        super().save()
