#!/usr/bin/env python
"""
Nettoyer les offres mock de la base de données
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.ai_models import ExternalJobOffer

def cleanup_mock_offers():
    print("=== Nettoyage des offres mock ===")
    
    # Trouver les offres mock
    mock_offers = ExternalJobOffer.objects.filter(external_id__contains='mock')
    count = mock_offers.count()
    
    print(f"✓ Offres mock trouvées: {count}")
    
    if count > 0:
        print(f"\n--- Suppression des offres mock ---")
        for offer in mock_offers:
            print(f"  - Suppression: {offer.title} ({offer.external_id})")
        
        # Supprimer les offres mock
        deleted_count = mock_offers.delete()[0]
        print(f"✓ {deleted_count} offres mock supprimées")
    else:
        print("✓ Aucune offre mock à supprimer")
    
    # Vérification finale
    remaining_mock = ExternalJobOffer.objects.filter(external_id__contains='mock').count()
    total_offers = ExternalJobOffer.objects.count()
    jsearch_offers = ExternalJobOffer.objects.filter(external_id__startswith='jsearch_').count()
    
    print(f"\n--- État final ---")
    print(f"✓ Total offres: {total_offers}")
    print(f"✓ Offres JSearch: {jsearch_offers}")
    print(f"✓ Offres mock restantes: {remaining_mock}")

if __name__ == "__main__":
    cleanup_mock_offers()