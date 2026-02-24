from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Company, JobOffer, Application
from .forms import JobOfferForm 
from profiles.models import Skill


def company_required(view_func ):
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'company_profile'):
            return HttpResponseForbidden("Accès réservé aux profils d'entreprise.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# =======================================================
# LE TABLEAU DE BORD DE L'ENTREPRISE 
# =======================================================
@company_required
def company_dashboard(request):
    """
    Affiche le tableau de bord de l'entreprise avec la liste de ses offres paginées.
    C'est la page principale pour une entreprise.
    """
    company_profile = get_object_or_404(Company, user=request.user)
    job_offers_list = company_profile.job_offers.all().order_by('-created_at')
    
    # Pagination des offres
    paginator = Paginator(job_offers_list, 8)  # 8 offres par page
    page_number = request.GET.get('page')
    
    try:
        job_offers = paginator.get_page(page_number)
    except PageNotAnInteger:
        job_offers = paginator.get_page(1)
    except EmptyPage:
        job_offers = paginator.get_page(paginator.num_pages)
    
    context = {
        'company': company_profile,
        'offers': job_offers,
        'page_obj': job_offers,
        'total_offers': job_offers_list.count()
    }
    return render(request, 'companies/dashboard.html', context)

# =======================================================
# LA VUE POUR VOIR LES CANDIDATS 
# =======================================================
@company_required
def offer_applicants_view(request, offer_id):
    """
    Affiche la liste paginée de tous les étudiants qui ont postulé à une offre spécifique.
    """
    # On récupère l'offre, en s'assurant qu'elle appartient bien à l'entreprise connectée.
    offer = get_object_or_404(JobOffer, id=offer_id, company__user=request.user)
    
    # On récupère toutes les candidatures pour cette offre.
    applicants_list = Application.objects.filter(job_offer=offer).select_related('student__user').order_by('-applied_at')
    
    # Pagination des candidatures
    paginator = Paginator(applicants_list, 15)  # 15 candidatures par page
    page_number = request.GET.get('page')
    
    try:
        applicants = paginator.get_page(page_number)
    except PageNotAnInteger:
        applicants = paginator.get_page(1)
    except EmptyPage:
        applicants = paginator.get_page(paginator.num_pages)
    
    context = {
        'offer': offer,
        'applicants': applicants,
        'page_obj': applicants,
        'total_applicants': applicants_list.count()
    }
    return render(request, 'companies/offer_applicants.html', context)

# =======================================================
# GESTION DES OFFRES D'EMPLOI 
# =======================================================
@company_required
def create_job_offer(request):
    company_profile = get_object_or_404(Company, user=request.user)
    if request.method == 'POST':
        form = JobOfferForm(request.POST)
        if form.is_valid():
           
            job_offer = form.save(commit=False)
            job_offer.company = company_profile
            job_offer.save()

            # gère les compétences manuellement 
            skills_str = form.cleaned_data.get('required_skills', '')
            skill_names = [name.strip() for name in skills_str.split(',') if name.strip()]
            
            job_offer.required_skills.clear() 
            for name in skill_names:
                skill, created = Skill.objects.get_or_create(name__iexact=name, defaults={'name': name})
                job_offer.required_skills.add(skill)

            messages.success(request, "L'offre d'emploi a été créée avec succès.")
            return redirect('companies:dashboard')
    else:
        form = JobOfferForm()

    context = {'form': form, 'form_title': "Créer une nouvelle offre"}
    return render(request, 'companies/job_offer_form.html', context)


# =======================================================
# MODIFIER UNE OFFRE D'EMPLOI
# =======================================================
@company_required
def update_job_offer(request, offer_id):
    offer = get_object_or_404(JobOffer, id=offer_id, company__user=request.user)
    
    if request.method == 'POST':
        form = JobOfferForm(request.POST, instance=offer)
        if form.is_valid():
            
            updated_offer = form.save(commit=False)
            updated_offer.save()

            #  gère les compétences manuellement
            skills_str = form.cleaned_data.get('required_skills', '')
            skill_names = [name.strip() for name in skills_str.split(',') if name.strip()]
            
            updated_offer.required_skills.clear() 
            for name in skill_names:
                skill, created = Skill.objects.get_or_create(name__iexact=name, defaults={'name': name})
                updated_offer.required_skills.add(skill)

            messages.success(request, "L'offre d'emploi a été mise à jour avec succès.")
            return redirect('companies:dashboard')
    else:
        current_skills = offer.required_skills.all()
        # On les transforme en une chaîne de caractères : "Python, Java, SEO"
        skills_str = ", ".join([skill.name for skill in current_skills])
        form = JobOfferForm(instance=offer, initial={'required_skills': skills_str})

    context = {'form': form, 'form_title': f"Modifier l'offre : {offer.title}"}
    return render(request, 'companies/job_offer_form.html', context)
# =======================================================
# SUPPRIMER UNE OFFRE D'EMPLOI
# =======================================================
@company_required
def delete_job_offer(request, offer_id):
    """
    Supprime une offre d'emploi.
    """
    offer = get_object_or_404(JobOffer, id=offer_id, company__user=request.user)
    
    if request.method == 'POST':
        offer_title = offer.title
        offer.delete()
        messages.success(request, f"L'offre '{offer_title}' a été supprimée avec succès.")
        return redirect('companies:dashboard')
    
    context = {'offer': offer}
    return render(request, 'companies/confirm_delete_offer.html', context)
