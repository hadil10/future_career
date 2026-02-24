#!/usr/bin/env python
"""
Diagnostic de la recherche CV - Pourquoi aucun résultat ?
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

User = get_user_model()

def debug_search_results():
    """Diagnostiquer pourquoi la recherche ne retourne aucun résultat"""
    print("=== DIAGNOSTIC DE LA RECHERCHE CV ===\n")
    
    # Utiliser l'utilisateur admin qui a des données CV
    try:
        admin_user = User.objects.get(username='admin')
        profile = Profile.objects.get(user=admin_user)
        print(f"✅ Utilisateur: {admin_user.username}")
        
        search_service = ExternalJobSearchService()
        
        # 1. Vérifier l'API Key
        print(f"\n--- 1. Vérification de l'API Key ---")
        api_key = search_service.rapidapi_key
        if api_key:
            print(f"✅ API Key présente: {api_key[:10]}...{api_key[-5:]}")
        else:
            print("❌ Aucune API Key - Mode dégradé activé")
        
        # 2. Test de recherche JSearch directe
        print(f"\n--- 2. Test de recherche JSearch pour Tunis ---")
        try:
            jsearch_results = search_service.search_jsearch_jobs(profile, "Tunis", limit=10)
            print(f"✅ Résultats JSearch: {len(jsearch_results)} offres")
            
            if jsearch_results:
                for i, job in enumerate(jsearch_results[:3]):
                    print(f"   {i+1}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
                    print(f"      Score: {job.get('compatibility_score', 0)}%")
                    print(f"      URL: {job.get('url', 'N/A')}")
            else:
                print("❌ Aucun résultat JSearch")
                
        except Exception as e:
            print(f"❌ Erreur JSearch: {e}")
        
        # 3. Test de recherche CV complète
        print(f"\n--- 3. Test de recherche CV complète ---")
        try:
            cv_results = search_service.search_cv_based_jobs(profile, "Tunis", limit=10)
            all_sources = cv_results.get('all_sources', [])
            print(f"✅ Résultats CV complets: {len(all_sources)} offres")
            
            if all_sources:
                for i, job in enumerate(all_sources[:3]):
                    print(f"   {i+1}. {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
                    print(f"      Score: {job.get('compatibility_score', 0)}%")
            else:
                print("❌ Aucun résultat dans search_cv_based_jobs")
                
        except Exception as e:
            print(f"❌ Erreur recherche CV: {e}")
        
        # 4. Vérifier les offres internes
        print(f"\n--- 4. Vérification des offres internes ---")
        from companies.models import JobOffer
        internal_offers = JobOffer.objects.filter(is_active=True)
        print(f"✅ Offres internes actives: {internal_offers.count()}")
        
        if internal_offers.exists():
            for offer in internal_offers[:3]:
                compatibility = search_service._calculate_job_compatibility(
                    offer.description + " " + offer.title, profile
                )
                print(f"   - {offer.title} ({offer.company.name})")
                print(f"     Compatibilité: {compatibility:.1f}%")
                print(f"     Localisation: {offer.location or 'Non spécifiée'}")
        
        # 5. Test de requête intelligente
        print(f"\n--- 5. Test de construction de requête ---")
        try:
            query = search_service._build_intelligent_query(profile, "Tunis")
            print(f"✅ Requête construite: '{query}'")
            
            # Analyser les compétences utilisées
            cv_analysis = search_service._analyze_cv_data(profile)
            print(f"✅ Compétences CV: {len(cv_analysis.get('skills_from_cv', []))}")
            
            if cv_analysis.get('skills_from_cv'):
                skills_names = []
                for skill in cv_analysis['skills_from_cv'][:5]:
                    if isinstance(skill, dict):
                        skills_names.append(skill.get('skill', 'N/A'))
                    else:
                        skills_names.append(str(skill))
                print(f"   Compétences principales: {', '.join(skills_names)}")
            
        except Exception as e:
            print(f"❌ Erreur construction requête: {e}")
        
        # 6. Test API JSearch direct
        print(f"\n--- 6. Test API JSearch direct ---")
        if api_key:
            try:
                import requests
                
                url = "https://jsearch.p.rapidapi.com/search"
                querystring = {
                    "query": "développeur python Tunis",
                    "page": "1",
                    "num_pages": "1",
                    "country": "tn",  # Code pays pour Tunisie
                    "location": "Tunis",
                    "employment_types": "FULLTIME,PARTTIME",
                    "date_posted": "all"
                }
                
                headers = {
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
                }
                
                print(f"   Requête: {querystring}")
                response = requests.get(url, headers=headers, params=querystring, timeout=10)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    jobs = data.get('data', [])
                    print(f"✅ API JSearch: {len(jobs)} offres trouvées")
                    
                    if jobs:
                        for i, job in enumerate(jobs[:3]):
                            print(f"   {i+1}. {job.get('job_title', 'N/A')}")
                            print(f"      Entreprise: {job.get('employer_name', 'N/A')}")
                            print(f"      Ville: {job.get('job_city', 'N/A')}")
                            print(f"      URL: {job.get('job_apply_link', 'N/A')}")
                    else:
                        print("❌ API retourne 0 offres")
                        
                        # Essayer avec des paramètres différents
                        print("\n   Test avec paramètres alternatifs...")
                        querystring2 = {
                            "query": "emploi Tunis",
                            "page": "1",
                            "num_pages": "1",
                            "country": "tn",
                            "employment_types": "FULLTIME,PARTTIME"
                        }
                        
                        response2 = requests.get(url, headers=headers, params=querystring2, timeout=10)
                        if response2.status_code == 200:
                            data2 = response2.json()
                            jobs2 = data2.get('data', [])
                            print(f"   Résultats alternatifs: {len(jobs2)} offres")
                else:
                    print(f"❌ Erreur API: {response.status_code}")
                    print(f"   Réponse: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Erreur test API direct: {e}")
        
        # 7. Vérifier les offres externes en base
        print(f"\n--- 7. Vérification des offres externes en base ---")
        from profiles.ai_models import ExternalJobOffer
        external_offers = ExternalJobOffer.objects.all()
        print(f"✅ Offres externes en base: {external_offers.count()}")
        
        if external_offers.exists():
            tunis_offers = external_offers.filter(location__icontains='tunis')
            print(f"   Offres contenant 'Tunis': {tunis_offers.count()}")
            
            for offer in external_offers[:5]:
                print(f"   - {offer.title} ({offer.company_name})")
                print(f"     Localisation: {offer.location}")
                print(f"     Source: {offer.source}")
        
        print(f"\n=== DIAGNOSTIC FINAL ===")
        print("Causes possibles du problème:")
        print("1. API JSearch ne retourne pas d'offres pour Tunis")
        print("2. Timeout de l'API (15 secondes)")
        print("3. Paramètres de requête incorrects")
        print("4. Pas d'offres internes correspondantes")
        print("5. Seuil de compatibilité trop élevé")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")

if __name__ == "__main__":
    debug_search_results()