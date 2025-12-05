from functools import wraps
from django.contrib import messages
from django.shortcuts import redirect

def login_required_toast(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "❌ Необходимо войти в аккаунт")
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper