import socket
from app.core.targets import resolve_public


def analyze_dns(domain: str) -> dict:
    result = {
        "domain": domain,
        "dns_ok": False,
        "resolved_ip": None,
        "addresses": [],
        "has_ipv6": False,
        "error": None,
    }
    try:
        ips = resolve_public(domain, 443)
        infos = [(None, None, None, None, (address,)) for address in ips]
        addresses = []
        has_ipv6 = False
        for info in infos:
            address = info[4][0]
            if address not in addresses:
                addresses.append(address)
            if ":" in address:
                has_ipv6 = True
        result.update({
            "dns_ok": bool(addresses),
            "resolved_ip": addresses[0] if addresses else None,
            "addresses": addresses,
            "has_ipv6": has_ipv6,
        })
    except Exception as exc:
        result["error"] = str(exc)
    return result
