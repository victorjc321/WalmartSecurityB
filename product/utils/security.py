import ipaddress

CLOUDFLARE_IPS = [
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22",
]


def is_cloudflare_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in ipaddress.ip_network(net) for net in CLOUDFLARE_IPS)
    except:
        return False


def get_client_ip(request):
    remote_addr = request.META.get("REMOTE_ADDR")

    if remote_addr and is_cloudflare_ip(remote_addr):
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

    return remote_addr
