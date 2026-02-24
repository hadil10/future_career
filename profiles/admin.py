# profiles/admin.py

from django.contrib import admin
from .models import (
    Profile, 
    Skill, 
    Interest, 
    AcademicResult, 
    UserSkillEvaluation, 
    UserInterestEvaluation,
    Formation
)

# Méthode d'enregistrement propre avec les classes de personnalisation

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_skills_count') # Affiche l'utilisateur et le nombre de compétences
    search_fields = ('user__username',)
    
    @admin.display(description='Nombre de compétences')
    def get_skills_count(self, obj):
        return obj.skills.count()

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_profiles_count', 'get_category')
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)
    
    @admin.display(description='Nombre de profils')
    def get_profiles_count(self, obj):
        return obj.profiles.count()
    
    @admin.display(description='Catégorie estimée')
    def get_category(self, obj):
        name_lower = obj.name.lower()
        if any(tech in name_lower for tech in ['python', 'java', 'html', 'css', 'javascript', 'sql', 'git', 'docker', 'aws', 'linux', 'api']):
            return '💻 Technique'
        elif any(mgmt in name_lower for mgmt in ['gestion', 'management', 'projet', 'leadership', 'scrum', 'agile']):
            return '📊 Gestion'
        elif any(comm in name_lower for comm in ['communication', 'présentation', 'négociation', 'relation']):
            return '🗣️ Communication'
        elif any(design in name_lower for design in ['design', 'graphique', 'ux', 'ui', 'photoshop', 'figma']):
            return '🎨 Design'
        else:
            return '📋 Autre'

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_profiles_count', 'get_domain')
    search_fields = ('name',)
    list_filter = ('name',)
    ordering = ('name',)
    
    @admin.display(description='Nombre de profils')
    def get_profiles_count(self, obj):
        return obj.profiles.count()
    
    @admin.display(description='Domaine estimé')
    def get_domain(self, obj):
        name_lower = obj.name.lower()
        if any(tech in name_lower for tech in ['intelligence', 'technologie', 'informatique', 'machine', 'cyber', 'blockchain']):
            return '💻 Technologie'
        elif any(biz in name_lower for biz in ['business', 'finance', 'marketing', 'entrepreneur', 'commerce']):
            return '💼 Business'
        elif any(creative in name_lower for creative in ['design', 'art', 'créativité', 'photo', 'musique']):
            return '🎨 Créativité'
        elif any(science in name_lower for science in ['science', 'recherche', 'médecine', 'physique', 'chimie']):
            return '🔬 Sciences'
        elif any(social in name_lower for social in ['éducation', 'social', 'ong', 'droit', 'psychologie']):
            return '🤝 Social'
        else:
            return '📋 Autre'

@admin.register(AcademicResult)
class AcademicResultAdmin(admin.ModelAdmin):
    list_display = ('profile', 'subject', 'grade', 'year')
    list_filter = ('profile__user__username', 'year', 'subject') # Filtre par nom d'utilisateur
    search_fields = ('subject',)

@admin.register(UserSkillEvaluation)
class UserSkillEvaluationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'skill', 'level')
    list_filter = ('profile__user__username', 'skill__name', 'level') # Filtre par nom

@admin.register(UserInterestEvaluation)
class UserInterestEvaluationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'interest', 'level')
    list_filter = ('profile__user__username', 'interest__name', 'level') # Filtre par nom

@admin.register(Formation)
class FormationAdmin(admin.ModelAdmin):
    list_display = ('title', 'school', 'level')
    search_fields = ('title', 'school')

# Import des modèles IA
from .ai_models import CVExtraction

@admin.register(CVExtraction)
class CVExtractionAdmin(admin.ModelAdmin):
    list_display = ('profile', 'extraction_date', 'is_processed', 'extraction_confidence', 'get_skills_count', 'get_experiences_count')
    list_filter = ('is_processed', 'extraction_method', 'extraction_date')
    search_fields = ('profile__user__username', 'extracted_name', 'extracted_email')
    readonly_fields = ('extraction_date', 'raw_text')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('profile', 'extraction_date', 'extraction_method', 'extraction_confidence', 'is_processed')
        }),
        ('Informations personnelles extraites', {
            'fields': ('extracted_name', 'extracted_email', 'extracted_phone', 'extracted_location')
        }),
        ('Résumé professionnel', {
            'fields': ('professional_summary',)
        }),
        ('Données structurées', {
            'fields': ('work_experiences', 'extracted_educations', 'extracted_skills', 'extracted_languages', 'extracted_projects', 'extracted_certifications'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('raw_text', 'processing_errors'),
            'classes': ('collapse',)
        })
    )
    
    @admin.display(description='Compétences extraites')
    def get_skills_count(self, obj):
        return len(obj.extracted_skills) if obj.extracted_skills else 0
    
    @admin.display(description='Expériences extraites')
    def get_experiences_count(self, obj):
        return len(obj.work_experiences) if obj.work_experiences else 0