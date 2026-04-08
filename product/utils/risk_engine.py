from django.utils.timezone import now
from product.models import UserRiskProfile, FailedLoginAttempt, FailedTOTPAttempt


def get_client_ip(request):
    cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")
    if cf_ip:
        return cf_ip

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")


def calculate_risk(request, user):
    risk = 0

    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT")

    profile, _ = UserRiskProfile.objects.get_or_create(user=user)

    if profile.last_ip and profile.last_ip != ip:
        risk += 30

    if profile.last_user_agent and profile.last_user_agent != user_agent:
        risk += 40

    try:
        failed = FailedLoginAttempt.objects.get(ip=ip)
        if failed.attempts >= 3:
            risk += 30
    except FailedLoginAttempt.DoesNotExist:
        pass

    try:
        totp_failed = FailedTOTPAttempt.objects.get(user=user)
        if totp_failed.attempts >= 3:
            risk += 50
    except FailedTOTPAttempt.DoesNotExist:
        pass

    risk = min(risk, 100)

    profile.last_ip = ip
    profile.last_user_agent = user_agent
    profile.risk_score = risk
    profile.last_activity = now()
    profile.save()

    return risk
