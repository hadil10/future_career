#!/usr/bin/env python
"""
Nettoyer toutes les offres externes pour forcer une nouvelle recherche
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.ai_models import ExternalJobOffer

def cleanup_all_external_offers():
    print("=== Nettoyage de toutes les offres externes ===")
    
    # Compter les offres
    total_offers = ExternalJobOffer.objects.count()
    print(f"✓ Offres externes à supprimer: {total_offers}")
    
    if total_offers > 0:
        # Supprimer toutes les offres externes
        ExternalJobOffer.objects.all().delete()
        print(f"✓ {total_offers} offres externes supprimées")
    else:
        print("✓ Aucune offre externe à supprimer")
    
    # Vérification finale
    remaining_offers = ExternalJobOffer.objects.count()
    print(f"✓ Offres restantes: {remaining_offers}")
    
    print("\n🔄 Les prochaines recherches utiliseront de nouvelles données JSearch")

if __name__ == "__main__":
    cleanup_all_external_offers()