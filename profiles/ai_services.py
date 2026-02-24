"""
Services d'IA pour les recommandations avancées
"""
import requests
import json
import re
from typing import List, Dict, Tuple
from django.conf import settings
from django.db.models import Q, Avg
from django.db import models
from .models import Profile, Skill, Interest
from .ai_models import ExternalJobOffer, AIRecommendation, ProfileAnalysis
from companies.models import JobOffer, Company
import numpy as np

class AIRecommendationEngine:
    """
    Moteur de recommandation basé sur l'IA
    """
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    def analyze_profile(self, profile: Profile) -> ProfileAnalysis:
        """
        Analyse complète du profil étudiant avec IA
        """
        analysis, created = ProfileAnalysis.objects.get_or_create(profile=profile)
        
        # Récupérer les compétences et intérêts
        skills = profile.skill_evaluations.all()
        interests = profile.interest_evaluations.all()
        
        # Analyser les forces et faiblesses
        skill_strengths = []
        skill_gaps = []
        
        for skill_eval in skills:
            if skill_eval.level >= 4:  # Niveau élevé
                skill_strengths.append({
                    'skill': skill_eval.skill.name,
                    'level': skill_eval.level,
                    'category': self._categorize_skill(skill_eval.skill.name)
                })
            elif skill_eval.level <= 2:  # Niveau faible
                skill_gaps.append({
                    'skill': skill_eval.skill.name,
                    'level': skill_eval.level,
                    'improvement_priority': self._calculate_improvement_priority(skill_eval.skill.name)
                })
        
        # Recommandations de compétences basées sur l'IA
        recommended_skills = self._recommend_skills_ai(profile)
        
        # Suggestions de carrière
        career_suggestions = self._suggest_career_paths(profile)
        
        # Calcul des scores
        completeness = self._calculate_profile_completeness(profile)
        marketability = self._calculate_marketability_score(profile)
        
        # Mise à jour de l'analyse
        analysis.skill_strengths = skill_strengths
        analysis.skill_gaps = skill_gaps
        analysis.recommended_skills = recommended_skills
        analysis.career_path_suggestions = career_suggestions
        analysis.profile_completeness = completeness
        analysis.marketability_score = marketability
        analysis.save()
        
        return analysis
    
    def _categorize_skill(self, skill_name: str) -> str:
        """
        Catégorise une compétence
        """
        skill_lower = skill_name.lower()
        
        if any(tech in skill_lower for tech in ['python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'angular']):
            return 'technique'
        elif any(soft in skill_lower for soft in ['communication', 'leadership', 'teamwork', 'management']):
            return 'soft_skills'
        elif any(business in skill_lower for business in ['marketing', 'finance', 'accounting', 'sales']):
            return 'business'
        else:
            return 'autre'
    
    def _calculate_improvement_priority(self, skill_name: str) -> int:
        """
        Calcule la priorité d'amélioration d'une compétence (1-5)
        """
        # Logique basée sur la demande du marché
        high_demand_skills = ['python', 'javascript', 'react', 'sql', 'communication', 'leadership']
        
        if any(skill in skill_name.lower() for skill in high_demand_skills):
            return 5
        else:
            return 3
    
    def _recommend_skills_ai(self, profile: Profile) -> List[Dict]:
        """
        Recommande des compétences basées sur l'IA
        """
        if not self.openai_api_key:
            return self._recommend_skills_fallback(profile)
        
        try:
            # Préparer le contexte du profil
            skills_text = ", ".join([eval.skill.name for eval in profile.skill_evaluations.all()])
            interests_text = ", ".join([eval.interest.name for eval in profile.interest_evaluations.all()])
            
            # Pour l'instant, utiliser la méthode fallback
            # TODO: Implémenter l'intégration OpenAI quand les clés API seront disponibles
            return self._recommend_skills_fallback(profile)
            
        except Exception as e:
            print(f"Erreur OpenAI: {e}")
            return self._recommend_skills_fallback(profile)
    
    def _recommend_skills_fallback(self, profile: Profile) -> List[Dict]:
        """
        Recommandations de compétences sans IA (fallback)
        """
        current_skills = [eval.skill.name.lower() for eval in profile.skill_evaluations.all()]
        
        # Recommandations basées sur des règles
        recommendations = []
        
        if any('python' in skill for skill in current_skills):
            recommendations.append({
                'skill': 'Machine Learning',
                'reason': 'Complément naturel à Python',
                'priority': 4
            })
        
        if any('web' in skill or 'html' in skill for skill in current_skills):
            recommendations.append({
                'skill': 'React.js',
                'reason': 'Framework populaire pour le développement web',
                'priority': 5
            })
        
        # Toujours recommander les soft skills
        recommendations.append({
            'skill': 'Communication',
            'reason': 'Compétence essentielle dans tous les domaines',
            'priority': 5
        })
        
        return recommendations[:5]
    
    def _suggest_career_paths(self, profile: Profile) -> List[Dict]:
        """
        Suggère des chemins de carrière
        """
        skills = [eval.skill.name.lower() for eval in profile.skill_evaluations.all()]
        interests = [eval.interest.name.lower() for eval in profile.interest_evaluations.all()]
        
        career_paths = []
        
        # Logique de suggestion basée sur les compétences
        if any('python' in skill or 'programming' in skill for skill in skills):
            career_paths.append({
                'title': 'Développeur Python',
                'match_score': 85,
                'description': 'Développement d\'applications et analyse de données',
                'required_skills': ['Python', 'SQL', 'Git']
            })
        
        if any('design' in skill or 'creative' in skill for skill in skills):
            career_paths.append({
                'title': 'Designer UX/UI',
                'match_score': 78,
                'description': 'Conception d\'interfaces utilisateur',
                'required_skills': ['Figma', 'Adobe Creative Suite', 'User Research']
            })
        
        if any('business' in interest or 'management' in interest for interest in interests):
            career_paths.append({
                'title': 'Chef de projet',
                'match_score': 72,
                'description': 'Gestion de projets et équipes',
                'required_skills': ['Leadership', 'Communication', 'Gestion de projet']
            })
        
        return sorted(career_paths, key=lambda x: x['match_score'], reverse=True)
    
    def _calculate_profile_completeness(self, profile: Profile) -> float:
        """
        Calcule le pourcentage de complétude du profil
        """
        score = 0
        max_score = 100
        
        # Informations de base (30 points)
        if profile.user.first_name and profile.user.last_name:
            score += 10
        if hasattr(profile, 'cv') and profile.cv:
            score += 20
        
        # Compétences (40 points)
        skill_count = profile.skill_evaluations.count()
        score += min(40, skill_count * 4)  # Max 40 points pour 10+ compétences
        
        # Intérêts (20 points)
        interest_count = profile.interest_evaluations.count()
        score += min(20, interest_count * 2)  # Max 20 points pour 10+ intérêts
        
        # Résultats académiques (10 points)
        if hasattr(profile, 'academic_results') and profile.academic_results.exists():
            score += 10
        
        return min(100, score)
    
    def _calculate_marketability_score(self, profile: Profile) -> float:
        """
        Calcule le score d'employabilité
        """
        score = 0
        
        # Compétences techniques demandées
        high_demand_skills = ['python', 'javascript', 'react', 'sql', 'machine learning']
        user_skills = [eval.skill.name.lower() for eval in profile.skill_evaluations.all()]
        
        for skill in high_demand_skills:
            if any(skill in user_skill for user_skill in user_skills):
                score += 15
        
        # Niveau des compétences
        avg_skill_level = profile.skill_evaluations.aggregate(
            avg_level=Avg('level')
        ).get('avg_level', 0) or 0
        
        score += avg_skill_level * 5  # Max 25 points
        
        return min(100, score)

class ExternalJobSearchService:
    """
    Service pour rechercher des offres d'emploi externes avec JSearch API
    """
    
    def __init__(self):
        self.rapidapi_key = getattr(settings, 'RAPIDAPI_KEY', None)
    
    def search_jsearch_jobs(self, profile: Profile, location: str = "", limit: int = 20) -> List[Dict]:
        """
        Recherche des offres avec JSearch API (RapidAPI) basée sur le profil et CV
        """
        if not self.rapidapi_key:
            # Mode dégradé : utiliser les offres réelles de la base de données
            return self._get_cached_real_jobs(profile, location, limit)
        
        # Construire une requête intelligente basée sur le profil ET les données CV
        query = self._build_intelligent_query(profile, location)
        
        url = "https://jsearch.p.rapidapi.com/search"
        
        # Paramètres optimisés pour JSearch
        querystring = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "employment_types": "FULLTIME,PARTTIME",
            "date_posted": "all"
        }
        
        # Ajouter le pays seulement pour certaines localisations
        if location and location.lower() in ['tunis', 'tunisia', 'tunisie', 'ariana', 'sfax', 'sousse']:
            querystring["country"] = "tn"
        elif location and location.lower() in ['paris', 'lyon', 'marseille', 'france']:
            querystring["country"] = "fr"
        else:
            # Pour les autres localisations, ne pas spécifier de pays
            querystring["country"] = "fr"  # Défaut France
        
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                # Si aucun résultat avec les paramètres spécifiques, essayer une requête plus simple
                if not jobs and location:
                    print(f"Aucun résultat avec requête spécifique, essai avec requête simple...")
                    
                    # Requête simplifiée
                    simple_querystring = {
                        "query": f"emploi {location}",
                        "page": "1",
                        "num_pages": "1",
                        "employment_types": "FULLTIME,PARTTIME"
                    }
                    
                    if location.lower() in ['tunis', 'tunisia', 'tunisie', 'ariana', 'sfax', 'sousse']:
                        simple_querystring["country"] = "tn"
                    
                    response = requests.get(url, headers=headers, params=simple_querystring, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        jobs = data.get('data', [])
                        print(f"Requête simple: {len(jobs)} offres trouvées")
                
                # Traiter et sauvegarder les offres
                processed_jobs = []
                for job in jobs[:limit]:
                    processed_job = self._process_jsearch_job(job, profile)
                    if processed_job:
                        processed_jobs.append(processed_job)
                
                return processed_jobs
            else:
                print(f"Erreur JSearch API: {response.status_code}")
            
        except Exception as e:
            print(f"Erreur recherche JSearch: {e}")
        
        # Fallback en cas d'erreur - utiliser les offres réelles de la base de données
        return self._get_cached_real_jobs(profile, location, limit)
    
    def search_linkedin_jobs(self, profile: Profile, location: str = "", limit: int = 20) -> List[Dict]:
        """
        Recherche spécifique sur LinkedIn via JSearch API
        """
        if not self.rapidapi_key:
            return []
        
        # Construire une requête optimisée pour LinkedIn
        query = self._build_intelligent_query(profile, location)
        
        url = "https://jsearch.p.rapidapi.com/search"
        
        querystring = {
            "query": f"{query} site:linkedin.com",  # Forcer la recherche sur LinkedIn
            "page": "1",
            "num_pages": "1",
            "country": "fr",
            "location": location or "Paris",
            "employment_types": "FULLTIME,PARTTIME",
            "date_posted": "all"
        }
        
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, params=querystring, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get('data', [])
                
                # Filtrer pour ne garder que les offres LinkedIn
                linkedin_jobs = []
                for job in jobs[:limit]:
                    job_url = job.get('job_apply_link', '')
                    if 'linkedin.com' in job_url.lower():
                        processed_job = self._process_jsearch_job(job, profile)
                        if processed_job:
                            # Marquer comme offre LinkedIn
                            processed_job['is_linkedin'] = True
                            linkedin_jobs.append(processed_job)
                
                return linkedin_jobs
            else:
                print(f"Erreur LinkedIn search: {response.status_code}")
                
        except Exception as e:
            print(f"Erreur recherche LinkedIn: {e}")
        
        return []
    
    def search_cv_based_jobs(self, profile: Profile, location: str = "", limit: int = 20) -> Dict:
        """
        Recherche complète basée sur les données CV extraites
        """
        results = {
            'all_sources': [],
            'linkedin_only': [],
            'cv_analysis': {},
            'search_strategy': ''
        }
        
        # 1. Analyser les données CV
        cv_analysis = self._analyze_cv_data(profile)
        results['cv_analysis'] = cv_analysis
        
        # 2. Construire la stratégie de recherche
        strategy = self._build_search_strategy(cv_analysis, location)
        results['search_strategy'] = strategy
        
        # 3. Recherche sur toutes les sources
        all_jobs = self.search_jsearch_jobs(profile, location, limit)
        results['all_sources'] = all_jobs
        
        # 4. Recherche spécifique LinkedIn
        linkedin_jobs = self.search_linkedin_jobs(profile, location, limit//2)
        results['linkedin_only'] = linkedin_jobs
        
        # 5. Combiner et dédupliquer
        combined_jobs = all_jobs + linkedin_jobs
        
        # Dédupliquer par titre et entreprise
        seen = set()
        unique_jobs = []
        for job in combined_jobs:
            external_job = job.get('external_job')
            if external_job:
                key = (external_job.title.lower(), external_job.company_name.lower())
                if key not in seen:
                    seen.add(key)
                    unique_jobs.append(job)
        
        results['all_sources'] = unique_jobs[:limit]
        
        return results
    
    def _analyze_cv_data(self, profile: Profile) -> Dict:
        """
        Analyse les données extraites du CV
        """
        analysis = {
            'has_cv_data': False,
            'skills_from_cv': [],
            'experience_level': 'junior',
            'work_experience': [],
            'education': [],
            'total_experience_months': 0
        }
        
        try:
            from .ai_models import CVExtraction
            cv_extraction = CVExtraction.objects.filter(profile=profile).first()
            
            if cv_extraction and cv_extraction.is_processed:
                analysis['has_cv_data'] = True
                analysis['skills_from_cv'] = cv_extraction.extracted_skills or []
                analysis['work_experience'] = cv_extraction.work_experiences or []
                analysis['education'] = cv_extraction.extracted_educations or []
                
                # Calculer l'expérience totale
                analysis['experience_level'] = self._determine_experience_level(analysis['work_experience'])
                
        except Exception as e:
            print(f"Erreur analyse CV: {e}")
        
        return analysis
    
    def _build_search_strategy(self, cv_analysis: Dict, location: str) -> str:
        """
        Construit une stratégie de recherche basée sur l'analyse CV
        """
        strategy_parts = []
        
        if cv_analysis['has_cv_data']:
            strategy_parts.append("✓ Utilisation des données CV extraites")
            
            if cv_analysis['skills_from_cv']:
                # Extraire les noms des compétences depuis les dictionnaires
                main_skills_raw = cv_analysis['skills_from_cv'][:3]
                main_skills = []
                for skill_item in main_skills_raw:
                    if isinstance(skill_item, dict):
                        skill_name = skill_item.get('skill', '')
                        if skill_name:
                            main_skills.append(skill_name)
                    elif isinstance(skill_item, str):
                        main_skills.append(skill_item)
                
                if main_skills:
                    strategy_parts.append(f"✓ Compétences principales: {', '.join(main_skills)}")
            
            strategy_parts.append(f"✓ Niveau d'expérience: {cv_analysis['experience_level']}")
            
            if location:
                strategy_parts.append(f"✓ Localisation ciblée: {location}")
            
            strategy_parts.append("✓ Recherche multi-sources (JSearch + LinkedIn)")
        else:
            strategy_parts.append("⚠️ Pas de données CV - utilisation du questionnaire uniquement")
            strategy_parts.append("✓ Recherche basée sur les compétences du profil")
        
        return " | ".join(strategy_parts)
    
    def _build_intelligent_query(self, profile: Profile, location: str = "") -> str:
        """
        Construit une requête intelligente basée sur le profil et les données CV extraites
        """
        # 1. Récupérer les données CV si disponibles
        cv_skills = []
        cv_experience = []
        
        try:
            from .ai_models import CVExtraction
            cv_extraction = CVExtraction.objects.filter(profile=profile).first()
            if cv_extraction and cv_extraction.is_processed:
                # Extraire les noms des compétences depuis les dictionnaires
                raw_cv_skills = cv_extraction.extracted_skills or []
                for skill_item in raw_cv_skills:
                    if isinstance(skill_item, dict):
                        skill_name = skill_item.get('skill', '')
                        if skill_name:
                            cv_skills.append(skill_name.lower())
                    elif isinstance(skill_item, str):
                        cv_skills.append(skill_item.lower())
                
                cv_experience = cv_extraction.work_experiences or []
        except Exception:
            pass
        
        # 2. Récupérer les compétences du questionnaire
        profile_skills = [eval.skill.name.lower() for eval in profile.skill_evaluations.all()]
        
        # 3. Combiner toutes les compétences (CV + questionnaire)
        all_skills = list(set(cv_skills + profile_skills))
        
        # 4. Analyser l'expérience pour déterminer le niveau
        experience_level = self._determine_experience_level(cv_experience)
        
        # 5. Construire la requête optimisée
        query_parts = []
        
        # Priorité aux compétences techniques du CV
        priority_skills = ['python', 'javascript', 'java', 'react', 'django', 'nodejs', 'angular', 'vue']
        main_skill = None
        
        for skill in all_skills:
            skill_lower = skill.lower()
            for priority in priority_skills:
                if priority in skill_lower:
                    main_skill = priority
                    break
            if main_skill:
                break
        
        # Construire la requête de base
        if main_skill:
            if main_skill == 'python':
                query_parts.append("développeur python")
            elif main_skill == 'javascript':
                query_parts.append("développeur javascript")
            elif main_skill == 'java':
                query_parts.append("développeur java")
            elif main_skill == 'react':
                query_parts.append("développeur react")
            elif main_skill == 'django':
                query_parts.append("développeur django")
            else:
                query_parts.append(f"développeur {main_skill}")
        else:
            query_parts.append("développeur")
        
        # Ajouter le niveau d'expérience
        if experience_level == "senior":
            query_parts.append("senior")
        elif experience_level == "junior":
            query_parts.append("junior")
        
        # Ajouter la localisation pour de meilleurs résultats
        if location and location.strip():
            query_parts.append(location.strip())
        
        return " ".join(query_parts)
    
    def _determine_experience_level(self, work_experiences: List) -> str:
        """
        Détermine le niveau d'expérience basé sur les données CV
        """
        if not work_experiences:
            return "junior"
        
        # Analyser la durée totale d'expérience
        total_months = 0
        for exp in work_experiences:
            if isinstance(exp, dict):
                duration = exp.get('duration', '')
                # Logique simple pour extraire la durée
                if 'an' in duration.lower() or 'year' in duration.lower():
                    try:
                        years = int(''.join(filter(str.isdigit, duration.split()[0])))
                        total_months += years * 12
                    except:
                        total_months += 12  # Défaut 1 an
                elif 'mois' in duration.lower() or 'month' in duration.lower():
                    try:
                        months = int(''.join(filter(str.isdigit, duration.split()[0])))
                        total_months += months
                    except:
                        total_months += 6  # Défaut 6 mois
        
        # Déterminer le niveau
        if total_months >= 60:  # 5+ ans
            return "senior"
        elif total_months >= 24:  # 2+ ans
            return "confirmé"
        else:
            return "junior"
    
    def _generate_mock_external_jobs(self, profile: Profile, location: str, limit: int) -> List[Dict]:
        """
        Génère des offres simulées basées sur le profil (mode dégradé)
        """
        user_skills = [eval.skill.name for eval in profile.skill_evaluations.all()]
        
        # Templates d'offres basées sur les compétences
        job_templates = []
        
        if any('python' in skill.lower() for skill in user_skills):
            job_templates.extend([
                {
                    'title': 'Développeur Python Junior',
                    'company': 'TechCorp France',
                    'description': 'Développement d\'applications Python, Django, analyse de données',
                    'compatibility': 85
                },
                {
                    'title': 'Data Analyst Python',
                    'company': 'DataViz Solutions',
                    'description': 'Analyse de données avec Python, pandas, matplotlib',
                    'compatibility': 78
                }
            ])
        
        if any('web' in skill.lower() or 'html' in skill.lower() for skill in user_skills):
            job_templates.extend([
                {
                    'title': 'Développeur Web Frontend',
                    'company': 'WebAgency Paris',
                    'description': 'Développement frontend HTML, CSS, JavaScript, React',
                    'compatibility': 82
                },
                {
                    'title': 'Intégrateur Web',
                    'company': 'Digital Studio',
                    'description': 'Intégration HTML/CSS, responsive design, WordPress',
                    'compatibility': 75
                }
            ])
        
        if any('design' in skill.lower() for skill in user_skills):
            job_templates.extend([
                {
                    'title': 'Designer UX/UI',
                    'company': 'Creative Agency',
                    'description': 'Conception d\'interfaces, prototypage, Figma, Adobe Creative Suite',
                    'compatibility': 88
                }
            ])
        
        # Offres génériques si pas de compétences spécifiques
        if not job_templates:
            job_templates = [
                {
                    'title': 'Assistant Marketing Digital',
                    'company': 'Marketing Plus',
                    'description': 'Gestion des réseaux sociaux, création de contenu, analyse des performances',
                    'compatibility': 65
                },
                {
                    'title': 'Chargé de Communication',
                    'company': 'Com & Co',
                    'description': 'Communication interne et externe, rédaction, événementiel',
                    'compatibility': 60
                },
                {
                    'title': 'Assistant Commercial',
                    'company': 'Sales Pro',
                    'description': 'Support commercial, relation client, suivi des ventes',
                    'compatibility': 55
                }
            ]
        
        # Générer les offres simulées
        mock_jobs = []
        location_display = location or "France"
        
        for i, template in enumerate(job_templates[:limit]):
            # Tronquer les champs pour respecter les limites de la base de données
            title = template['title'][:490]
            company = template['company'][:290]
            description = template['description'][:1000]  # Tronquer la description aussi
            location_truncated = location_display[:290]
            
            # Créer un ID externe unique et tronqué
            external_id = f"mock_{title.lower().replace(' ', '_')}_{i}"[:290]
            
            # Créer une offre externe simulée
            try:
                external_job, created = ExternalJobOffer.objects.get_or_create(
                    external_id=external_id,
                    defaults={
                        'title': title,
                        'company_name': company,
                        'description': description,
                        'location': location_truncated,
                        'external_url': f"https://www.google.com/search?q={title.replace(' ', '+')}+{company.replace(' ', '+')}+emploi",
                        'source': 'jsearch'
                    }
                )
                
                mock_jobs.append({
                    'external_job': external_job,
                    'compatibility_score': template['compatibility'],
                    'title': title,
                    'company': company,
                    'location': location_truncated,
                    'url': f"/external-jobs/{external_job.id}/"
                })
            except Exception as e:
                print(f"Erreur création offre mock: {e}")
                continue
        
        return mock_jobs
    
    def _get_cached_real_jobs(self, profile: Profile, location: str, limit: int) -> List[Dict]:
        """
        Récupère les offres réelles de la base de données (pas de simulation)
        """
        # Filtrer uniquement les offres réelles (pas de mock)
        real_offers = ExternalJobOffer.objects.filter(
            source='jsearch'
        ).exclude(
            external_id__icontains='mock'
        ).exclude(
            external_url__icontains='google.com/search'
        ).exclude(
            external_url__icontains='example.com'
        )
        
        # Filtrer par localisation si spécifiée
        if location and location.strip():
            location_lower = location.lower()
            real_offers = real_offers.filter(
                models.Q(location__icontains=location) |
                models.Q(location__icontains=location_lower)
            )
        
        # Limiter le nombre de résultats
        real_offers = real_offers[:limit * 2]  # Prendre plus pour avoir du choix après calcul de compatibilité
        
        cached_jobs = []
        for offer in real_offers:
            # Calculer la compatibilité
            compatibility_score = self._calculate_job_compatibility(
                offer.description + " " + offer.title, profile
            )
            
            # Garder seulement les offres avec une compatibilité raisonnable
            if compatibility_score > 10:  # Seuil plus bas pour avoir plus de résultats
                cached_jobs.append({
                    'external_job': offer,
                    'compatibility_score': compatibility_score,
                    'title': offer.title,
                    'company': offer.company_name,
                    'location': offer.location,
                    'url': f"/external-jobs/{offer.id}/",
                    'is_real': True
                })
        
        # Trier par compatibilité et limiter
        cached_jobs.sort(key=lambda x: x['compatibility_score'], reverse=True)
        return cached_jobs[:limit]
    
    def _process_jsearch_job(self, job_data: Dict, profile: Profile) -> Dict:
        """
        Traite une offre JSearch et calcule la compatibilité
        """
        try:
            # Extraire les informations de JSearch
            title = job_data.get('job_title', '')
            company = job_data.get('employer_name', '')
            description = job_data.get('job_description', '')
            job_city = job_data.get('job_city', '') or ''
            job_country = job_data.get('job_country', '') or ''
            location = f"{job_city}, {job_country}".strip(', ')
            apply_url = job_data.get('job_apply_link', '')
            job_id = job_data.get('job_id', '')
            
            # Informations supplémentaires JSearch
            employment_type = job_data.get('job_employment_type', '')
            salary_min = job_data.get('job_min_salary')
            salary_max = job_data.get('job_max_salary')
            posted_date = job_data.get('job_posted_at_datetime_utc', '')
            
            # Calculer le score de compatibilité
            compatibility_score = self._calculate_job_compatibility(
                description + " " + title, profile
            )
            
            # Tronquer les champs pour respecter les limites de la base de données
            title = title[:490] if title else ''  # max_length=500, garde une marge
            company = company[:290] if company else ''  # max_length=300, garde une marge
            location = location[:290] if location else ''  # max_length=300, garde une marge
            
            # Créer un ID externe unique et tronqué
            location_key = location.replace(' ', '_').replace(',', '').lower() if location else 'default'
            external_id = f"jsearch_{job_id}_{location_key}"
            external_id = external_id[:290]  # max_length=300, garde une marge
            
            # Tronquer l'URL si nécessaire (URLField a généralement une limite)
            if apply_url and len(apply_url) > 2000:
                apply_url = apply_url[:2000]
            
            # Créer ou mettre à jour l'offre externe
            external_job, created = ExternalJobOffer.objects.get_or_create(
                external_id=external_id,
                defaults={
                    'title': title,
                    'company_name': company,
                    'description': description,
                    'location': location,
                    'external_url': apply_url,
                    'source': 'jsearch',
                    'salary_min': salary_min,
                    'salary_max': salary_max
                }
            )
            
            # Extraire et associer les compétences (avec gestion d'erreur)
            try:
                extracted_skills = self._extract_skills_from_text(description)
                external_job.extracted_skills.set(extracted_skills)
            except Exception as skill_error:
                print(f"Erreur extraction compétences: {skill_error}")
            
            return {
                'external_job': external_job,
                'compatibility_score': compatibility_score,
                'title': title,
                'company': company,
                'location': location,
                'url': f"/external-jobs/{external_job.id}/",
                'employment_type': employment_type,
                'posted_date': posted_date
            }
            
        except Exception as e:
            print(f"Erreur traitement offre JSearch: {e}")
            return None
    
    def _calculate_job_compatibility(self, job_text: str, profile: Profile) -> float:
        """
        Calcule la compatibilité entre une offre et un profil
        """
        # Récupérer les compétences du profil
        user_skills = [eval.skill.name.lower() for eval in profile.skill_evaluations.all()]
        user_interests = [eval.interest.name.lower() for eval in profile.interest_evaluations.all()]
        
        if not user_skills and not user_interests:
            return 50  # Score neutre si pas de données
        
        job_text_lower = job_text.lower()
        
        # Compter les correspondances de compétences
        skill_matches = 0
        for skill in user_skills:
            # Recherche plus flexible
            skill_words = skill.split()
            for word in skill_words:
                if len(word) > 2 and word in job_text_lower:
                    skill_matches += 1
                    break
        
        # Compter les correspondances d'intérêts
        interest_matches = 0
        for interest in user_interests:
            interest_words = interest.split()
            for word in interest_words:
                if len(word) > 3 and word in job_text_lower:
                    interest_matches += 1
                    break
        
        # Calculer le score (0-100)
        skill_score = 0
        interest_score = 0
        
        if user_skills:
            skill_score = (skill_matches / len(user_skills)) * 70  # 70% pour les compétences
        
        if user_interests:
            interest_score = (interest_matches / len(user_interests)) * 30  # 30% pour les intérêts
        
        total_score = skill_score + interest_score
        
        # Bonus pour les mots-clés génériques
        generic_keywords = ['stage', 'junior', 'débutant', 'formation', 'apprentissage']
        for keyword in generic_keywords:
            if keyword in job_text_lower:
                total_score += 10
                break
        
        return min(100, max(0, total_score))
    
    def _extract_skills_from_text(self, text: str) -> List[Skill]:
        """
        Extrait les compétences mentionnées dans un texte
        """
        extracted_skills = []
        text_lower = text.lower()
        
        # Récupérer toutes les compétences existantes
        all_skills = Skill.objects.all()
        
        for skill in all_skills:
            if skill.name.lower() in text_lower:
                extracted_skills.append(skill)
        
        return extracted_skills

class CompanyRecommendationService:
    """
    Service de recommandation de profils pour les entreprises
    """
    
    def recommend_students_for_company(self, company, job_offer: JobOffer = None, limit: int = 10) -> List[Dict]:
        """
        Recommande des étudiants pour une entreprise
        """
        # Récupérer tous les profils étudiants
        student_profiles = Profile.objects.filter(
            user__user_type='student'
        ).prefetch_related('skill_evaluations__skill', 'interest_evaluations__interest')
        
        recommendations = []
        
        for profile in student_profiles:
            if job_offer:
                # Recommandation pour une offre spécifique
                score = self._calculate_student_job_match(profile, job_offer)
            else:
                # Recommandation générale pour l'entreprise
                score = self._calculate_student_company_match(profile, company)
            
            if score > 20:  # Seuil minimum
                recommendations.append({
                    'profile': profile,
                    'score': score,
                    'reasoning': self._generate_recommendation_reasoning(profile, job_offer or company)
                })
        
        # Trier par score et limiter
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    def _calculate_student_job_match(self, profile: Profile, job_offer: JobOffer) -> float:
        """
        Calcule la compatibilité étudiant-offre
        """
        score = 0
        
        # Compétences requises
        required_skills = job_offer.required_skills.all()
        user_skills = {eval.skill: eval.level for eval in profile.skill_evaluations.all()}
        
        if required_skills:
            skill_matches = 0
            total_skill_score = 0
            
            for required_skill in required_skills:
                if required_skill in user_skills:
                    skill_matches += 1
                    total_skill_score += user_skills[required_skill]
            
            # Score basé sur les compétences (70% du total)
            skill_percentage = skill_matches / len(required_skills)
            avg_skill_level = total_skill_score / skill_matches if skill_matches > 0 else 0
            score += (skill_percentage * avg_skill_level * 20) * 0.7
        
        # Intérêts (30% du total)
        # Logique simplifiée - peut être améliorée avec l'IA
        if profile.interest_evaluations.exists():
            score += 30 * 0.3
        
        return min(100, score)
    
    def _calculate_student_company_match(self, profile: Profile, company) -> float:
        """
        Calcule la compatibilité étudiant-entreprise (général)
        """
        # Logique basée sur toutes les offres de l'entreprise
        company_offers = company.job_offers.filter(is_active=True)
        
        if not company_offers.exists():
            return 50  # Score neutre si pas d'offres
        
        total_score = 0
        for offer in company_offers:
            total_score += self._calculate_student_job_match(profile, offer)
        
        return total_score / company_offers.count()
    
    def _generate_recommendation_reasoning(self, profile: Profile, target) -> str:
        """
        Génère une explication de la recommandation
        """
        skills = [eval.skill.name for eval in profile.skill_evaluations.all()[:3]]
        skills_text = ", ".join(skills)
        
        if isinstance(target, JobOffer):
            return f"Profil compatible grâce aux compétences: {skills_text}. Correspond aux exigences du poste {target.title}."
        else:
            return f"Profil intéressant avec les compétences: {skills_text}. Bon potentiel pour l'entreprise."