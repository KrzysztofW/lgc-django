from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

alpha = RegexValidator(r'^[^0-9`;:_{}()$^~"\%&*#!?.,\\<>|@/]*$',
                                 _('Numbers and special characters are not allowed.'))
alphanum = RegexValidator(r'^[^`;:_{}()$^~"\%&*#!?.,\\<>|@/]*$',
                                    _('Special characters are not allowed.'))
siret = RegexValidator(r'^[0-9]{14}$')
