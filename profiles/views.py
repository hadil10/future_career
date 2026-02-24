from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseForbidden, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import ProfileUpdateForm, AcademicResultForm

from .models import (
    Profile, 
    Skill, 
    Interest, 
    UserSkillEvaluation, 
    UserInterestEvaluation, 
    AcademicResult
 )
from companies.models import JobOffer, Application
from .recommender import get_job_recommendations

def get_or_create_profile(user):
    """
    Fonction utilitaire pour récupérer ou créer un profil utilisateur
    """
    try:
        return Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        return Profile.objects.create(user=user)
def home_view(request):
    return render(request, 'home.html', {})

@login_required 
def profile_view(request):
    profile = get_or_create_profile(request.user)
    context = {'profile': profile}
    return render(request, 'profiles/profile_detail.html', context)
    
@login_required
def profile_update_view(request):
    # Essayer de récupérer le profil, le créer s'il n'existe pas
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Créer automatiquement un profil pour l'utilisateur
        profile = Profile.objects.create(user=request.user)
        messages.info(request, 'Un profil a été créé pour vous.')
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save() 
            messages.success(request, 'Votre profil a été mis à jour avec succès !')
            return redirect('profiles:profile-detail') # Utiliser le nom de l'URL est plus robuste
    else:
        form = ProfileUpdateForm(instance=profile)
    context = {'form': form}
    return render(request, 'profiles/profile_form.html', context)


@login_required
def questionnaire_view(request):
    # Essayer de récupérer le profil, le créer s'il n'existe pas
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        # Créer automatiquement un profil pour l'utilisateur
        profile = Profile.objects.create(user=request.user)
        messages.info(request, 'Un profil a été créé pour vous.')
    
    all_skills = Skill.objects.all()
    all_interests = Interest.objects.all()

    if request.method == 'POST':
        for skill in all_skills:
            level = request.POST.get(f'skill_{skill.id}')
            if level:
                UserSkillEvaluation.objects.update_or_create(
                    profile=profile, skill=skill, defaults={'level': int(level)}
                )
        for interest in all_interests:
            level = request.POST.get(f'interest_{interest.id}')
            if level:
                UserInterestEvaluation.objects.update_or_create(
                    profile=profile, interest=interest, defaults={'level': int(level)}
                )
        messages.success(request, 'Votre questionnaire a été enregistré avec succès !')
        return redirect('profiles:profile-detail')

    context = {
        'all_skills': all_skills,
        'all_interests': all_interests,
        'existing_skill_evals': {eval.skill.id: eval.level for eval in profile.skill_evaluations.all()},
        'existing_interest_evals': {eval.interest.id: eval.level for eval in profile.interest_evaluations.all()},
        'skill_levels': UserSkillEvaluation.LEVEL_CHOICES,
        'interest_levels': UserInterestEvaluation.INTEREST_CHOICES,
    }
    return render(request, 'profiles/questionnaire.html', context)
@login_required
def recommendations_view(request):
    profile = get_or_create_profile(request.user)
    recommendations = get_job_recommendations(profile)
    
    # Pagination des recommandations
    paginator = Paginator(recommendations, 10)  # 10 recommandations par page
    page_number = request.GET.get('page')
    
    try:
        page_obj = paginator.get_page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.get_page(1)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)
    
    context = {
        'recommendations': page_obj,
        'page_obj': page_obj,
        'total_recommendations': len(recommendations)
    }
    
    return render(request, 'profiles/recommendations.html', context)
@login_required
def job_detail_view(request, job_id):
    
    offer = get_object_or_404(JobOffer, id=job_id, is_active=True)
    has_applied = False

    
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
     
        student_profile = request.user.profile
        has_applied = Application.objects.filter(
            student=student_profile,
            job_offer=offer
        ).exists()

    
    context = {
        'offer': offer,
        'has_applied': has_applied, 
    }
    return render(request, 'profiles/job_detail.html', context)
@login_required
def interest_questionnaire_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    interests = Interest.objects.all()

    if request.method == 'POST':
        for interest in interests:
            level = request.POST.get(f'interest_{interest.id}')
            if level:

                UserInterestEvaluation.objects.update_or_create(
                    profile=profile,
                    interest=interest,
                    defaults={'level': int(level)}
                )

        return redirect('profiles:recommendations')

    existing_evaluations = {eval.interest.id: eval.level for eval in profile.interest_evaluations.all()}
    
    context = {
        'interests': interests,
        'existing_evaluations': existing_evaluations,
    }
    return render(request, 'profiles/interest_questionnaire.html', context)
@login_required
def redirect_on_login_view(request):
    if request.user.user_type == 'company':
        return redirect('companies:dashboard')
    else:
        return redirect('profiles:home')
@login_required
def add_academic_result_view(request):
    profile = get_object_or_404(Profile, user=request.user)

    if request.method == 'POST':
        form = AcademicResultForm(request.POST)
        if form.is_valid():
            try:
                result = form.save(commit=False)
                result.profile = profile
                result.save()
                messages.success(request, 'Résultat académique ajouté avec succès !')
                return redirect('profiles:profile-detail')
            except IntegrityError:
                messages.error(request, 'Vous avez deja ajouté un résultat académique pour cette matière.')
    else:
        form = AcademicResultForm()
    existing_results = profile.academic_results.all().order_by('-year', 'subject')    

    context = {
        'form': form,
        'results': existing_results
    }
    return render(request, 'profiles/academic_results.html', context)
