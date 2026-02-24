#!/usr/bin/env python
"""
Débogage du problème de recherche qui n'affiche aucune offre
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
from profiles.ai_models import ExternalJobOffer

User = get_user_model()

def debug_search_issue():
    """Débogage du problème de recherche"""
    print("=== Débogage du problème de recherche ===\n")
    
    # Trouver un utilisateur étudiant
    student_user = User.objects.filter(user_type='student').first()
    if not student_user:
        print("❌ Aucun utilisateur étudiant trouvé")
        return
    
    profile = Profile.objects.get(user=student_user)
    print(f"✅ Utilisateur: {student_user.username}")
    
    # Vérifier les compétences du profil
    skills = profile.skill_evaluations.all()
    print(f"📊 Compétences du profil: {skills.count()}")
    for skill in skills:
        print(f"   - {skill.skill.name}: {skill.level}/5")
    
    # Vérifier la clé API
    from django.conf import settings
    rapidapi_key = getattr(settings, 'RAPIDAPI_KEY', None)
    print(f"\n🔑 Clé API: {'✅ Configurée' if rapidapi_key else '❌ Manquante'}")
    
    # Test du service de recherche
    search_service = ExternalJobSearchService()
    
    print("\n--- Test 1: Recherche JSearch directe ---")
    try:
        results = search_service.search_jsearch_jobs(profile, "Paris", limit=5)
        print(f"Résultats JSearch: {len(results)}")
        
        for i, job in enumerate(results[:3]):
            external_job = job.get('external_job')
            if external_job:
                print(f"  {i+1}. {external_job.title}")
                print(f"     Entreprise: {external_job.company_name}")
                print(f"     Compatibilité: {job.get('compatibility_score', 0):.0f}%")
    except Exception as e:
        print(f"❌ Erreur JSearch: {e}")
    
    print("\n--- Test 2: Recherche CV complète ---")
    try:
        cv_results = search_service.search_cv_based_jobs(profile, "Paris", limit=5)
        all_sources = cv_results.get('all_sources', [])
        print(f"Résultats CV: {len(all_sources)}")
        
        if all_sources:
            for i, job in enumerate(all_sources[:3]):
                external_job = job.get('external_job')
                if external_job:
                    print(f"  {i+1}. {external_job.title}")
                    print(f"     Compatibilité: {job.get('compatibility_score', 0):.0f}%")
        else:
            print("❌ Aucun résultat dans search_cv_based_jobs")
            
    except Exception as e:
        print(f"❌ Erreur recherche CV: {e}")
    
    print("\n--- Test 3: Vérification des offres en base ---")
    try:
        external_offers = ExternalJobOffer.objects.all()
        print(f"Offres externes en base: {external_offers.count()}")
        
        for offer in external_offers[:3]:
            print(f"  - {offer.title} ({offer.company_name})")
            print(f"    Source: {offer.source}, Actif: {offer.is_active}")
            
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
    
    print("\n--- Test 4: Test de compatibilité ---")
    try:
        # Créer une offre de test
        test_job_text = "Développeur Python Django React JavaScript SQL"
        compatibility = search_service._calculate_job_compatibility(test_job_text, profile)
        print(f"Score de compatibilité test: {compatibility:.0f}%")
        
        if compatibility == 0:
            print("❌ Problème: Score de compatibilité = 0")
            print("   Vérifiez que le profil a des compétences")
        
    except Exception as e:
        print(f"❌ Erreur calcul compatibilité: {e}")
    
    print("\n--- Test 5: Test API JSearch direct ---")
    try:
        import requests
        
        if rapidapi_key:
            url = "https://jsearch.p.rapidapi.com/search"
            querystring = {
                "query": "développeur python Paris",
                "page": "1",
                "num_pages": "1",
                "country": "fr",
                "location": "Paris"
            }
            
            headers = {
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
            }
            
            response = requests.get(url, headers=headers, params=querystring, timeout=10)
            print(f"Status API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                print(f"Offres API directe: {len(jobs)}")
                
                for i, job in enumerate(jobs[:2]):
                    print(f"  {i+1}. {job.get('job_title', 'N/A')}")
                    print(f"     Entreprise: {job.get('employer_name', 'N/A')}")
            else:
                print(f"❌ Erreur API: {response.text}")
        else:
            print("❌ Pas de clé API pour tester")
            
    except Exception as e:
        print(f"❌ Erreur test API: {e}")
    
    print("\n--- Diagnostic ---")
    
    # Vérifier les conditions
    issues = []
    
    if not rapidapi_key:
        issues.append("❌ Clé RAPIDAPI_KEY manquante")
    
    if skills.count() == 0:
        issues.append("❌ Aucune compétence dans le profil")
    
    if ExternalJobOffer.objects.count() == 0:
        issues.append("❌ Aucune offre externe en base")
    
    if issues:
        print("🔍 Problèmes identifiés:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ Configuration semble correcte")
    
    print("\n--- Solutions recommandées ---")
    print("1. Vérifier que la clé RAPIDAPI_KEY est configurée dans .env")
    print("2. S'assurer que l'utilisateur a des compétences dans son profil")
    print("3. Tester la recherche avec différentes localisations")
    print("4. Vérifier la connectivité internet pour l'API JSearch")
    
    print("\n=== Fin du diagnostic ===")

if __name__ == "__main__":
    debug_search_issue()