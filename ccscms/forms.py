from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.validators import RegexValidator
from .models import Account

class CustomUserCreationForm(UserCreationForm):
    firstname = forms.CharField(max_length=100, required=True)
    lastname = forms.CharField(max_length=100, required=True)
    contact_number = forms.CharField(
        max_length=20,
        required=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    account_type = forms.ChoiceField(
        choices=Account.ACCOUNT_TYPES,
        initial='user',
        widget=forms.RadioSelect
    )

    class Meta:
        model = Account
        fields = ('email', 'firstname', 'lastname', 'contact_number', 'account_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'placeholder': 'Email Address'})
        self.fields['firstname'].widget.attrs.update({'placeholder': 'First Name'})
        self.fields['lastname'].widget.attrs.update({'placeholder': 'Last Name'})
        self.fields['contact_number'].widget.attrs.update({'placeholder': 'Contact Number'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm Password'})

class AuthenticationForm(AuthenticationForm):
    username = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Email Address'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = "Invalid email or password. Please try again."