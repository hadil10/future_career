#!/usr/bin/env python
"""
Debug du mode démonstration
"""
import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.models import Profile
from profiles.ai_services import ExternalJobSearchService

def debug_demo_mode():
    print("=== Debug mode démonstration ===")
    
    # Récupérer un utilisateur étudiant
    User = get_user_model()
    student_user = User.objects.filter(user_type='student').first()
    profile = Profile.objects.get(user=student_user)
    
    # Tester la recherche directement
    search_service = ExternalJobSearchService()
    external_jobs = search_service.search_jsearch_jobs(profile, "Paris", 5)
    
    print(f"✓ Nombre d'offres externes: {len(external_jobs)}")
    
    # Vérifier chaque offre
    demo_mode = False
    for i, job in enumerate(external_jobs):
        external_job = job.get('external_job')
        if external_job:
            has_mock = 'mock' in external_job.external_id
            print(f"  {i+1}. {external_job.title}")
            print(f"     external_id: {external_job.external_id}")
            print(f"     contains 'mock': {has_mock}")
            
            if has_mock:
                demo_mode = True
    
    print(f"\n✓ Mode démo détecté: {demo_mode}")
    
    # Tester la logique de la vue
    print(f"\n--- Test logique de la vue ---")
    if external_jobs:
        for job in external_jobs:
            external_job = job.get('external_job')
            if external_job and hasattr(external_job, 'external_id') and 'mock' in external_job.external_id:
                print(f"❌ Offre mock trouvée: {external_job.external_id}")
                demo_mode = True
                break
        else:
            print(f"✓ Aucune offre mock trouvée")
            demo_mode = False
    
    print(f"✓ Résultat final demo_mode: {demo_mode}")

if __name__ == "__main__":
    debug_demo_mode()