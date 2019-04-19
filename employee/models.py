from django.db import models
from lgc import models as lgc_models
from django.contrib.auth import get_user_model

User = get_user_model()

class Employee(lgc_models.PersonInfo):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                null=True, blank=True,
                                related_name='employee_user_set')
    updated = models.BooleanField(default=False)

class Child(lgc_models.ChildCommon):
    person = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pass

class Expiration(lgc_models.ExpirationCommon):
    person = models.ForeignKey(Employee, on_delete=models.CASCADE)
    pass
