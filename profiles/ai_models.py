"""
Modèles pour l'IA et les recommandations avancées
"""
from django.db import models
from django.contrib.auth import get_user_model
from .models import Profile, Skill, Interest
from companies.models import JobOffer

User = get_user_model()

class ExternalJobOffer(models.Model):
    """
    Modèle pour stocker les offres d'emploi externes (Indeed, etc.)
    """
    SOURCES = [
        ('jsearch', 'JSearch'),
        ('indeed', 'Indeed'),
        ('linkedin', 'LinkedIn'),
        ('glassdoor', 'Glassdoor'),
        ('other', 'Autre'),
    ]
    
    title = models.CharField(max_length=500, verbose_name="Titre du poste")
    company_name = models.CharField(max_length=300, verbose_name="Nom de l'entreprise")
    description = models.TextField(verbose_name="Description")
    location = models.CharField(max_length=300, blank=True, verbose_name="Localisation")
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Salaire minimum")
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Salaire maximum")
    
    # Métadonnées de la source
    source = models.CharField(max_length=20, choices=SOURCES, default='jsearch', verbose_name="Source")
    external_id = models.CharField(max_length=300, unique=True, verbose_name="ID externe")
    external_url = models.URLField(max_length=2000, verbose_name="URL externe")
    
    # Compétences extraites par IA
    extracted_skills = models.ManyToManyField(Skill, blank=True, verbose_name="Compétences extraites")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    class Meta:
        verbose_name = "Offre externe"
        verbose_name_plural = "Offres externes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.company_name} ({self.source})"

class AIRecommendation(models.Model):
    """
    Modèle pour stocker les recommandations générées par l'IA
    """
    RECOMMENDATION_TYPES = [
        ('job_to_student', 'Offre pour étudiant'),
        ('student_to_company', 'Étudiant pour entreprise'),
        ('external_job', 'Offre externe'),
    ]
    
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    
    # Relations
    student_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, null=True, blank=True)
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE, null=True, blank=True)
    external_job = models.ForeignKey(ExternalJobOffer, on_delete=models.CASCADE, null=True, blank=True)
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, null=True, blank=True)
    
    # Scores IA
    compatibility_score = models.FloatField(verbose_name="Score de compatibilité")
    skill_match_score = models.FloatField(verbose_name="Score compétences")
    interest_match_score = models.FloatField(verbose_name="Score intérêts")
    location_score = models.FloatField(default=0, verbose_name="Score localisation")
    salary_score = models.FloatField(default=0, verbose_name="Score salaire")
    
    # Métadonnées IA
    ai_model_version = models.CharField(max_length=50, default="v1.0")
    confidence_level = models.FloatField(verbose_name="Niveau de confiance")
    reasoning = models.TextField(blank=True, verbose_name="Raisonnement IA")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Recommandation IA"
        verbose_name_plural = "Recommandations IA"
        ordering = ['-compatibility_score', '-created_at']
    
    def __str__(self):
        return f"Recommandation {self.recommendation_type} - Score: {self.compatibility_score}%"

class AISearchQuery(models.Model):
    """
    Modèle pour stocker les requêtes de recherche IA
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query_text = models.TextField(verbose_name="Texte de la requête")
    search_parameters = models.JSONField(default=dict, verbose_name="Paramètres de recherche")
    
    # Résultats
    results_count = models.IntegerField(default=0)
    execution_time = models.FloatField(default=0.0, verbose_name="Temps d'exécution (secondes)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Requête de recherche IA"
        verbose_name_plural = "Requêtes de recherche IA"
        ordering = ['-created_at']

class CVExtraction(models.Model):
    """
    Modèle pour stocker les données extraites du CV par l'IA
    """
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='cv_extraction')
    
    # Informations personnelles extraites
    extracted_name = models.CharField(max_length=300, blank=True, verbose_name="Nom extrait")
    extracted_email = models.EmailField(blank=True, verbose_name="Email extrait")
    extracted_phone = models.CharField(max_length=20, blank=True, verbose_name="Téléphone extrait")
    extracted_location = models.CharField(max_length=300, blank=True, verbose_name="Localisation extraite")
    
    # Expériences professionnelles
    work_experiences = models.JSONField(default=list, verbose_name="Expériences professionnelles")
    # Format: [{"title": "Développeur", "company": "TechCorp", "duration": "2 ans", "description": "..."}]
    
    # Formations extraites
    extracted_educations = models.JSONField(default=list, verbose_name="Formations extraites")
    # Format: [{"degree": "Master", "school": "Université", "year": "2023", "field": "Informatique"}]
    
    # Compétences extraites
    extracted_skills = models.JSONField(default=list, verbose_name="Compétences extraites")
    # Format: [{"skill": "Python", "level": "Avancé", "category": "Programmation"}]
    
    # Langues
    extracted_languages = models.JSONField(default=list, verbose_name="Langues extraites")
    # Format: [{"language": "Anglais", "level": "Courant"}]
    
    # Projets et réalisations
    extracted_projects = models.JSONField(default=list, verbose_name="Projets extraits")
    # Format: [{"title": "Site web", "description": "...", "technologies": ["React", "Node.js"]}]
    
    # Certifications
    extracted_certifications = models.JSONField(default=list, verbose_name="Certifications extraites")
    # Format: [{"name": "AWS Certified", "issuer": "Amazon", "date": "2023"}]
    
    # Résumé professionnel
    professional_summary = models.TextField(blank=True, verbose_name="Résumé professionnel extrait")
    
    # Métadonnées d'extraction
    extraction_date = models.DateTimeField(auto_now_add=True)
    extraction_method = models.CharField(max_length=50, default="openai_gpt", verbose_name="Méthode d'extraction")
    extraction_confidence = models.FloatField(default=0, verbose_name="Confiance de l'extraction")
    raw_text = models.TextField(blank=True, verbose_name="Texte brut extrait")
    
    # Statut de l'extraction
    is_processed = models.BooleanField(default=False, verbose_name="Traité")
    processing_errors = models.TextField(blank=True, verbose_name="Erreurs de traitement")
    
    class Meta:
        verbose_name = "Extraction de CV"
        verbose_name_plural = "Extractions de CV"
    
    def __str__(self):
        return f"Extraction CV - {self.profile.user.username}"

class ProfileAnalysis(models.Model):
    """
    Analyse IA du profil étudiant
    """
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, related_name='ai_analysis')
    
    # Analyse des compétences
    skill_strengths = models.JSONField(default=list, verbose_name="Forces en compétences")
    skill_gaps = models.JSONField(default=list, verbose_name="Lacunes en compétences")
    recommended_skills = models.JSONField(default=list, verbose_name="Compétences recommandées")
    
    # Analyse des intérêts
    career_path_suggestions = models.JSONField(default=list, verbose_name="Suggestions de carrière")
    industry_matches = models.JSONField(default=list, verbose_name="Secteurs compatibles")
    
    # Scores globaux
    profile_completeness = models.FloatField(default=0, verbose_name="Complétude du profil")
    marketability_score = models.FloatField(default=0, verbose_name="Score d'employabilité")
    
    # Métadonnées
    last_analysis = models.DateTimeField(auto_now=True)
    analysis_version = models.CharField(max_length=20, default="v1.0")
    
    class Meta:
        verbose_name = "Analyse de profil IA"
        verbose_name_plural = "Analyses de profil IA"
    
    def __str__(self):
        return f"Analyse IA - {self.profile.user.username}"