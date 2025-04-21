from django import forms
#from xrechnung_light.models import LogMessage, PostalAddress, CustomerParty
from django.forms.models import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Order, OrderLine

class RegistrationForm(UserCreationForm):

    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class PredefinedOrderLineForm(forms.Form):

    #https://stackoverflow.com/questions/66772595/django-form-widget-how-can-i-set-max-value-to-a-value-on-the-database-for-each
    #

    #def __init__(self, *args, **kwargs):
    #    super().__init__(*args, **kwargs)
    #    self.max_amount = kwargs.pop('max_amount', 10) #getting kwargs

    #max_amount = 10
    amount = forms.IntegerField(label="Anzahl", min_value=0)



class OrderLineForm(forms.ModelForm):
    class Meta:
        model = OrderLine
        fields = (
            "package",
            "amount"
        )

OrderLineFormSet = inlineformset_factory(
    Order,
    OrderLine,
    form=OrderLineForm,
    can_delete=True,
    min_num=2,
    extra=0
)