from __future__ import annotations
import ipaddress, socket
from yarl import URL

PRIVATE_NETS = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('fc00::/7'),
    ipaddress.ip_network('fe80::/10'),
]

def normalize(u: str) -> str:
    url = URL(u)
    if url.scheme not in {"http", "https"}:
        raise ValueError("Only http/https are allowed")
    # Drop fragments, normalize host lower
    url = url.with_fragment(None)
    if url.port in (80, 443):
        url = url.with_port(None)
    return str(url)

def same_scope(root: str, candidate: str, *, same_domain: bool, under_path: bool) -> bool:
    r, c = URL(root), URL(candidate)
    if same_domain and r.host != c.host:
        return False
    if under_path and not str(c).startswith(str(r)):
        return False
    return True

def guard_ssrf(host: str) -> None:
    # Resolve host and deny private/link-local
    try:
        _, _, addrs = socket.gethostbyname_ex(host)
    except Exception:
        # If DNS fails, let the fetcher error naturally; do not allow private by default
        return
    for a in addrs:
        try:
            ip = ipaddress.ip_address(a)
            if any(ip in net for net in PRIVATE_NETS):
                raise PermissionError(f"Blocked private/link-local address: {ip}")
        except ValueError:
            continue
