from django.urls import path
from . import views
from profiles import ai_views

app_name = 'companies'

urlpatterns = [

    path('dashboard/', views.company_dashboard, name='dashboard'),
   
    path('offer/<int:offer_id>/applicants/', views.offer_applicants_view, name='offer-applicants'),

    path('offers/create/', views.create_job_offer, name='offer-create'),
    

    path('offers/<int:offer_id>/update/', views.update_job_offer, name='offer-update'),
    

    path('offers/<int:offer_id>/delete/', views.delete_job_offer, name='offer-delete'),
    
    # URLs IA pour les entreprises
    path('ai/', ai_views.company_ai_dashboard_view, name='ai-dashboard'),
    path('ai/recommendations/', ai_views.company_student_recommendations_view, name='student-recommendations'),
    path('ai/recommendations/<int:offer_id>/', ai_views.company_student_recommendations_view, name='student-recommendations-offer'),
]
