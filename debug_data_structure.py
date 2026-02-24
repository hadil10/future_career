#!/usr/bin/env python
"""
Debug de la structure des données retournées
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.ai_services import ExternalJobSearchService
from profiles.models import Profile

def debug_data_structure():
    print("=== Debug structure des données ===")
    
    # Récupérer un profil
    profile = Profile.objects.filter(user__user_type='student').first()
    if not profile:
        print("❌ Aucun profil trouvé")
        return
    
    print(f"✓ Profil: {profile.user.username}")
    
    # Tester la recherche
    search_service = ExternalJobSearchService()
    results = search_service.search_jsearch_jobs(profile, "Paris", 3)
    
    print(f"✓ Nombre de résultats: {len(results)}")
    
    if results:
        print(f"\n--- Structure du premier résultat ---")
        first_result = results[0]
        print(f"Type: {type(first_result)}")
        print(f"Clés: {list(first_result.keys()) if isinstance(first_result, dict) else 'N/A'}")
        
        for key, value in first_result.items():
            print(f"  {key}: {type(value)} = {value}")
            
        print(f"\n--- Test d'accès aux propriétés ---")
        external_job = first_result.get('external_job')
        if external_job:
            print(f"external_job trouvé: {type(external_job)}")
            print(f"  - ID: {external_job.id}")
            print(f"  - external_id: {external_job.external_id}")
            print(f"  - title: {external_job.title}")
            print(f"  - company_name: {external_job.company_name}")
        else:
            print("❌ Pas d'external_job trouvé")

if __name__ == "__main__":
    debug_data_structure()