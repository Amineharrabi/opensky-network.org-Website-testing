import pytest

from tests.test_logger import get_logger, log_step
from utils.web_audit import check_urls, collect_dom_urls, is_internal_url

logger = get_logger(__name__)


PAGES = [
    ("/", "Home"),
    ("/about", "About"),
    ("/about/faq", "FAQ"),
    ("/data", "Data"),
    ("/data/api", "API"),
    ("/feed", "Feed"),
    ("/feed/raspberry", "Raspberry feed guide"),
]


@pytest.mark.links
@pytest.mark.audit
@pytest.mark.parametrize("path,desc", PAGES)
def test_links_01_internal_links_not_broken(driver, settings, path, desc):
    url = settings.base_url.rstrip("/") + path
    log_step(logger, 1, f"Loading {desc}: {url}")
    driver.get(url)

    log_step(logger, 2, "Collecting DOM URLs (a/script/link/img)")
    collected = collect_dom_urls(driver, base_url=settings.base_url)
    urls = collected["links"]

    # Internal only by default; external links tend to be noisy and out of scope.
    internal = [u for u in urls if is_internal_url(settings.base_url, u)]
    external = [u for u in urls if u not in internal]

    if settings.check_external_links:
        to_check = internal + external
    else:
        to_check = internal

    log_step(logger, 3, f"Checking {min(len(to_check), settings.link_check_max)} URLs")
    results = check_urls(
        to_check,
        timeout=settings.link_check_timeout_s,
        max_urls=settings.link_check_max,
        delay_s=settings.link_check_delay_s,
        require_https=False,
    )

    broken = [r for r in results if not r.ok]
    if broken:
        details = [(b.url, b.status_code, b.error) for b in broken[:10]]
        logger.info(f"[FINDING] broken links/resources on {url}: {details}")
    if settings.audit_strict:
        assert not broken, f"Broken links/resources on {url}: {[(b.url, b.status_code) for b in broken]}"

