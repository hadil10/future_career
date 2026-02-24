"""
Vues pour les fonctionnalités d'IA
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
import json
import time

from .models import Profile
from .ai_models import ExternalJobOffer, AIRecommendation, ProfileAnalysis, AISearchQuery
from .ai_services import AIRecommendationEngine, ExternalJobSearchService, CompanyRecommendationService
from companies.models import Company, JobOffer

@login_required
def ai_dashboard_view(request):
    """
    Tableau de bord IA pour les étudiants
    """
    if request.user.user_type != 'student':
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('profiles:home')
    
    profile = get_object_or_404(Profile, user=request.user)
    
    # Initialiser les services IA
    ai_engine = AIRecommendationEngine()
    
    # Analyser le profil
    analysis = ai_engine.analyze_profile(profile)
    
    # Récupérer les recommandations récentes
    recent_recommendations = AIRecommendation.objects.filter(
        student_profile=profile,
        recommendation_type__in=['external_job', 'job_to_student']
    )[:5]
    
    context = {
        'profile': profile,
        'analysis': analysis,
        'recent_recommendations': recent_recommendations,
        'completeness_percentage': analysis.profile_completeness,
        'marketability_percentage': analysis.marketability_score,
    }
    
    return render(request, 'profiles/ai_dashboard.html', context)

@login_required
def ai_job_search_view(request):
    """
    Recherche d'offres avec IA
    """
    if request.user.user_type != 'student':
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('profiles:home')
    
    profile = get_object_or_404(Profile, user=request.user)
    search_service = ExternalJobSearchService()
    
    # Paramètres de recherche
    location = request.GET.get('location', '')
    search_external = request.GET.get('external', 'true') == 'true'
    
    external_jobs = []
    internal_jobs = []
    
    # Vérifier si une recherche a été effectuée (présence de paramètres GET)
    search_performed = bool(request.GET)
    
    if search_performed and search_external:
        # Recherche sur JSearch seulement si une recherche est demandée
        try:
            import time
            start_time = time.time()
            
            external_results = search_service.search_jsearch_jobs(profile, location, limit=20)
            external_jobs = external_results
            
            search_time = time.time() - start_time
            
            # Enregistrer la requête
            try:
                AISearchQuery.objects.create(
                    user=request.user,
                    query_text=f"Recherche externe - Location: {location}",
                    search_parameters={
                        'location': location,
                        'external': True,
                        'source': 'jsearch'
                    },
                    results_count=len(external_jobs),
                    execution_time=search_time
                )
            except Exception as query_error:
                print(f"Erreur enregistrement requête: {query_error}")
            
            # Message informatif si peu de résultats (probablement dû au rate limiting)
            if len(external_jobs) < 5:
                messages.info(request, 
                    "Recherche effectuée avec succès. "
                    "Nombre de résultats limité par la charge du serveur. "
                    "Réessayez dans quelques minutes pour plus d'offres.")
            
        except Exception as e:
            messages.warning(request, f"Erreur lors de la recherche externe: {str(e)}")
            print(f"Erreur recherche externe: {e}")
    
    if search_performed:
        # Recherche interne avec IA seulement si une recherche est demandée
        ai_engine = AIRecommendationEngine()
        recommendations = ai_engine.analyze_profile(profile)
        
        # Récupérer les offres internes recommandées
        internal_offers = JobOffer.objects.filter(is_active=True)
        
        for offer in internal_offers:
            # Calculer la compatibilité
            compatibility = search_service._calculate_job_compatibility(
                offer.description + " " + offer.title, profile
            )
            if compatibility > 20:
                internal_jobs.append({
                    'offer': offer,
                    'compatibility_score': compatibility,
                    'is_internal': True
                })
    
    # Trier par score
    internal_jobs.sort(key=lambda x: x['compatibility_score'], reverse=True)
    
    # Vérifier si on est en mode démo (si des offres externes sont des mocks)
    demo_mode = False
    if external_jobs:
        for job in external_jobs:
            external_job = job.get('external_job')
            if external_job and hasattr(external_job, 'external_id') and 'mock' in external_job.external_id:
                demo_mode = True
                break
    
    # Pagination
    all_jobs = external_jobs + internal_jobs if search_performed else []
    paginator = Paginator(all_jobs, 12)
    page_number = request.GET.get('page')
    jobs_page = paginator.get_page(page_number)
    
    context = {
        'jobs': jobs_page,
        'page_obj': jobs_page,
        'location': location,
        'search_external': search_external,
        'total_results': len(all_jobs),
        'external_count': len(external_jobs),
        'internal_count': len(internal_jobs),
        'demo_mode': demo_mode,
        'search_performed': search_performed,
    }
    
    return render(request, 'profiles/ai_job_search.html', context)

@login_required
def company_ai_dashboard_view(request):
    """
    Tableau de bord IA pour les entreprises
    """
    if request.user.user_type != 'company':
        messages.error(request, "Accès réservé aux entreprises.")
        return redirect('profiles:home')
    
    company = get_object_or_404(Company, user=request.user)
    recommendation_service = CompanyRecommendationService()
    
    # Recommandations générales d'étudiants
    student_recommendations = recommendation_service.recommend_students_for_company(
        company, limit=10
    )
    
    # Statistiques
    total_offers = company.job_offers.filter(is_active=True).count()
    total_applications = sum(
        offer.applications.count() for offer in company.job_offers.filter(is_active=True)
    )
    
    context = {
        'company': company,
        'student_recommendations': student_recommendations,
        'total_offers': total_offers,
        'total_applications': total_applications,
    }
    
    return render(request, 'companies/ai_dashboard.html', context)

@login_required
def company_student_recommendations_view(request, offer_id=None):
    """
    Recommandations d'étudiants pour une offre spécifique
    """
    if request.user.user_type != 'company':
        messages.error(request, "Accès réservé aux entreprises.")
        return redirect('profiles:home')
    
    company = get_object_or_404(Company, user=request.user)
    recommendation_service = CompanyRecommendationService()
    
    job_offer = None
    if offer_id:
        job_offer = get_object_or_404(JobOffer, id=offer_id, company=company)
    
    # Obtenir les recommandations
    recommendations = recommendation_service.recommend_students_for_company(
        company, job_offer, limit=20
    )
    
    # Pagination
    paginator = Paginator(recommendations, 10)
    page_number = request.GET.get('page')
    recommendations_page = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'job_offer': job_offer,
        'recommendations': recommendations_page,
        'page_obj': recommendations_page,
        'total_recommendations': len(recommendations),
    }
    
    return render(request, 'companies/student_recommendations.html', context)

@login_required
@require_http_methods(["POST"])
def refresh_profile_analysis_view(request):
    """
    Actualise l'analyse IA du profil
    """
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    try:
        profile = get_object_or_404(Profile, user=request.user)
        ai_engine = AIRecommendationEngine()
        
        # Forcer une nouvelle analyse
        if hasattr(profile, 'ai_analysis'):
            profile.ai_analysis.delete()
        
        analysis = ai_engine.analyze_profile(profile)
        
        return JsonResponse({
            'success': True,
            'completeness': analysis.profile_completeness,
            'marketability': analysis.marketability_score,
            'message': 'Analyse mise à jour avec succès!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def ai_career_guidance_view(request):
    """
    Conseils de carrière basés sur l'IA
    """
    if request.user.user_type != 'student':
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('profiles:home')
    
    profile = get_object_or_404(Profile, user=request.user)
    ai_engine = AIRecommendationEngine()
    
    # Obtenir l'analyse du profil
    analysis = ai_engine.analyze_profile(profile)
    
    # Recommandations de compétences à développer
    skill_recommendations = analysis.recommended_skills
    
    # Chemins de carrière suggérés
    career_paths = analysis.career_path_suggestions
    
    context = {
        'profile': profile,
        'analysis': analysis,
        'skill_recommendations': skill_recommendations,
        'career_paths': career_paths,
    }
    
    return render(request, 'profiles/ai_career_guidance.html', context)

@login_required
def external_job_detail_view(request, job_id):
    """
    Détail d'une offre externe
    """
    from django.http import HttpResponse
    
    external_job = get_object_or_404(ExternalJobOffer, id=job_id)
    
    # Calculer la compatibilité si l'utilisateur est un étudiant
    compatibility_score = 0
    if request.user.user_type == 'student' and hasattr(request.user, 'profile'):
        search_service = ExternalJobSearchService()
        compatibility_score = search_service._calculate_job_compatibility(
            external_job.description, request.user.profile
        )
    
    context = {
        'job': external_job,
        'compatibility_score': compatibility_score,
    }
    
    response = render(request, 'profiles/external_job_detail.html', context)
    
    # Empêcher la mise en cache pour éviter les problèmes d'anciennes données
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

@login_required
def ai_search_history_view(request):
    """
    Historique des recherches IA
    """
    searches = AISearchQuery.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(searches, 20)
    page_number = request.GET.get('page')
    searches_page = paginator.get_page(page_number)
    
    context = {
        'searches': searches_page,
        'page_obj': searches_page,
    }
    
    return render(request, 'profiles/ai_search_history.html', context)

@login_required
def extract_cv_data_view(request):
    """
    Extrait les données du CV de l'utilisateur avec l'IA
    """
    if request.user.user_type != 'student':
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('profiles:home')
    
    profile = get_object_or_404(Profile, user=request.user)
    
    if not profile.cv:
        messages.error(request, "Aucun CV n'a été téléchargé. Veuillez d'abord télécharger votre CV.")
        return redirect('profiles:profile-update')
    
    try:
        from .cv_extraction_service import CVExtractionService
        extraction_service = CVExtractionService()
        
        # Extraire les données du CV
        extraction = extraction_service.extract_cv_data(profile)
        
        if extraction and extraction.is_processed:
            messages.success(request, "Extraction des données CV réussie ! Votre profil a été enrichi automatiquement.")
            
            # Générer des recommandations basées sur le CV
            recommendations = extraction_service.get_job_recommendations_from_cv(profile)
            
            context = {
                'extraction': extraction,
                'recommendations': recommendations,
                'profile': profile
            }
            
            return render(request, 'profiles/cv_extraction_results.html', context)
        else:
            error_msg = extraction.processing_errors if extraction else "Erreur inconnue"
            messages.error(request, f"Erreur lors de l'extraction: {error_msg}")
            return redirect('profiles:profile-detail')
            
    except Exception as e:
        messages.error(request, f"Erreur lors de l'extraction des données CV: {str(e)}")
        return redirect('profiles:profile-detail')

@login_required
def cv_extraction_status_view(request):
    """
    Affiche le statut de l'extraction CV
    """
    if request.user.user_type != 'student':
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('profiles:home')
    
    profile = get_object_or_404(Profile, user=request.user)
    
    try:
        from .ai_models import CVExtraction
        extraction = CVExtraction.objects.get(profile=profile)
    except CVExtraction.DoesNotExist:
        extraction = None
    
    context = {
        'profile': profile,
        'extraction': extraction,
        'has_cv': bool(profile.cv)
    }
    
    return render(request, 'profiles/cv_extraction_status.html', context)

@login_required
@require_http_methods(["POST"])
def refresh_cv_extraction_view(request):
    """
    Relance l'extraction des données CV (AJAX)
    """
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    try:
        profile = get_object_or_404(Profile, user=request.user)
        
        if not profile.cv:
            return JsonResponse({
                'success': False,
                'error': 'Aucun CV téléchargé'
            })
        
        from .cv_extraction_service import CVExtractionService
        extraction_service = CVExtractionService()
        
        # Supprimer l'ancienne extraction
        from .ai_models import CVExtraction
        CVExtraction.objects.filter(profile=profile).delete()
        
        # Nouvelle extraction
        extraction = extraction_service.extract_cv_data(profile)
        
        if extraction and extraction.is_processed:
            # Générer des recommandations
            recommendations = extraction_service.get_job_recommendations_from_cv(profile)
            
            return JsonResponse({
                'success': True,
                'message': 'Extraction réussie !',
                'data': {
                    'skills_count': len(extraction.extracted_skills),
                    'experiences_count': len(extraction.work_experiences),
                    'educations_count': len(extraction.extracted_educations),
                    'recommendations_count': len(recommendations),
                    'confidence': extraction.extraction_confidence
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': extraction.processing_errors if extraction else 'Erreur inconnue'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@require_http_methods(["POST"])
def ai_instant_recommendations_view(request):
    """
    Recherche instantanée de recommandations IA (AJAX)
    """
    if request.user.user_type != 'student':
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    try:
        profile = get_object_or_404(Profile, user=request.user)
        
        # Paramètres de recherche
        data = json.loads(request.body)
        location = data.get('location', '')
        search_external = data.get('search_external', True)
        limit = data.get('limit', 10)
        
        # Services IA
        search_service = ExternalJobSearchService()
        ai_engine = AIRecommendationEngine()
        
        results = {
            'internal_jobs': [],
            'external_jobs': [],
            'total_count': 0,
            'search_time': 0
        }
        
        import time
        start_time = time.time()
        
        # Recherche interne avec IA
        internal_offers = JobOffer.objects.filter(is_active=True)[:limit]
        for offer in internal_offers:
            compatibility = search_service._calculate_job_compatibility(
                offer.description + " " + offer.title, profile
            )
            if compatibility > 20:
                results['internal_jobs'].append({
                    'id': offer.id,
                    'title': offer.title,
                    'company': offer.company.name,
                    'location': offer.location or 'Non spécifié',
                    'compatibility_score': round(compatibility),
                    'offer_type': offer.get_offer_type_display(),
                    'url': f'/offers/{offer.id}/',
                    'is_internal': True
                })
        
        # Recherche externe si demandée
        if search_external:
            try:
                external_results = search_service.search_jsearch_jobs(profile, location, limit=limit)
                for job in external_results[:limit]:
                    if job and job.get('external_job'):
                        results['external_jobs'].append({
                            'id': job['external_job'].id,
                            'title': job['title'],
                            'company': job['company'],
                            'location': job['location'] or 'Non spécifié',
                            'compatibility_score': round(job['compatibility_score']),
                            'url': job['url'],
                            'is_internal': False
                        })
            except Exception as e:
                print(f"Erreur recherche externe: {e}")
        
        # Trier tous les résultats par score
        all_jobs = results['internal_jobs'] + results['external_jobs']
        all_jobs.sort(key=lambda x: x['compatibility_score'], reverse=True)
        
        results['all_jobs'] = all_jobs[:limit]
        results['total_count'] = len(all_jobs)
        results['search_time'] = round(time.time() - start_time, 2)
        
        # Enregistrer la recherche
        try:
            AISearchQuery.objects.create(
                user=request.user,
                query_text=f"Recherche IA instantanée - Location: {location}",
                search_parameters={
                    'location': location,
                    'search_external': search_external,
                    'limit': limit
                },
                results_count=results['total_count'],
                execution_time=results['search_time']
            )
        except Exception as e:
            print(f"Erreur enregistrement recherche: {e}")
        
        return JsonResponse({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
@login_required
def external_jobs_diagnostic_view(request):
    """
    Page de diagnostic pour les offres externes
    """
    if not request.user.is_staff:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('profiles:home')
    
    from .ai_models import ExternalJobOffer
    
    jobs = ExternalJobOffer.objects.all().order_by('-created_at')
    
    context = {
        'jobs': jobs,
        'total_jobs': jobs.count(),
    }
    
    return render(request, 'profiles/external_jobs_diagnostic.html', context)

@login_required
@require_http_methods(["POST"])
def cleanup_external_jobs_view(request):
    """
    Nettoie toutes les offres externes (AJAX)
    """
    if not request.user.is_staff:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    try:
        from .ai_models import ExternalJobOffer
        count = ExternalJobOffer.objects.all().count()
        ExternalJobOffer.objects.all().delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{count} offres externes supprimées avec succès!'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)

@login_required
def cv_extraction_results_view(request):
    """
    Affiche les résultats de l'extraction CV
    """
    if request.user.user_type != 'student':
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('profiles:home')
    
    profile = get_object_or_404(Profile, user=request.user)
    
    try:
        from .ai_models import CVExtraction
        extraction = CVExtraction.objects.get(profile=profile)
    except CVExtraction.DoesNotExist:
        messages.error(request, "Aucune extraction CV trouvée. Veuillez d'abord extraire les données de votre CV.")
        return redirect('profiles:cv-extraction-status')
    
    # Générer des recommandations basées sur le CV si possible
    recommendations = []
    try:
        from .cv_extraction_service import CVExtractionService
        extraction_service = CVExtractionService()
        recommendations = extraction_service.get_job_recommendations_from_cv(profile)
    except Exception as e:
        print(f"Erreur génération recommandations: {e}")
    
    context = {
        'extraction': extraction,
        'recommendations': recommendations,
        'profile': profile
    }
    
    return render(request, 'profiles/cv_extraction_results.html', context)

@login_required
def cv_based_job_search_view(request):
    """
    Recherche d'offres basée sur les données CV extraites
    """
    if request.user.user_type != 'student':
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('profiles:home')
    
    profile = get_object_or_404(Profile, user=request.user)
    search_service = ExternalJobSearchService()
    
    # Toujours analyser les données CV, même sans recherche
    cv_analysis = search_service._analyze_cv_data(profile)
    
    # Paramètres de recherche
    location = request.GET.get('location', '')
    search_linkedin = request.GET.get('linkedin', 'false') == 'true'
    # Déclencher la recherche si des paramètres GET sont présents
    search_performed = bool(request.GET.keys())
    
    results = {}
    all_jobs = []
    
    if search_performed:
        try:
            import time
            start_time = time.time()
            
            # Utiliser une localisation par défaut si vide
            search_location = location.strip() if location.strip() else "France"
            
            if search_linkedin:
                # Recherche spécifique LinkedIn
                linkedin_jobs = search_service.search_linkedin_jobs(profile, search_location, limit=15)
                results = {
                    'all_sources': linkedin_jobs,
                    'linkedin_only': linkedin_jobs,
                    'cv_analysis': cv_analysis,
                    'search_strategy': f"Recherche LinkedIn spécifique - {search_location}"
                }
            else:
                # Recherche complète basée sur le CV
                results = search_service.search_cv_based_jobs(profile, search_location, limit=20)
                # S'assurer que cv_analysis est inclus dans les résultats
                results['cv_analysis'] = cv_analysis
            
            # Récupérer les résultats
            all_jobs = results.get('all_sources', [])
            
            search_time = time.time() - start_time
            
            # Enregistrer la requête
            try:
                AISearchQuery.objects.create(
                    user=request.user,
                    query_text=f"Recherche CV-basée - Location: {search_location} - LinkedIn: {search_linkedin}",
                    search_parameters={
                        'location': search_location,
                        'original_location': location,
                        'linkedin_only': search_linkedin,
                        'cv_based': True,
                        'source': 'cv_extraction'
                    },
                    results_count=len(all_jobs),
                    execution_time=search_time
                )
            except Exception as query_error:
                print(f"Erreur enregistrement requête: {query_error}")
            
            # Message informatif pour l'utilisateur
            if len(all_jobs) > 0:
                if len(all_jobs) < 5:
                    messages.info(request, 
                        f"Recherche réussie ! {len(all_jobs)} offre(s) trouvée(s). "
                        "Nombre limité par la charge du serveur - réessayez plus tard pour plus de résultats.")
                else:
                    messages.success(request, f"Recherche réussie ! {len(all_jobs)} offre(s) trouvée(s).")
            else:
                messages.warning(request, 
                    "Aucune offre trouvée pour cette recherche. "
                    "Essayez avec une autre localisation ou sans spécifier de lieu.")
            
        except Exception as e:
            messages.warning(request, f"Erreur lors de la recherche CV: {str(e)}")
            print(f"Erreur recherche CV: {e}")
    else:
        # Même sans recherche, inclure l'analyse CV
        results = {
            'cv_analysis': cv_analysis,
            'search_strategy': ''
        }
    
    # Pagination
    paginator = Paginator(all_jobs, 12)
    page_number = request.GET.get('page')
    jobs_page = paginator.get_page(page_number)
    
    context = {
        'jobs': jobs_page,
        'page_obj': jobs_page,
        'location': location,
        'search_linkedin': search_linkedin,
        'search_performed': search_performed,
        'total_results': len(all_jobs),
        'linkedin_count': len(results.get('linkedin_only', [])),
        'cv_analysis': cv_analysis,  # Toujours inclure l'analyse CV
        'search_strategy': results.get('search_strategy', ''),
        'has_cv_data': cv_analysis.get('has_cv_data', False),  # Toujours calculer has_cv_data
        'used_default_location': search_performed and not location.strip(),
        'cache_buster': int(time.time()),  # Aide à éviter les problèmes de cache
    }
    
    response = render(request, 'profiles/cv_based_job_search.html', context)
    
    # Headers pour éviter la mise en cache
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response