import ipaddress


def get_client_ip(request):
    cf_ip = request.META.get("HTTP_CF_CONNECTING_IP")

    if cf_ip:
        try:
            ipaddress.ip_address(cf_ip)
            return cf_ip
        except:
            pass

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
        try:
            ipaddress.ip_address(ip)
            return ip
        except:
            pass

    return request.META.get("REMOTE_ADDR")
