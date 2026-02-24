from django.core.management.base import BaseCommand
from profiles.models import Skill, Interest

class Command(BaseCommand):
    help = 'Ajoute des compétences et centres d\'intérêt de base'

    def handle(self, *args, **options):
        # Compétences techniques
        technical_skills = [
            'Python', 'JavaScript', 'Java', 'HTML/CSS', 'React', 'Django', 'Node.js',
            'SQL', 'MongoDB', 'Git', 'Docker', 'AWS', 'Linux', 'API REST'
        ]
        
        # Compétences de gestion
        management_skills = [
            'Gestion de projet', 'Leadership', 'Management d\'équipe', 'Planification stratégique',
            'Gestion budgétaire', 'Analyse des risques', 'Méthodologies Agile', 'Scrum'
        ]
        
        # Compétences de communication
        communication_skills = [
            'Communication orale', 'Rédaction', 'Présentation publique', 'Négociation',
            'Relations clients', 'Travail en équipe', 'Écoute active'
        ]
        
        # Compétences design
        design_skills = [
            'Design graphique', 'UX/UI Design', 'Photoshop', 'Illustrator', 'Figma',
            'Design thinking', 'Prototypage', 'Wireframing'
        ]
        
        # Autres compétences
        other_skills = [
            'Analyse de données', 'Marketing digital', 'SEO/SEM', 'Comptabilité',
            'Ressources humaines', 'Vente', 'Service client', 'Logistique'
        ]
        
        all_skills = technical_skills + management_skills + communication_skills + design_skills + other_skills
        
        for skill_name in all_skills:
            skill, created = Skill.objects.get_or_create(name=skill_name)
            if created:
                self.stdout.write(f'Compétence créée: {skill_name}')
        
        # Centres d'intérêt technologie
        tech_interests = [
            'Intelligence Artificielle', 'Machine Learning', 'Cybersécurité', 'Blockchain',
            'Internet des Objets (IoT)', 'Réalité Virtuelle', 'Développement mobile', 'Cloud Computing'
        ]
        
        # Centres d'intérêt business
        business_interests = [
            'Entrepreneuriat', 'Finance', 'Marketing', 'E-commerce', 'Stratégie d\'entreprise',
            'Innovation', 'Investissement', 'Consulting'
        ]
        
        # Centres d'intérêt créativité
        creative_interests = [
            'Design graphique', 'Photographie', 'Vidéographie', 'Arts visuels',
            'Écriture créative', 'Musique', 'Architecture', 'Mode'
        ]
        
        # Centres d'intérêt sciences
        science_interests = [
            'Recherche scientifique', 'Biotechnologie', 'Environnement', 'Énergie renouvelable',
            'Médecine', 'Physique', 'Chimie', 'Mathématiques'
        ]
        
        # Centres d'intérêt social
        social_interests = [
            'Éducation', 'Travail social', 'ONG et associations', 'Développement durable',
            'Droits humains', 'Politique publique', 'Psychologie', 'Sociologie'
        ]
        
        all_interests = tech_interests + business_interests + creative_interests + science_interests + social_interests
        
        for interest_name in all_interests:
            interest, created = Interest.objects.get_or_create(name=interest_name)
            if created:
                self.stdout.write(f'Centre d\'intérêt créé: {interest_name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Terminé! {len(all_skills)} compétences et {len(all_interests)} centres d\'intérêt ajoutés.'
            )
        )