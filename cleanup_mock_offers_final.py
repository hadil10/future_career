#!/usr/bin/env python
"""
Nettoyage final des offres simulées (mock)
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from profiles.ai_models import ExternalJobOffer

def cleanup_mock_offers():
    """Nettoyer toutes les offres simulées"""
    print("=== NETTOYAGE DES OFFRES SIMULÉES ===\n")
    
    try:
        # 1. Identifier les offres simulées
        print("--- 1. Identification des offres simulées ---")
        
        mock_offers = ExternalJobOffer.objects.filter(external_id__icontains='mock')
        google_search_offers = ExternalJobOffer.objects.filter(external_url__icontains='google.com/search')
        example_offers = ExternalJobOffer.objects.filter(external_url__icontains='example.com')
        
        print(f"Offres avec 'mock' dans l'ID: {mock_offers.count()}")
        print(f"Offres avec URL Google Search: {google_search_offers.count()}")
        print(f"Offres avec URL example.com: {example_offers.count()}")
        
        # Afficher les détails des offres simulées
        print(f"\n--- 2. Détail des offres simulées ---")
        all_fake_offers = ExternalJobOffer.objects.filter(
            models.Q(external_id__icontains='mock') |
            models.Q(external_url__icontains='google.com/search') |
            models.Q(external_url__icontains='example.com')
        ).distinct()
        
        for offer in all_fake_offers:
            print(f"❌ {offer.title} - {offer.company_name}")
            print(f"   ID: {offer.external_id}")
            print(f"   URL: {offer.external_url}")
            print(f"   Source: {offer.source}")
            print()
        
        # 3. Supprimer les offres simulées
        print(f"--- 3. Suppression des offres simulées ---")
        total_to_delete = all_fake_offers.count()
        
        if total_to_delete > 0:
            print(f"Suppression de {total_to_delete} offres simulées...")
            deleted_count = all_fake_offers.delete()[0]
            print(f"✅ {deleted_count} offres simulées supprimées")
        else:
            print("✅ Aucune offre simulée trouvée")
        
        # 4. Vérifier les offres restantes
        print(f"\n--- 4. Vérification des offres restantes ---")
        remaining_offers = ExternalJobOffer.objects.all()
        real_offers = ExternalJobOffer.objects.filter(source='jsearch').exclude(
            models.Q(external_id__icontains='mock') |
            models.Q(external_url__icontains='google.com/search') |
            models.Q(external_url__icontains='example.com')
        )
        
        print(f"✅ Total offres restantes: {remaining_offers.count()}")
        print(f"✅ Offres réelles JSearch: {real_offers.count()}")
        
        # Exemples d'offres réelles restantes
        print(f"\n--- 5. Exemples d'offres réelles restantes ---")
        for offer in real_offers[:5]:
            print(f"✅ {offer.title} - {offer.company_name}")
            print(f"   Localisation: {offer.location}")
            print(f"   URL: {offer.external_url[:80]}...")
            print()
        
        print(f"=== NETTOYAGE TERMINÉ ===")
        print(f"✅ Base de données nettoyée")
        print(f"✅ Seules les offres réelles restent")
        print(f"✅ La recherche IA affichera maintenant uniquement des offres réelles")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Import Django Q pour les requêtes
    from django.db import models
    cleanup_mock_offers()