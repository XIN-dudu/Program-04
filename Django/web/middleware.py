# Django/web/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.utils import timezone
import traceback

from .models import SystemLog
from .views import get_client_ip

class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        # 获取用户（如有）
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            user_obj = user
        else:
            # 你项目用 session 存用户名
            from .models import UserProfile
            username = request.session.get('username')
            user_obj = None
            if username:
                try:
                    user_obj = UserProfile.objects.get(username=username)
                except UserProfile.DoesNotExist:
                    pass

        # 记录异常日志
        SystemLog.objects.create(
            user=user_obj,
            level='error',
            action='系统异常',
            details=f"{str(exception)}\n{traceback.format_exc()}",
            ip_address=get_client_ip(request),
            timestamp=timezone.now()
        )

        # 返回统一的错误响应
        return JsonResponse({
            'msg': '服务器内部错误，请联系管理员。',
            'error': str(exception)
        }, status=500)
