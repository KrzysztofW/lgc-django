from django.db import models
from lgc import models as lgc_models
from django.contrib.auth import get_user_model

User = get_user_model()

class Employee(lgc_models.PersonInfo):
    id = models.AutoField(primary_key=True)
    version = models.PositiveIntegerField(default=0)
    updated = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                null=True, blank=True,
                                related_name='employee_user_set')

class Child(lgc_models.ChildCommon):
    person = models.ForeignKey(Employee, on_delete=models.CASCADE)
    dcem_expiration = models.ForeignKey(lgc_models.Expiration,
                                        on_delete=models.SET_NULL,
                                        related_name='expiration',
                                        default=None, null=True)
    person_child = models.OneToOneField(lgc_models.Child, on_delete=models.CASCADE,
                                        related_name='employee_child_set',
                                        null=True)

class Expiration(lgc_models.ExpirationCommon):
    person = models.ForeignKey(Employee, on_delete=models.CASCADE)