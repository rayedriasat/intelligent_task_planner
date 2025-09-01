from .services import user_has_pomodoro_access, user_has_ai_chat_access


def subscription_context(request):
    """Add subscription status to all templates."""
    context = {
        'has_pomodoro_subscription': False,
        'has_ai_chat_subscription': False,
    }
    
    if request.user.is_authenticated:
        context.update({
            'has_pomodoro_subscription': user_has_pomodoro_access(request.user),
            'has_ai_chat_subscription': user_has_ai_chat_access(request.user),
        })
    
    return context
