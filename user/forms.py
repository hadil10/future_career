from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

USER_TYPE_CHOICES = (
    ('student', 'Étudiant'),
    ('company', 'Entreprise'),
)

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Adresse e-mail",
        help_text="Nous utiliserons cette adresse pour vous contacter."
    )
    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect, 
        required=True,
        label="Type d'utilisateur",
        help_text="Choisissez votre profil : étudiant ou entreprise."
    )

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'password1', 'password2')
        labels = {
            'username': "Nom d'utilisateur",
        }
        help_texts = {
            'username': "Lettres, chiffres et @/./+/-/_ uniquement.",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type')
