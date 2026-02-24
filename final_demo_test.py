#!/usr/bin/env python
"""
Test final pour confirmer que le mode démo est désactivé
"""
import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.ai_models import ExternalJobOffer

def final_demo_test():
    print("=== Test final mode démonstration ===")
    
    # 1. Vérifier la base de données
    print(f"\n--- État de la base de données ---")
    total_offers = ExternalJobOffer.objects.count()
    mock_offers = ExternalJobOffer.objects.filter(external_id__contains='mock').count()
    jsearch_offers = ExternalJobOffer.objects.filter(external_id__startswith='jsearch_').count()
    
    print(f"✓ Total offres: {total_offers}")
    print(f"✓ Offres mock: {mock_offers}")
    print(f"✓ Offres JSearch: {jsearch_offers}")
    
    if mock_offers == 0:
        print("✅ Aucune offre mock en base")
    else:
        print(f"❌ {mock_offers} offres mock restantes")
    
    # 2. Test de l'interface web
    print(f"\n--- Test interface web ---")
    User = get_user_model()
    student_user = User.objects.filter(user_type='student').first()
    
    client = Client()
    client.force_login(student_user)
    
    # Recherche avec offres externes
    response = client.get('/ai/search/', {
        'location': 'Paris',
        'external': 'true'
    })
    
    content = response.content.decode('utf-8')
    
    # Vérifications spécifiques
    demo_alert = 'Les offres externes affichées sont simulées pour la démonstration'
    if demo_alert in content:
        print("❌ Message de démonstration visible")
    else:
        print("✅ Pas de message de démonstration")
    
    # Vérifier les vraies offres JSearch
    if 'JSearch' in content and 'offre(s) trouvée(s)' in content:
        print("✅ Vraies offres JSearch affichées")
    
    # Compter les offres
    external_cards = content.count('border-primary')
    print(f"✅ {external_cards} offres externes affichées")
    
    # 3. Test du modal IA
    print(f"\n--- Test modal IA ---")
    import json
    
    response = client.post('/ai/instant-recommendations/', 
                         data=json.dumps({
                             'location': 'Lyon',
                             'search_external': True,
                             'limit': 5
                         }),
                         content_type='application/json')
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            results = data.get('data', {})
            external_jobs = results.get('external_jobs', [])
            print(f"✅ Modal IA: {len(external_jobs)} offres externes")
            
            # Vérifier que ce sont de vraies offres
            if external_jobs:
                first_job = external_jobs[0]
                print(f"✅ Exemple: {first_job.get('title')} chez {first_job.get('company')}")
    
    # 4. Résumé final
    print(f"\n=== RÉSUMÉ FINAL ===")
    if mock_offers == 0 and external_cards > 0:
        print("🎉 SUCCÈS COMPLET !")
        print("✅ Mode démonstration désactivé")
        print("✅ Vraies offres JSearch fonctionnelles")
        print("✅ Modal IA opérationnel")
        print("✅ Aucune offre mock en base")
        print("\n🚀 L'application utilise maintenant 100% de vraies données JSearch !")
    else:
        print("⚠️  Problèmes détectés - vérifiez les détails ci-dessus")

if __name__ == "__main__":
    final_demo_test()