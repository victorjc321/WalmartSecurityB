from django.utils.timezone import now, timedelta
from product.models import SecurityLog


def detectar_ataque(user):
    ultimos_eventos = SecurityLog.objects.filter(
        user=user, timestamp__gte=now() - timedelta(minutes=5)
    ).order_by("-timestamp")[:20]

    eventos = list(ultimos_eventos.values_list("event", flat=True))

    riesgo = 0

    if eventos.count("LOGIN_FAILED") >= 5:
        return 100

    if eventos.count("LOGIN_FAILED") >= 3:
        riesgo += 40

    if "OTP_FAILED" in eventos:
        riesgo += 30

    if eventos.count("LOGIN_FAILED") >= 3 and "OTP_FAILED" in eventos:
        riesgo += 50

    if eventos.count("SESSION_EXPIRED") >= 2:
        riesgo += 20

    if len(eventos) >= 15:
        riesgo += 40

    return riesgo
