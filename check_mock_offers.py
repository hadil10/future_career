#!/usr/bin/env python
"""
Vérifier les offres mock dans la base de données
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.ai_models import ExternalJobOffer

def check_mock_offers():
    print("=== Vérification des offres mock ===")
    
    # Toutes les offres externes
    all_offers = ExternalJobOffer.objects.all()
    print(f"✓ Total offres externes: {all_offers.count()}")
    
    # Offres mock
    mock_offers = ExternalJobOffer.objects.filter(external_id__contains='mock')
    print(f"✓ Offres mock: {mock_offers.count()}")
    
    # Offres JSearch
    jsearch_offers = ExternalJobOffer.objects.filter(external_id__startswith='jsearch_')
    print(f"✓ Offres JSearch: {jsearch_offers.count()}")
    
    if mock_offers.exists():
        print(f"\n--- Offres mock trouvées ---")
        for offer in mock_offers[:5]:
            print(f"  - {offer.title} ({offer.external_id})")
    
    if jsearch_offers.exists():
        print(f"\n--- Offres JSearch trouvées ---")
        for offer in jsearch_offers[:5]:
            print(f"  - {offer.title} ({offer.external_id})")
    
    # Offres récentes
    recent_offers = ExternalJobOffer.objects.order_by('-created_at')[:10]
    print(f"\n--- 10 offres les plus récentes ---")
    for offer in recent_offers:
        is_mock = 'mock' in offer.external_id
        print(f"  - {offer.title} ({'MOCK' if is_mock else 'REAL'}) - {offer.created_at}")

if __name__ == "__main__":
    check_mock_offers()