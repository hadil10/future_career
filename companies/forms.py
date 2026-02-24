from django import forms
from .models import Company, JobOffer
from profiles.models import Skill

class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'description', 'website', 'industry', 'logo']
        labels = {
            'name': "Nom de l'entreprise",
            'description': "Description de l'entreprise",
            'website': "Site web",
            'industry': "Secteur d'activité",
            'logo': "Logo",
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
class JobOfferForm(forms.ModelForm):
    required_skills = forms.CharField(
        label="Compétences requises (séparées par des virgules)",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Ex: Python, Gestion de projet, SEO'}),
        help_text="Entrez les compétences nécessaires, séparées par une virgule."
    )
    
    class Meta:
        model = JobOffer
        # On exclut 'company' car on l'ajoutera manuellement dans la vue.
        fields = ['title', 'description', 'offer_type', 'location', 'is_active']
        labels = {
            'title': "Titre du poste",
            'description': "Description détaillée du poste",
            'offer_type': "Type de contrat",
            'location': "Lieu (Ville, Pays)",
            'is_active': "Rendre cette offre visible publiquement",
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        """
        Le constructeur standard et robuste pour un formulaire personnalisé.
        """
        request = kwargs.pop('request', None)
        super(JobOfferForm, self).__init__(*args, **kwargs)
