from django.urls import path
from django.shortcuts import render
from .views import (
    home_view,
    profile_view, 
    profile_update_view, 
    questionnaire_view, 
    recommendations_view, 
    interest_questionnaire_view,
    add_academic_result_view,
    delete_academic_result,
    update_academic_result,
    job_offer_list_view,
    job_detail_view,
    apply_for_offer,  

)
from . import views
from . import ai_views

def ai_diagnostic_view(request):
    return render(request, 'ai_diagnostic.html')

def test_ai_icons_view(request):
    return render(request, 'test_ai_icons.html')

def test_ai_visibility_view(request):
    return render(request, 'test_ai_visibility.html')

def simple_test_view(request):
    from django.http import HttpResponse
    return HttpResponse("Simple test view works!")

def simple_ai_test_view(request):
    from django.http import HttpResponse
    return HttpResponse("Simple AI test view works!")

def test_ai_search_view(request):
    return render(request, 'test_ai_search.html')

def diagnostic_simple_view(request):
    return render(request, 'diagnostic_simple.html')

app_name = 'profiles'

urlpatterns = [
    
    path('', home_view, name='home'),
    
    path('profile/', views.profile_view, name='profile-detail'),
    path('profile/update/', views.profile_update_view, name='profile-update'),
    

    path('profile/public/<int:profile_id>/', views.public_profile_detail_view, name='profile-detail-public'),

    path('questionnaire/', views.questionnaire_view, name='questionnaire'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    

    path('academic-results/add/', views.add_academic_result_view, name='add-academic-result'),
    path('academic-results/<int:result_id>/update/', views.update_academic_result, name='update-academic-result'),
    path('academic-results/<int:result_id>/delete/', views.delete_academic_result, name='delete-academic-result'),


    path('offers/', views.job_offer_list_view, name='offer-list'),
    path('offers/<int:job_id>/', views.job_detail_view, name='job-detail'),
    path('offers/<int:job_id>/apply/', views.apply_for_offer, name='offer-apply'),
    
    # URLs IA
    path('ai/', ai_views.ai_dashboard_view, name='ai-dashboard'),
    path('ai/search/', ai_views.ai_job_search_view, name='ai-job-search'),
    path('ai/career-guidance/', ai_views.ai_career_guidance_view, name='ai-career-guidance'),
    path('ai/refresh-analysis/', ai_views.refresh_profile_analysis_view, name='refresh-profile-analysis'),
    path('ai/search-history/', ai_views.ai_search_history_view, name='ai-search-history'),
    path('ai/instant-recommendations/', ai_views.ai_instant_recommendations_view, name='ai-instant-recommendations'),
    path('external-jobs/<int:job_id>/', ai_views.external_job_detail_view, name='external-job-detail'),
    
    # URLs extraction CV
    path('cv/extract/', ai_views.extract_cv_data_view, name='extract-cv-data'),
    path('cv/status/', ai_views.cv_extraction_status_view, name='cv-extraction-status'),
    path('cv/results/', ai_views.cv_extraction_results_view, name='cv-extraction-results'),
    path('cv/refresh/', ai_views.refresh_cv_extraction_view, name='refresh-cv-extraction'),
    path('cv/demo/', lambda request: render(request, 'profiles/cv_extraction_demo.html'), name='cv-extraction-demo'),
    path('cv/job-search/', ai_views.cv_based_job_search_view, name='cv-based-job-search'),
    
    # URLs diagnostic
    path('diagnostic/external-jobs/', ai_views.external_jobs_diagnostic_view, name='external-jobs-diagnostic'),
    path('cleanup-external-jobs/', ai_views.cleanup_external_jobs_view, name='cleanup-external-jobs'),
    
    # Page de test pour les icônes IA
    path('test-ai-icons/', test_ai_icons_view, name='test-ai-icons'),
    path('test-ai-visibility/', test_ai_visibility_view, name='test-ai-visibility'),
    
    # Pages de débogage
    path('debug/user-status/', lambda request: __import__('profiles.debug_views', fromlist=['debug_user_status']).debug_user_status(request), name='debug-user-status'),
    path('debug/template/', lambda request: __import__('profiles.debug_views', fromlist=['debug_template_context']).debug_template_context(request), name='debug-template'),
    path('debug/ai-diagnostic/', ai_diagnostic_view, name='ai-diagnostic'),
    path('debug/simple-test/', simple_test_view, name='simple-test'),
    path('diagnostic/', diagnostic_simple_view, name='diagnostic-simple'),
    path('test-search/', test_ai_search_view, name='test-ai-search'),
]