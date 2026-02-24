from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import Company

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_company_profile(sender, instance, created, **kwargs):
    """
    Crée un CompanyProfile automatiquement pour chaque nouvel utilisateur
    de type 'company'.
    """
    if created and instance.user_type == 'company':
        Company.objects.create(user=instance, name=f"Profil de {instance.username}")
