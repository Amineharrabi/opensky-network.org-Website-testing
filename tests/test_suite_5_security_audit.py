import pytest

from tests.test_logger import get_logger, log_step, log_check
from utils.web_audit import head_or_get, security_headers

logger = get_logger(__name__)


def _missing_security_headers(headers: dict[str, str]) -> list[str]:
    missing: list[str] = []

    # Core baseline
    if "strict-transport-security" not in headers:
        missing.append("strict-transport-security")
    if headers.get("x-content-type-options", "").lower() != "nosniff":
        missing.append("x-content-type-options=nosniff")

    # Framing protections: either XFO or CSP frame-ancestors
    csp = headers.get("content-security-policy", "")
    if "x-frame-options" not in headers and "frame-ancestors" not in csp:
        missing.append("x-frame-options OR csp frame-ancestors")

    # Good practice headers (not strictly required, but useful findings)
    if "referrer-policy" not in headers:
        missing.append("referrer-policy")
    if "permissions-policy" not in headers:
        missing.append("permissions-policy")

    return missing


@pytest.mark.security
@pytest.mark.audit
def test_security_01_https_redirect(settings):
    log_step(logger, 1, "Checking HTTP->HTTPS redirect (best-effort)")
    http_url = settings.base_url.replace("https://", "http://").rstrip("/") + "/"
    try:
        resp = head_or_get(http_url, timeout=10)
    except Exception as exc:
        pytest.skip(f"Network blocked or request failed: {exc}")

    final = str(resp.url)
    log_check(logger, f"HTTP final URL: {final}")
    if settings.audit_strict:
        assert final.startswith("https://"), f"Expected HTTPS redirect, got {final}"


@pytest.mark.security
@pytest.mark.audit
@pytest.mark.parametrize("path", ["/", "/about", "/data", "/feed"])
def test_security_02_security_headers_public_pages(settings, path):
    url = settings.base_url.rstrip("/") + path
    log_step(logger, 1, f"Fetching headers: {url}")

    try:
        headers = security_headers(url, timeout=10)
    except Exception as exc:
        pytest.skip(f"Network blocked or request failed: {exc}")

    missing = _missing_security_headers(headers)
    if missing:
        logger.info(f"[FINDING] missing/weak headers on {url}: {missing}")
    else:
        log_check(logger, "Security headers look OK")

    if settings.audit_strict:
        assert not missing, f"Missing/weak security headers on {url}: {missing}"