@login_required
def delete_academic_result(request, result_id):
    result = get_object_or_404(AcademicResult, id=result_id)

    if result.profile.user != request.user:
        return HttpResponseForbidden("Vous n'êtes pas autorisé à supprimer ce résultat.")
    if request.method == 'POST':
        result.delete()
        messages.success(request, 'Résultat académique supprimé avec succès !')
    return redirect('profiles:profile-detail')
@login_required
def update_academic_result(request, result_id):
    result = get_object_or_404(AcademicResult, id=result_id)

    if request.method == 'POST':
        form = AcademicResultForm(request.POST, instance=result)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Résultat académique mis à jour avec succès !')
                return redirect('profiles:profile-detail')
            except IntegrityError:
                messages.error(request, 'Vous avez déjà un résultat académique pour cette matière et cette année.')
    else:
        form = AcademicResultForm(instance=result)

    context = {
        'form': form,
        'result_id': result_id
    }
    return render(request, 'profiles/academic_result_form.html', context)

# =======================================================
#  POUR LISTER TOUTES LES OFFRES D'EMPLOI
# =======================================================
@login_required
def job_offer_list_view(request):
    """
    Affiche la liste de toutes les offres d'emploi actives avec pagination.
    Peut être triée par priorité selon le profil de l'utilisateur.
    """
    # Récupérer le paramètre de tri
    sort_by = request.GET.get('sort', 'date')  # 'date' ou 'priority'
    
    offers_list = JobOffer.objects.filter(is_active=True).select_related('company').order_by('-created_at')
    
    # Si l'utilisateur demande un tri par priorité
    if sort_by == 'priority':
        profile = get_or_create_profile(request.user)
        
        # Utiliser le système de recommandation pour calculer les scores
        recommendations = get_job_recommendations(profile)
        
        # Extraire les offres avec leurs scores
        offers_with_scores = []
        scored_offer_ids = []
        
        for reco in recommendations:
            offers_with_scores.append({
                'offer': reco['offer'],
                'score': reco['score'],
                'skill_score': reco['skill_score'],
                'interest_score': reco['interest_score']
            })
            scored_offer_ids.append(reco['offer'].id)
        
        # Ajouter les offres non scorées (score 0) à la fin
        unscored_offers = offers_list.exclude(id__in=scored_offer_ids)
        for offer in unscored_offers:
            offers_with_scores.append({
                'offer': offer,
                'score': 0,
                'skill_score': 0,
                'interest_score': 0
            })
        
        # Pagination des offres avec scores
        paginator = Paginator(offers_with_scores, 12)
        page_number = request.GET.get('page')
        
        try:
            offers_page = paginator.get_page(page_number)
        except PageNotAnInteger:
            offers_page = paginator.get_page(1)
        except EmptyPage:
            offers_page = paginator.get_page(paginator.num_pages)
        
        context = {
            'offers': offers_page,
            'page_obj': offers_page,
            'total_offers': len(offers_with_scores),
            'sort_by': sort_by,
            'show_scores': True
        }
    else:
        # Tri par date (comportement par défaut)
        paginator = Paginator(offers_list, 12)
        page_number = request.GET.get('page')
        
        try:
            offers = paginator.get_page(page_number)
        except PageNotAnInteger:
            offers = paginator.get_page(1)
        except EmptyPage:
            offers = paginator.get_page(paginator.num_pages)
        
        context = {
            'offers': offers,
            'page_obj': offers,
            'total_offers': offers_list.count(),
            'sort_by': sort_by,
            'show_scores': False
        }
    
    return render(request, 'profiles/offers_list.html', context)
# =======================================================
#  POUR LE DÉTAIL D'UNE OFFRE D'EMPLOI
# =======================================================
@login_required
def job_offer_detail_view(request, offer_id):
    """
    Affiche les détails d'une offre d'emploi spécifique.
    """
    offer = get_object_or_404(JobOffer, id=offer_id, is_active=True)
    
    context = {
        'offer': offer
    }
    
    return render(request, 'profiles/offer_detail.html', context)   

# =======================================================
#  POUR POSTULER À UNE OFFRE
# =======================================================
@login_required
def apply_for_offer(request, job_id):
    if request.user.user_type != 'student':
        messages.error(request, "Seuls les étudiants peuvent postuler aux offres.")
        return redirect('profiles:home')

    if request.method == 'POST':
        job_offer = get_object_or_404(JobOffer, id=job_id)
        student_profile = get_object_or_404(Profile, user=request.user)

        try:

            Application.objects.create(
                student=student_profile, 
                job_offer=job_offer
            )
            messages.success(request, f"Votre candidature pour '{job_offer.title}' a été envoyée avec succès !")
        
        except IntegrityError:

            messages.warning(request, "Vous avez déjà postulé à cette offre.")


        return redirect('profiles:job-detail', job_id=job_id)
    return redirect('profiles:job-detail', job_id=job_id)
# =======================================================
#  LE PROFIL PUBLIC (consultable par les entreprises)
# =======================================================
@login_required
def public_profile_detail_view(request, profile_id):
    """
    Affiche une version publique du profil d'un étudiant.
    Accessible par les entreprises qui ont reçu une candidature.
    """

    if not hasattr(request.user, 'company_profile'):
        return HttpResponseForbidden("Accès réservé aux entreprises.")

 
    profile = get_object_or_404(Profile, id=profile_id)
    
  
    context = {
        'profile': profile,
    }

    return render(request, 'profiles/profile_detail.html', context)