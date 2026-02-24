from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView
from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.contrib import messages

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('user:login')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        """
        Cette méthode est appelée UNIQUEMENT si le formulaire est valide.
        """
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f'Bienvenue {user.username}! Votre compte a été créé avec succès.')
        return redirect('profiles:home')
    
    def form_invalid(self, form):
        """
        Cette méthode est appelée si le formulaire a des erreurs.
        """
        messages.error(self.request, 'Il y a des erreurs dans votre formulaire. Veuillez les corriger.')
        return super().form_invalid(form)

def user_redirect_view(request):
    if hasattr(request.user, 'company_profile'):
        return redirect('companies:dashboard') 
    elif hasattr(request.user, 'profile'):
        return redirect('profiles:profile-detail')
    return redirect('profiles:home')