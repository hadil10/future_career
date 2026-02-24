"""
Service d'extraction de données CV avec IA
"""
import os
import json
import PyPDF2
import docx
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from django.core.files.storage import default_storage
import openai
from .models import Profile, Skill, Interest
from .ai_models import CVExtraction

class CVExtractionService:
    """
    Service pour extraire les données des CV avec l'IA
    """
    
    def __init__(self):
        self.openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
    
    def extract_cv_data(self, profile: Profile) -> Optional[CVExtraction]:
        """
        Extrait les données du CV d'un profil
        """
        if not profile.cv:
            return None
        
        try:
            # Extraire le texte du CV
            cv_text = self._extract_text_from_cv(profile.cv)
            if not cv_text:
                return None
            
            # Analyser avec l'IA
            extracted_data = self._analyze_cv_with_ai(cv_text)
            
            # Créer ou mettre à jour l'extraction
            cv_extraction, created = CVExtraction.objects.get_or_create(
                profile=profile,
                defaults={
                    'raw_text': cv_text,
                    'extraction_method': 'openai_gpt' if self.openai_api_key else 'rule_based',
                    'extraction_confidence': extracted_data.get('confidence', 0.7)
                }
            )
            
            # Mettre à jour les données extraites
            cv_extraction.extracted_name = extracted_data.get('name', '')
            cv_extraction.extracted_email = extracted_data.get('email', '')
            cv_extraction.extracted_phone = extracted_data.get('phone', '')
            cv_extraction.extracted_location = extracted_data.get('location', '')
            cv_extraction.work_experiences = extracted_data.get('work_experiences', [])
            cv_extraction.extracted_educations = extracted_data.get('educations', [])
            cv_extraction.extracted_skills = extracted_data.get('skills', [])
            cv_extraction.extracted_languages = extracted_data.get('languages', [])
            cv_extraction.extracted_projects = extracted_data.get('projects', [])
            cv_extraction.extracted_certifications = extracted_data.get('certifications', [])
            cv_extraction.professional_summary = extracted_data.get('summary', '')
            cv_extraction.is_processed = True
            cv_extraction.processing_errors = ''
            cv_extraction.raw_text = cv_text
            
            cv_extraction.save()
            
            # Mettre à jour le profil avec les données extraites
            self._update_profile_from_extraction(profile, cv_extraction)
            
            return cv_extraction
            
        except Exception as e:
            # Enregistrer l'erreur
            cv_extraction, created = CVExtraction.objects.get_or_create(
                profile=profile,
                defaults={'processing_errors': str(e)}
            )
            if not created:
                cv_extraction.processing_errors = str(e)
                cv_extraction.save()
            
            return cv_extraction
    
    def _extract_text_from_cv(self, cv_file) -> str:
        """
        Extrait le texte d'un fichier CV (PDF, DOCX, DOC)
        """
        try:
            file_path = cv_file.path
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension == '.pdf':
                return self._extract_text_from_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._extract_text_from_docx(file_path)
            else:
                return ""
                
        except Exception as e:
            print(f"Erreur extraction texte CV: {e}")
            return ""
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extrait le texte d'un fichier PDF
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"Erreur extraction PDF: {e}")
            return ""
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """
        Extrait le texte d'un fichier DOCX
        """
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            print(f"Erreur extraction DOCX: {e}")
            return ""
    
    def _analyze_cv_with_ai(self, cv_text: str) -> Dict:
        """
        Analyse le texte du CV avec l'IA
        """
        if self.openai_api_key:
            return self._analyze_with_openai(cv_text)
        else:
            return self._analyze_with_rules(cv_text)
    
    def _analyze_with_openai(self, cv_text: str) -> Dict:
        """
        Analyse avec OpenAI GPT 
        """
        try:
            prompt = f"""
            Analysez ce CV et extrayez UNIQUEMENT les informations suivantes au format JSON :
            
            {{
                "skills": [
                    {{
                        "skill": "nom de la compétence technique",
                        "level": "niveau (Débutant/Intermédiaire/Avancé/Expert)",
                        "category": "catégorie (Programmation/Base de données/Framework/Outil/etc.)"
                    }}
                ],
                "educations": [
                    {{
                        "degree": "diplôme (ex: Master, Licence, BTS, etc.)",
                        "school": "établissement",
                        "year": "année d'obtention",
                        "field": "domaine d'études (ex: Informatique, Gestion, etc.)"
                    }}
                ],
                "confidence": 0.9
            }}
            
            INSTRUCTIONS IMPORTANTES :
            - Extrayez SEULEMENT les compétences techniques (programmation, logiciels, outils, technologies)
            - Ignorez les soft skills (communication, leadership, etc.)
            - Concentrez-vous sur les formations diplômantes uniquement
            - Soyez précis sur les niveaux de compétences
            - Limitez à 10 compétences maximum et 3 formations maximum
            
            CV à analyser :
            {cv_text}
            
            Répondez uniquement avec le JSON, sans texte supplémentaire.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Vous êtes un expert en analyse de CV. Extrayez UNIQUEMENT les compétences techniques et formations diplômantes au format JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            extracted_data = json.loads(result)
            
            # Ajouter les champs vides pour compatibilité
            return {
                "name": "",
                "email": "",
                "phone": "",
                "location": "",
                "summary": "",
                "work_experiences": [],
                "educations": extracted_data.get('educations', []),
                "skills": extracted_data.get('skills', []),
                "languages": [],
                "projects": [],
                "certifications": [],
                "confidence": extracted_data.get('confidence', 0.8)
            }
            
        except Exception as e:
            print(f"Erreur OpenAI: {e}")
            return self._analyze_with_rules(cv_text)
    
    def _analyze_with_rules(self, cv_text: str) -> Dict:
        """
        Analyse basique avec des règles 
        """
        import re
        
        # Recherche de compétences techniques courantes
        technical_skills = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'PHP', 'Ruby',
            'React', 'Angular', 'Vue.js', 'Node.js', 'Django', 'Flask', 'Spring',
            'HTML', 'CSS', 'SASS', 'Bootstrap', 'Tailwind',
            'SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite',
            'Git', 'Docker', 'Kubernetes', 'Jenkins', 'AWS', 'Azure', 'GCP',
            'Linux', 'Windows', 'MacOS', 'Ubuntu',
            'Photoshop', 'Illustrator', 'Figma', 'Sketch',
            'Excel', 'Word', 'PowerPoint', 'Office',
            'Machine Learning', 'AI', 'Data Science', 'TensorFlow', 'PyTorch'
        ]
        
        found_skills = []
        cv_lower = cv_text.lower()
        
        for skill in technical_skills:
            if skill.lower() in cv_lower:
                # Déterminer la catégorie
                category = "Technique"
                if skill in ['Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'PHP', 'Ruby']:
                    category = "Programmation"
                elif skill in ['React', 'Angular', 'Vue.js', 'Django', 'Flask', 'Spring']:
                    category = "Framework"
                elif skill in ['SQL', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis']:
                    category = "Base de données"
                elif skill in ['Git', 'Docker', 'AWS', 'Azure']:
                    category = "Outil"
                elif skill in ['Photoshop', 'Illustrator', 'Figma']:
                    category = "Design"
                
                found_skills.append({
                    "skill": skill,
                    "level": "Intermédiaire",
                    "category": category
                })
        
        # Recherche de formations avec regex plus précis
        education_patterns = [
            r'(Master|M1|M2|Master 1|Master 2).*?(\d{4})',
            r'(Licence|L3|Licence 3).*?(\d{4})',
            r'(BTS|DUT|BUT).*?(\d{4})',
            r'(Baccalauréat|Bac).*?(\d{4})',
            r'(Doctorat|PhD).*?(\d{4})',
            r'(Ingénieur|École d\'ingénieur).*?(\d{4})',
            r'(\d{4}[-:]?\d{4}):?\s*(Master|Licence|BTS|DUT|BUT|Bac)',
            r'(\d{4}):?\s*(Master|Licence|BTS|DUT|BUT|Bac).*?(Informatique|Gestion|Marketing|Ingénieur)',
        ]
        
        educations = []
        lines = cv_text.split('\n')
        
        # Recherche ligne par ligne
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Recherche avec patterns
            for pattern in education_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    if len(groups) >= 2:
                        # Déterminer le diplôme et l'année
                        if groups[0].isdigit():  # Année en premier
                            year = groups[0]
                            degree = groups[1]
                        else:  # Diplôme en premier
                            degree = groups[0]
                            year = groups[1] if len(groups) > 1 else "À déterminer"
                        
                        # Déterminer le domaine d'études
                        field = "À déterminer"
                        line_lower = line.lower()
                        if any(word in line_lower for word in ['informatique', 'computer', 'software', 'développement']):
                            field = "Informatique"
                        elif any(word in line_lower for word in ['gestion', 'management', 'business', 'commerce']):
                            field = "Gestion"
                        elif any(word in line_lower for word in ['marketing', 'communication', 'publicité']):
                            field = "Marketing"
                        elif any(word in line_lower for word in ['ingénieur', 'engineering', 'technique']):
                            field = "Ingénierie"
                        elif any(word in line_lower for word in ['économie', 'finance', 'comptabilité']):
                            field = "Économie"
                        
                        # Extraire l'école si possible
                        school = "À compléter"
                        if 'université' in line_lower:
                            school_match = re.search(r'université\s+([^,\n]+)', line, re.IGNORECASE)
                            if school_match:
                                school = f"Université {school_match.group(1).strip()}"
                        elif 'école' in line_lower:
                            school_match = re.search(r'école\s+([^,\n]+)', line, re.IGNORECASE)
                            if school_match:
                                school = f"École {school_match.group(1).strip()}"
                        
                        educations.append({
                            "degree": degree,
                            "school": school,
                            "year": year,
                            "field": field
                        })
                        break
            
            # Recherche simple par mots-clés si pas de match avec patterns
            if not educations:
                education_keywords = ['master', 'licence', 'bts', 'dut', 'but', 'bac', 'doctorat', 'ingénieur']
                if any(keyword in line.lower() for keyword in education_keywords):
                    # Recherche d'année dans la ligne
                    year_match = re.search(r'(\d{4})', line)
                    year = year_match.group(1) if year_match else "À déterminer"
                    
                    # Déterminer le type de diplôme
                    degree = "Formation"
                    for keyword in education_keywords:
                        if keyword in line.lower():
                            degree = keyword.capitalize()
                            break
                    
                    educations.append({
                        "degree": degree,
                        "school": "À compléter",
                        "year": year,
                        "field": "À déterminer"
                    })
        
        # Limiter les résultats
        found_skills = found_skills[:10]  # Max 10 compétences
        educations = educations[:3]       # Max 3 formations
        
        return {
            "name": "",
            "email": "",
            "phone": "",
            "location": "",
            "summary": "",
            "work_experiences": [],
            "educations": educations,
            "skills": found_skills,
            "languages": [],
            "projects": [],
            "certifications": [],
            "confidence": 0.6 if found_skills or educations else 0.3
        }
    
    def _update_profile_from_extraction(self, profile: Profile, extraction: CVExtraction):
        """
        Met à jour le profil avec les compétences extraites uniquement
        """
        try:
            # Ajouter uniquement les compétences techniques extraites
            for skill_data in extraction.extracted_skills:
                skill_name = skill_data.get('skill', '').strip()
                if skill_name:
                    # Créer ou récupérer la compétence
                    skill, created = Skill.objects.get_or_create(
                        name=skill_name,
                        defaults={'name': skill_name}
                    )
                    
                    # Ajouter la compétence au profil si elle n'existe pas déjà
                    if not profile.skill_evaluations.filter(skill=skill).exists():
                        from .models import UserSkillEvaluation
                        
                        # Déterminer le niveau basé sur l'extraction
                        level_mapping = {
                            'Débutant': 2,
                            'Intermédiaire': 3,
                            'Avancé': 4,
                            'Expert': 5
                        }
                        level = level_mapping.get(skill_data.get('level', 'Intermédiaire'), 3)
                        
                        # Créer l'évaluation de compétence
                        UserSkillEvaluation.objects.create(
                            profile=profile,
                            skill=skill,
                            level=level
                        )
            
            profile.save()
            print(f"✅ Profil mis à jour avec {len(extraction.extracted_skills)} compétences")
            
        except Exception as e:
            print(f"❌ Erreur mise à jour profil: {e}")
    
    def get_job_recommendations_from_cv(self, profile: Profile) -> List[Dict]:
        """
        Génère des recommandations d'emploi basées sur l'extraction CV
        """
        try:
            extraction = CVExtraction.objects.get(profile=profile)
            
            # Analyser les compétences et expériences
            skills = [skill['skill'] for skill in extraction.extracted_skills]
            experiences = extraction.work_experiences
            
            # Générer des recommandations basées sur les données extraites
            recommendations = []
            
            # Logique de recommandation basée sur les compétences
            if any('python' in skill.lower() for skill in skills):
                recommendations.append({
                    'title': 'Développeur Python',
                    'match_reason': 'Compétences Python détectées dans votre CV',
                    'confidence': 0.8
                })
            
            if any('web' in skill.lower() or 'html' in skill.lower() or 'css' in skill.lower() for skill in skills):
                recommendations.append({
                    'title': 'Développeur Web',
                    'match_reason': 'Compétences web détectées dans votre CV',
                    'confidence': 0.7
                })
            
            # Ajouter des recommandations basées sur l'expérience
            for exp in experiences:
                if 'développeur' in exp.get('title', '').lower():
                    recommendations.append({
                        'title': 'Développeur Senior',
                        'match_reason': f'Expérience en tant que {exp.get("title", "")}',
                        'confidence': 0.9
                    })
            
            return recommendations
            
        except CVExtraction.DoesNotExist:
            return []
        except Exception as e:
            print(f"Erreur recommandations CV: {e}")
            return []