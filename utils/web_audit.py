from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests


@dataclass(frozen=True)
class UrlCheckResult:
    url: str
    ok: bool
    status_code: int | None
    final_url: str | None
    error: str | None
    elapsed_ms: float | None


def is_http_url(url: str) -> bool:
    try:
        return urlparse(url).scheme in ("http", "https")
    except Exception:
        return False


def is_internal_url(base_url: str, url: str) -> bool:
    try:
        base = urlparse(base_url)
        target = urlparse(url)
        return (target.scheme in ("http", "https")) and (target.netloc == base.netloc)
    except Exception:
        return False


def normalize_url(base_url: str, url: str) -> str | None:
    if not url:
        return None
    url = url.strip()
    if url.startswith(("mailto:", "tel:", "javascript:", "#")):
        return None
    return urljoin(base_url, url)


def head_or_get(url: str, timeout: float = 10.0) -> requests.Response:
    try:
        return requests.head(url, allow_redirects=True, timeout=timeout)
    except requests.RequestException:
        # Some servers block HEAD; fall back to GET (small timeout, no streaming).
        return requests.get(url, allow_redirects=True, timeout=timeout)


def check_urls(
    urls: list[str],
    *,
    timeout: float = 10.0,
    max_urls: int = 40,
    delay_s: float = 0.0,
    require_https: bool = False,
) -> list[UrlCheckResult]:
    results: list[UrlCheckResult] = []
    for idx, url in enumerate(urls[:max_urls]):
        if require_https and urlparse(url).scheme != "https":
            results.append(
                UrlCheckResult(
                    url=url,
                    ok=False,
                    status_code=None,
                    final_url=None,
                    error="non-https",
                    elapsed_ms=None,
                )
            )
            continue

        start = time.time()
        try:
            resp = head_or_get(url, timeout=timeout)
            elapsed_ms = (time.time() - start) * 1000.0
            results.append(
                UrlCheckResult(
                    url=url,
                    ok=resp.status_code < 400,
                    status_code=resp.status_code,
                    final_url=str(resp.url),
                    error=None,
                    elapsed_ms=elapsed_ms,
                )
            )
        except requests.RequestException as exc:
            elapsed_ms = (time.time() - start) * 1000.0
            results.append(
                UrlCheckResult(
                    url=url,
                    ok=False,
                    status_code=None,
                    final_url=None,
                    error=str(exc),
                    elapsed_ms=elapsed_ms,
                )
            )

        if delay_s and idx < max_urls - 1:
            time.sleep(delay_s)

    return results


def collect_dom_urls(driver, *, base_url: str) -> dict[str, list[str]]:
    """Collect URLs from the current DOM via JavaScript.

    Returns dict keys: links, scripts, stylesheets, images.
    """
    script = """
    const abs = (u) => {
      try { return new URL(u, document.baseURI).toString(); } catch (e) { return null; }
    };
    const uniq = (arr) => Array.from(new Set(arr.filter(Boolean)));

    const links = uniq(Array.from(document.querySelectorAll('a[href]')).map(a => abs(a.getAttribute('href'))));
    const scripts = uniq(Array.from(document.querySelectorAll('script[src]')).map(s => abs(s.getAttribute('src'))));
    const stylesheets = uniq(Array.from(document.querySelectorAll('link[rel=\"stylesheet\"][href]')).map(l => abs(l.getAttribute('href'))));
    const images = uniq(Array.from(document.querySelectorAll('img[src]')).map(i => abs(i.getAttribute('src'))));
    return {links, scripts, stylesheets, images};
    """
    raw = driver.execute_script(script) or {}
    out: dict[str, list[str]] = {k: [] for k in ("links", "scripts", "stylesheets", "images")}
    for key in out:
        vals = raw.get(key) or []
        normalized: list[str] = []
        for v in vals:
            nv = normalize_url(base_url, str(v))
            if nv:
                normalized.append(nv)
        out[key] = sorted(set(normalized))
    return out


def security_headers(url: str, timeout: float = 10.0) -> dict[str, str]:
    resp = head_or_get(url, timeout=timeout)
    return {k.lower(): v for k, v in resp.headers.items()}

