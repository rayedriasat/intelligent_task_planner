from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .services import user_has_pomodoro_access, user_has_ai_chat_access


def pomodoro_required(view_func):
    """Decorator to require Pomodoro subscription."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        if not user_has_pomodoro_access(request.user):
            messages.warning(
                request, 
                'You need a Pomodoro subscription to access this feature.'
            )
            return redirect(reverse('billing:subscribe') + '?feature=pomodoro')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def ai_chat_required(view_func):
    """Decorator to require AI Chat subscription."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        if not user_has_ai_chat_access(request.user):
            messages.warning(
                request, 
                'You need an AI Chat subscription to access this feature.'
            )
            return redirect(reverse('billing:subscribe') + '?feature=ai_chat')
        
        return view_func(request, *args, **kwargs)
    return wrapper


class PomodoroRequiredMixin:
    """Mixin to require Pomodoro subscription for class-based views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        if not user_has_pomodoro_access(request.user):
            messages.warning(
                request, 
                'You need a Pomodoro subscription to access this feature.'
            )
            return redirect(reverse('billing:subscribe') + '?feature=pomodoro')
        
        return super().dispatch(request, *args, **kwargs)


class AIChatRequiredMixin:
    """Mixin to require AI Chat subscription for class-based views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        
        if not user_has_ai_chat_access(request.user):
            messages.warning(
                request, 
                'You need an AI Chat subscription to access this feature.'
            )
            return redirect(reverse('billing:subscribe') + '?feature=ai_chat')
        
        return super().dispatch(request, *args, **kwargs)
