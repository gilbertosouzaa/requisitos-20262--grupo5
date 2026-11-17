from flask import Blueprint, request, redirect, url_for
from functools import wraps
from flask_login import current_user

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    """
    Decorator que protege rotas exigindo autenticação.
    Ao barrar o acesso, redireciona para /entrar?next=<url> e,
    após o login, retorna para essa página.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # Garante que o next leve à URL que o usuário tentou acessar
            return redirect(url_for('auth.login', next=request.full_path if request.query_string else request.path))
        return f(*args, **kwargs)
    return decorated_function


def requer_perfil(*perfis_permitidos):
    """
    RN11: Decorator que exige login e perfil específico (ex: 'admin' ou ['admin', 'professor']).
    Se o usuário não estiver autenticado, redireciona para o login com next.
    Se estiver autenticado mas com perfil diferente, retorna HTTP 403 com página de erro sem permissão.
    """
    if len(perfis_permitidos) == 1 and isinstance(perfis_permitidos[0], (list, tuple, set)):
        perfis = list(perfis_permitidos[0])
    else:
        perfis = list(perfis_permitidos)

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.full_path if request.query_string else request.path))
            if current_user.perfil not in perfis:
                from flask import render_template
                return render_template('auth/403.html'), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


from app.auth import routes  # noqa: E402, F401
