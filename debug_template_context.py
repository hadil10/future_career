#!/usr/bin/env python
"""
Debug du contexte du template
"""
import os
import django
from django.test import Client
from django.contrib.auth import get_user_model

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def debug_template_context():
    print("=== Debug contexte template ===")
    
    # Récupérer un utilisateur étudiant
    User = get_user_model()
    student_user = User.objects.filter(user_type='student').first()
    
    # Créer un client et se connecter
    client = Client()
    client.force_login(student_user)
    
    # Test sans paramètres
    print(f"\n--- Test sans paramètres ---")
    response = client.get('/ai/search/')
    
    if hasattr(response, 'context') and response.context:
        context = response.context
        print(f"search_performed: {context.get('search_performed')}")
        print(f"total_results: {context.get('total_results')}")
        print(f"external_count: {context.get('external_count')}")
        print(f"internal_count: {context.get('internal_count')}")
        
        jobs = context.get('jobs', [])
        print(f"Nombre de jobs: {len(jobs)}")
        
        if hasattr(jobs, 'object_list'):
            print(f"Jobs object_list: {len(jobs.object_list)}")
    else:
        print("Pas de contexte disponible")
    
    # Examiner le contenu HTML
    content = response.content.decode('utf-8')
    
    # Chercher des indicateurs spécifiques
    if 'class="card h-100 shadow-sm border-primary"' in content:
        print("❌ Cartes d'offres externes trouvées dans le HTML")
    
    if 'class="card h-100 shadow-sm border-success"' in content:
        print("❌ Cartes d'offres internes trouvées dans le HTML")
    
    if 'Recherche Intelligente d\'Offres' in content and 'Utilisez notre IA' in content:
        print("✓ Message d'accueil trouvé")
    
    # Compter les occurrences de certains éléments
    card_count = content.count('class="card h-100')
    print(f"Nombre de cartes trouvées: {card_count}")

if __name__ == "__main__":
    debug_template_context()