from django.utils.timezone import now
from datetime import timedelta
from product.models import UserRiskProfile, FailedLoginAttempt, FailedTOTPAttempt
from .security import get_client_ip
from .ip_intelligence import check_ip_reputation
from product.models import BlockedIP


def calculate_risk(request, user):
    risk = 0

    ip = get_client_ip(request)
    user_agent = request.META.get("HTTP_USER_AGENT")

    profile, _ = UserRiskProfile.objects.get_or_create(user=user)

    if not request.session.get("ip_checked"):
        ip_data = check_ip_reputation(ip)
        request.session["ip_data"] = ip_data
        request.session["ip_checked"] = True
    else:
        ip_data = request.session.get("ip_data", {})

    if ip_data.get("tor"):
        return 100

    if ip_data.get("vpn"):
        risk += 30

    if ip_data.get("proxy"):
        risk += 40

    if ip_data.get("fraud_score", 0) > 70:
        risk += 50

    if profile.last_ip and profile.last_ip != ip:
        risk += 40

        if profile.last_user_agent != user_agent:
            risk += 30

    if profile.last_activity and (now() - profile.last_activity) < timedelta(minutes=5):
        if profile.last_ip != ip:
            risk += 30

    try:
        failed = (
            FailedLoginAttempt.objects.filter(ip=ip).order_by("-last_attempt").first()
        )
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

    if risk >= 90:
        BlockedIP.objects.update_or_create(
            ip=ip,
            defaults={
                "is_active": True,
                "blocked_until": now() + timedelta(minutes=30),
                "reason": "Alto riesgo detectado",
            },
        )

    return risk
