from django.utils.timezone import now
from datetime import timedelta
from product.models import UserRiskProfile, FailedLoginAttempt, FailedTOTPAttempt
from .security import get_client_ip


def calculate_risk(request, user):
    risk = 0

    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT")

    profile, _ = UserRiskProfile.objects.get_or_create(user=user)

    if profile.last_ip and profile.last_ip != ip:
        risk += 40

        if profile.last_user_agent != user_agent:
            risk += 30

    if profile.last_activity and (now() - profile.last_activity) < timedelta(minutes=5):
        if profile.last_ip != ip:
            risk += 30

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

    if risk < 80:
        profile.last_ip = ip
        profile.last_user_agent = user_agent

    profile.risk_score = risk
    profile.last_activity = now()
    profile.save()

    return risk
