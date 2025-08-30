from functools import wraps
from flask import session, redirect, url_for

def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "role" not in session or session.get("role") not in roles:
                return redirect(url_for("login"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator