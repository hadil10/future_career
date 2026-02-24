#!/usr/bin/env python
"""
Diagnostic du modal IA - Pourquoi affiche-t-il toujours les mêmes résultats ?
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from profiles.models import Profile
from profiles.ai_services import ExternalJobSearchService
from companies.models import JobOffer
import json

User = get_user_model()

def debug_ai_modal_search():
    """Diagnostiquer le modal IA"""
    print("=== DIAGNOSTIC MODAL IA ===\n")
    
    try:
        # Utiliser l'utilisateur admin
        admin_user = User.objects.get(username='admin')
        profile = Profile.objects.get(user=admin_user)
        print(f"✅ Utilisateur: {admin_user.username}")
        
        search_service = ExternalJobSearchService()
        
        # Simuler exactement ce que fait ai_instant_recommendations_view
        print("\n--- 1. Test avec Paris ---")
        location = "Paris"
        search_external = True
        limit = 10
        
        results = {
            'internal_jobs': [],
            'external_jobs': [],
            'total_count': 0,
            'search_time': 0
        }
        
        import time
        start_time = time.time()
        
        # Recherche interne
        print("Recherche interne...")
        internal_offers = JobOffer.objects.filter(is_active=True)[:limit]
        print(f"Offres internes trouvées: {internal_offers.count()}")
        
        for offer in internal_offers:
            compatibility = search_service._calculate_job_compatibility(
                offer.description + " " + offer.title, profile
            )
            print(f"  - {offer.title}: {compatibility:.1f}% compatibilité")
            if compatibility > 20:
                results['internal_jobs'].append({
                    'id': offer.id,
                    'title': offer.title,
                    'company': offer.company.name,
                    'location': offer.location or 'Non spécifié',
                    'compatibility_score': round(compatibility),
                    'is_internal': True
                })
        
        print(f"Offres internes compatibles: {len(results['internal_jobs'])}")
        
        # Recherche externe
        if search_external:
            print(f"\nRecherche externe pour {location}...")
            try:
                external_results = search_service.search_jsearch_jobs(profile, location, limit=limit)
                print(f"Offres externes trouvées: {len(external_results)}")
                
                for i, job in enumerate(external_results[:5]):
                    if job and job.get('external_job'):
                        external_job = job['external_job']
                        print(f"  {i+1}. {external_job.title} - {external_job.company_name}")
                        print(f"     Localisation: {external_job.location}")
                        print(f"     Compatibilité: {job['compatibility_score']:.1f}%")
                        print(f"     URL: {external_job.external_url[:60]}...")
                        
                        results['external_jobs'].append({
                            'id': external_job.id,
                            'title': job['title'],
                            'company': job['company'],
                            'location': job['location'] or 'Non spécifié',
                            'compatibility_score': round(job['compatibility_score']),
                            'url': job['url'],
                            'is_internal': False
                        })
                        
            except Exception as e:
                print(f"❌ Erreur recherche externe: {e}")
        
        # Trier tous les résultats par score
        all_jobs = results['internal_jobs'] + results['external_jobs']
        all_jobs.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        results['all_jobs'] = all_jobs[:limit]
        results['total_count'] = len(all_jobs)
        results['search_time'] = round(time.time() - start_time, 2)
        
        print(f"\n--- Résultats pour Paris ---")
        print(f"Total: {results['total_count']} offres")
        print(f"Internes: {len(results['internal_jobs'])}")
        print(f"Externes: {len(results['external_jobs'])}")
        
        # Test avec une autre ville
        print(f"\n--- 2. Test avec Lyon ---")
        location2 = "Lyon"
        
        try:
            external_results2 = search_service.search_jsearch_jobs(profile, location2, limit=5)
            print(f"Offres externes pour Lyon: {len(external_results2)}")
            
            for i, job in enumerate(external_results2[:3]):
                if job and job.get('external_job'):
                    external_job = job['external_job']
                    print(f"  {i+1}. {external_job.title} - {external_job.company_name}")
                    print(f"     Localisation: {external_job.location}")
                    
        except Exception as e:
            print(f"❌ Erreur recherche Lyon: {e}")
        
        # Test avec Tunis
        print(f"\n--- 3. Test avec Tunis ---")
        location3 = "Tunis"
        
        try:
            external_results3 = search_service.search_jsearch_jobs(profile, location3, limit=5)
            print(f"Offres externes pour Tunis: {len(external_results3)}")
            
            for i, job in enumerate(external_results3[:3]):
                if job and job.get('external_job'):
                    external_job = job['external_job']
                    print(f"  {i+1}. {external_job.title} - {external_job.company_name}")
                    print(f"     Localisation: {external_job.location}")
                    
        except Exception as e:
            print(f"❌ Erreur recherche Tunis: {e}")
        
        # Vérifier la méthode _get_cached_real_jobs
        print(f"\n--- 4. Test de _get_cached_real_jobs ---")
        
        print("Test avec Paris:")
        cached_paris = search_service._get_cached_real_jobs(profile, "Paris", 5)
        print(f"Offres cachées Paris: {len(cached_paris)}")
        for job in cached_paris[:3]:
            print(f"  - {job['title']} ({job['location']})")
        
        print("\nTest avec Lyon:")
        cached_lyon = search_service._get_cached_real_jobs(profile, "Lyon", 5)
        print(f"Offres cachées Lyon: {len(cached_lyon)}")
        for job in cached_lyon[:3]:
            print(f"  - {job['title']} ({job['location']})")
        
        print("\nTest avec Tunis:")
        cached_tunis = search_service._get_cached_real_jobs(profile, "Tunis", 5)
        print(f"Offres cachées Tunis: {len(cached_tunis)}")
        for job in cached_tunis[:3]:
            print(f"  - {job['title']} ({job['location']})")
        
        # Vérifier les offres en base par localisation
        print(f"\n--- 5. Vérification base de données par localisation ---")
        from profiles.ai_models import ExternalJobOffer
        
        paris_offers = ExternalJobOffer.objects.filter(location__icontains='paris').count()
        lyon_offers = ExternalJobOffer.objects.filter(location__icontains='lyon').count()
        tunis_offers = ExternalJobOffer.objects.filter(location__icontains='tunis').count()
        
        print(f"Offres Paris en base: {paris_offers}")
        print(f"Offres Lyon en base: {lyon_offers}")
        print(f"Offres Tunis en base: {tunis_offers}")
        
        print(f"\n=== DIAGNOSTIC FINAL ===")
        print("Problèmes potentiels:")
        print("1. API JSearch en limite de taux (429)")
        print("2. Méthode _get_cached_real_jobs ne filtre pas correctement par localisation")
        print("3. Modal IA utilise toujours les mêmes offres internes")
        print("4. Pas assez d'offres en base pour certaines localisations")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ai_modal_search()