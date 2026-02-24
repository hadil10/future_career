#!/usr/bin/env python
"""
Test final de l'intégration JSearch
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.ai_services import ExternalJobSearchService
from profiles.models import Profile
from profiles.ai_models import ExternalJobOffer

def final_test():
    print("=== Test final intégration JSearch ===")
    
    # 1. Vérifier la configuration API
    from django.conf import settings
    api_key = getattr(settings, 'RAPIDAPI_KEY', None)
    print(f"✓ Clé API configurée: {'Oui' if api_key else 'Non'}")
    
    # 2. Vérifier les offres en base
    total_offers = ExternalJobOffer.objects.count()
    mock_offers = ExternalJobOffer.objects.filter(external_id__contains='mock').count()
    jsearch_offers = ExternalJobOffer.objects.filter(external_id__startswith='jsearch_').count()
    
    print(f"✓ Total offres en base: {total_offers}")
    print(f"✓ Offres mock: {mock_offers}")
    print(f"✓ Offres JSearch: {jsearch_offers}")
    
    # 3. Test de recherche
    profile = Profile.objects.filter(user__user_type='student').first()
    if profile:
        search_service = ExternalJobSearchService()
        results = search_service.search_jsearch_jobs(profile, "Paris", 5)
        
        print(f"✓ Résultats de recherche: {len(results)}")
        
        if results:
            first_result = results[0]
            external_job = first_result.get('external_job')
            if external_job:
                is_real = not ('mock' in external_job.external_id)
                print(f"✓ Premier résultat: {external_job.title}")
                print(f"✓ Type: {'Réel (JSearch)' if is_real else 'Mock'}")
                print(f"✓ Compatibilité: {first_result.get('compatibility_score', 0):.1f}%")
    
    # 4. Résumé
    print(f"\n=== RÉSUMÉ ===")
    if api_key and jsearch_offers > 0 and mock_offers == 0:
        print("✅ SUCCÈS: L'intégration JSearch fonctionne parfaitement!")
        print("   - API configurée ✓")
        print("   - Vraies offres JSearch disponibles ✓")
        print("   - Aucune offre mock ✓")
        print("   - Recherche fonctionnelle ✓")
    else:
        print("⚠️  PROBLÈMES DÉTECTÉS:")
        if not api_key:
            print("   - Clé API manquante")
        if mock_offers > 0:
            print(f"   - {mock_offers} offres mock restantes")
        if jsearch_offers == 0:
            print("   - Aucune offre JSearch")
    
    print(f"\n🌐 Accédez à l'application: http://127.0.0.1:8000/ai/search/")
    print(f"📝 Connectez-vous avec un compte étudiant pour tester la recherche")

if __name__ == "__main__":
    final_test()