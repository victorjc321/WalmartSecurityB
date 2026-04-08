from product.models import SecurityLog


def get_client_ip(request):
    cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
    if cf_ip:
        return cf_ip

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def log_security_event(request, event, user=None):
    try:
        ip = get_client_ip(request) if request else None
        user_agent = request.META.get("HTTP_USER_AGENT") if request else None

        SecurityLog.objects.create(
            user=user,
            event=event,
            ip=ip,
            user_agent=user_agent,
        )
    except Exception as e:
        print("Security log error:", e)
