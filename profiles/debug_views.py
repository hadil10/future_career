"""
Vues de débogage pour tester l'affichage des icônes IA
"""
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

def debug_user_status(request):
    """
    Vue de débogage pour vérifier l'état de l'utilisateur
    """
    context = {
        'user_authenticated': request.user.is_authenticated,
        'user_type': getattr(request.user, 'user_type', None) if request.user.is_authenticated else None,
        'username': request.user.username if request.user.is_authenticated else None,
        'user_id': request.user.id if request.user.is_authenticated else None,
        'is_staff': request.user.is_staff if request.user.is_authenticated else None,
        'is_active': request.user.is_active if request.user.is_authenticated else None,
    }
    
    return JsonResponse(context)

def debug_template_context(request):
    """
    Vue pour tester le contexte des templates
    """
    return render(request, 'debug_template.html', {
        'debug_info': {
            'user_authenticated': request.user.is_authenticated,
            'user_type': getattr(request.user, 'user_type', None) if request.user.is_authenticated else None,
            'username': request.user.username if request.user.is_authenticated else None,
        }
    })