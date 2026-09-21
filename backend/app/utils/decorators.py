from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from .response import fail


def role_required(*roles):
    """角色守卫：装饰需要特定角色的接口。"""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return fail(f"无权访问：需要 {' / '.join(roles)} 角色", 403, 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
