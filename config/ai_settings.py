"""
Configuration pour les services d'IA
"""
import os
from django.conf import settings

# Clés API pour les services externes
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '')
INDEED_API_KEY = os.environ.get('INDEED_API_KEY', '')

# Configuration des services IA
AI_SETTINGS = {
    'OPENAI': {
        'API_KEY': OPENAI_API_KEY,
        'MODEL': 'gpt-3.5-turbo',
        'MAX_TOKENS': 500,
        'TEMPERATURE': 0.7,
    },
    'INDEED': {
        'API_KEY': INDEED_API_KEY,
        'RAPIDAPI_KEY': RAPIDAPI_KEY,
        'BASE_URL': 'https://indeed12.p.rapidapi.com',
        'DEFAULT_LOCATION': 'France',
        'MAX_RESULTS': 20,
    },
    'RECOMMENDATIONS': {
        'MIN_COMPATIBILITY_SCORE': 20,
        'MAX_RECOMMENDATIONS': 10,
        'SKILL_WEIGHT': 0.70,
        'INTEREST_WEIGHT': 0.30,
    }
}

# Instructions pour obtenir les clés API
API_INSTRUCTIONS = {
    'OPENAI': """
    Pour obtenir une clé API OpenAI:
    1. Créez un compte sur https://platform.openai.com/
    2. Allez dans API Keys
    3. Créez une nouvelle clé secrète
    4. Ajoutez OPENAI_API_KEY=votre_clé dans votre fichier .env
    """,
    'RAPIDAPI': """
    Pour obtenir une clé RapidAPI (pour Indeed):
    1. Créez un compte sur https://rapidapi.com/
    2. Abonnez-vous à l'API Indeed: https://rapidapi.com/letscrape-6bRBa3QguO5/api/indeed12
    3. Copiez votre clé X-RapidAPI-Key
    4. Ajoutez RAPIDAPI_KEY=votre_clé dans votre fichier .env
    """
}

def get_ai_setting(service, key, default=None):
    """
    Récupère une configuration IA
    """
    return AI_SETTINGS.get(service, {}).get(key, default)

def is_service_available(service):
    """
    Vérifie si un service IA est disponible
    """
    if service == 'OPENAI':
        return bool(OPENAI_API_KEY)
    elif service == 'INDEED':
        return bool(RAPIDAPI_KEY)
    return False

def get_service_status():
    """
    Retourne le statut de tous les services IA
    """
    return {
        'openai': {
            'available': is_service_available('OPENAI'),
            'name': 'OpenAI GPT',
            'description': 'Recommandations intelligentes et analyse de profil'
        },
        'indeed': {
            'available': is_service_available('INDEED'),
            'name': 'Indeed API',
            'description': 'Recherche d\'offres d\'emploi externes'
        }
    }