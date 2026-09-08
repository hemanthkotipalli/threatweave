"""
app/core/url_heuristics.py
--------------------------
Pure, network-free URL heuristic analysis functions for ThreatWeave Phase 6.

All public functions are designed to:
- Accept a URL string (or parsed components) and return a simple type.
- Never raise — malformed input returns safe defaults (False / 0 / 0.0).
- Be individually testable with zero mocking required.

Design note on severity thresholds
-----------------------------------
A SINGLE weak signal (e.g. suspicious TLD) is NEVER sufficient alone to
reach "high" or "critical" severity. At least 2 corroborating structural
flags are required before the suggested severity escalates beyond "medium".
This prevents alert fatigue from the many legitimate .xyz / .tk domains.
"""
from __future__ import annotations

import ipaddress
import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger("threatweave-api.core.url_heuristics")

# ---------------------------------------------------------------------------
# Curated reference data
# ---------------------------------------------------------------------------

# Well-known URL shortening services (structural detection only — no network).
_SHORTENER_HOSTS: frozenset[str] = frozenset({
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "is.gd",
    "ow.ly",
    "buff.ly",
    "rebrand.ly",
    "cutt.ly",
    "short.io",
    "bl.ink",
    "tiny.cc",
    "rb.gy",
    "shorturl.at",
})

# Weak-signal TLDs — commonly abused because they are free or lightly
# moderated.  NOTE: This is a WEAK signal.  Many legitimate services
# (developers, startups, open-source projects) use these TLDs.  Never
# promote a finding to "high"/"critical" based on this flag alone.
_SUSPICIOUS_TLDS: frozenset[str] = frozenset({
    ".tk",
    ".ml",
    ".ga",
    ".cf",
    ".gq",
    ".xyz",
    ".top",
    ".click",
    ".link",
    ".online",
    ".site",
    ".icu",
    ".pw",
    ".cc",
})

# Commonly-impersonated brand domains in Indian banking / UPI / government
# context.  lookalike_score() computes edit-distance similarity between the
# *registered domain* of the input URL and each entry in this list.
_BRAND_DOMAINS: list[str] = [
    "sbi.co.in",
    "onlinesbi.com",
    "hdfcbank.com",
    "icicibank.com",
    "axisbank.com",
    "bankofbaroda.in",
    "pnbindia.in",
    "unionbankofindia.co.in",
    "canarabank.com",
    "kotakbank.com",
    "paytm.com",
    "phonepe.com",
    "gpay.com",
    "bhimupi.org.in",
    "npci.org.in",
    "incometax.gov.in",
    "irctc.co.in",
    "uidai.gov.in",
    "epfindia.gov.in",
    "paypal.com",
    "amazon.in",
    "amazon.com",
    "flipkart.com",
    "myntra.com",
    "snapdeal.com",
]

# Path/query patterns that are structurally suspicious (credential harvesting
# paths, encoded redirects, etc.)
_SUSPICIOUS_PATH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(login|signin|verify|update|secure|account|password|credential)"),
    re.compile(r"(?i)(paypal|amazon|apple|microsoft|google|facebook|instagram)"),
    re.compile(r"(?i)(%[0-9a-f]{2}){5,}"),   # Heavy URL encoding
    re.compile(r"(?i)(cmd=|exec=|redirect=|return=|next=)"),
]


# ---------------------------------------------------------------------------
# Helper: extract registered domain (eTLD+1 approximation)
# ---------------------------------------------------------------------------

def _registered_domain(hostname: str) -> str:
    """
    Returns an approximation of the registered domain (eTLD+1) from a
    hostname.  This is a lightweight heuristic — it does NOT use the full
    Public Suffix List.  For the purposes of lookalike detection, stripping
    the left-most subdomains and comparing the result is sufficient.

    Examples:
        "login.secure.sbi.co.in"  -> "sbi.co.in"
        "hdfcbank.com"            -> "hdfcbank.com"
        "evil-paypa1.tk"          -> "evil-paypa1.tk"
    """
    parts = hostname.lower().split(".")
    # Common two-part country-code second-levels (.co.in, .org.in, .net.in …)
    if len(parts) >= 3 and parts[-2] in {"co", "org", "net", "gov", "ac", "edu"}:
        return ".".join(parts[-3:])
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return hostname.lower()


def _levenshtein(a: str, b: str) -> int:
    """Simple Levenshtein distance without external dependencies."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = curr
    return prev[-1]


def _domain_stem(reg: str) -> str:
    """
    Extracts the primary brand/domain label without the TLD/ccTLD.
    Examples:
        "paypal.com"              -> "paypal"
        "sbi.co.in"               -> "sbi"
        "paypa1-verify.tk"        -> "paypa1-verify"
        "onlinesbi-secure.com"    -> "onlinesbi-secure"
    """
    parts = reg.lower().split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "org", "net", "gov", "ac", "edu"}:
        return parts[0]
    if len(parts) >= 2:
        return parts[0]
    return reg.lower()


# Common leetspeak / homoglyph character substitutions used in phishing
_HOMOGLYPHS: dict[int, str] = str.maketrans({
    "0": "o",
    "1": "l",
    "3": "e",
    "4": "a",
    "5": "s",
    "7": "t",
    "8": "b",
    "@": "a",
    "$": "s",
})


# ---------------------------------------------------------------------------
# Public heuristic functions
# ---------------------------------------------------------------------------

def has_https(url: str) -> bool:
    """
    Returns True if the URL uses the https:// scheme, False otherwise.
    Returns False for malformed input instead of raising.

    :param url: Raw URL string to inspect.
    :return: True when scheme is 'https', False for http or any parse failure.
    """
    try:
        return urlparse(url).scheme.lower() == "https"
    except (ValueError, AttributeError):
        logger.debug("has_https: failed to parse url=%r", url)
        return False


def is_ip_address_host(url: str) -> bool:
    """
    Returns True when the URL's hostname is a raw IPv4 or IPv6 address
    rather than a domain name.  Attackers use bare IP addresses to bypass
    domain-reputation lookups and to conceal ownership.

    :param url: Raw URL string to inspect.
    :return: True if host is a valid IP address literal, False otherwise.
    """
    try:
        hostname = urlparse(url).hostname or ""
        # Strip IPv6 brackets if present
        hostname = hostname.strip("[]")
        ipaddress.ip_address(hostname)
        return True
    except (ValueError, AttributeError):
        return False


def count_subdomains(url: str) -> int:
    """
    Returns the number of subdomain labels in the URL's hostname, excluding
    the registered domain itself.  For example:
        login.secure.sbi.co.in  -> 2  (login, secure)
        www.paypal.com          -> 1  (www)
        paypal.com              -> 0

    Returns 0 for malformed input.

    :param url: Raw URL string to inspect.
    :return: Non-negative integer subdomain count.
    """
    try:
        hostname = (urlparse(url).hostname or "").lower()
        reg = _registered_domain(hostname)
        # Number of labels in hostname minus labels in registered domain
        host_parts = hostname.split(".")
        reg_parts = reg.split(".")
        extra = len(host_parts) - len(reg_parts)
        return max(0, extra)
    except (ValueError, AttributeError):
        logger.debug("count_subdomains: failed to parse url=%r", url)
        return 0


def is_known_shortener(url: str) -> bool:
    """
    Returns True if the URL's hostname (with or without www.) matches a
    known URL shortening service.  URL shorteners are commonly used in
    phishing to hide the real destination before the user clicks.

    Curated shortener list: bit.ly, tinyurl.com, t.co, goo.gl, is.gd,
    ow.ly, buff.ly, rebrand.ly, cutt.ly, short.io, bl.ink, tiny.cc,
    rb.gy, shorturl.at.

    :param url: Raw URL string to inspect.
    :return: True if host is a known shortener, False otherwise.
    """
    try:
        raw = (urlparse(url).hostname or "").lower()
        hostname = raw.removeprefix("www.")
        return hostname in _SHORTENER_HOSTS
    except (ValueError, AttributeError):
        logger.debug("is_known_shortener: failed to parse url=%r", url)
        return False


def has_suspicious_tld(url: str) -> bool:
    """
    Returns True if the URL's TLD appears on the curated weak-signal list.

    ⚠ WEAK SIGNAL: This flag alone MUST NOT be promoted to "high" or
    "critical" severity.  Many legitimate services use .xyz, .tk, etc.
    Require at least one additional corroborating structural flag.

    Curated TLD list: .tk, .ml, .ga, .cf, .gq, .xyz, .top, .click, .link,
    .online, .site, .icu, .pw, .cc.

    :param url: Raw URL string to inspect.
    :return: True if the TLD is in the curated suspicious list.
    """
    try:
        hostname = (urlparse(url).hostname or "").lower()
        for tld in _SUSPICIOUS_TLDS:
            if hostname.endswith(tld):
                return True
        return False
    except (ValueError, AttributeError):
        logger.debug("has_suspicious_tld: failed to parse url=%r", url)
        return False


def lookalike_score(url: str) -> tuple[float, str]:
    """
    Computes a 0–1 similarity score between the domain of the input URL
    and the closest entry in the curated brand-domain list.

    Checks:
    1. Exact registered domain match against the real brand -> returns (1.0, brand).
       (Exact match 1.0 is intentionally NOT flagged by callers because it indicates
       the legitimate brand domain).
    2. Full registered domain edit distance.
    3. Primary domain stem vs brand stem (e.g. paypa1 vs paypal).
    4. Delimited token vs brand stem (combosquatting, e.g. paypa1-verify or paypal-update).
    5. Leetspeak / homoglyph normalization (e.g. digit 1 for l, 0 for o).

    Non-exact domain matches are capped at 0.95 to preserve 1.0 strictly for
    genuine domains.

    :param url: Raw URL string to inspect.
    :return: Tuple of (similarity_score: float, closest_brand: str).
             Returns (0.0, "") on malformed input.
    """
    try:
        hostname = (urlparse(url).hostname or "").lower()
        reg = _registered_domain(hostname)
        if not reg:
            return 0.0, ""
        best_score = 0.0
        best_brand = ""
        cand_stem = _domain_stem(reg)
        cand_tokens = [t for t in re.split(r"[-_]", cand_stem) if t]

        for brand in _BRAND_DOMAINS:
            # Legitimate exact match
            if reg == brand:
                return 1.0, brand

            # 1. Full registered domain comparison
            max_len = max(len(reg), len(brand))
            if max_len > 0:
                dist = _levenshtein(reg, brand)
                score_full = 1.0 - (dist / max_len)
                if score_full > best_score:
                    best_score = score_full
                    best_brand = brand

            # 2. Domain stem vs brand stem (with homoglyph normalization)
            brand_stem = _domain_stem(brand)
            max_stem = max(len(cand_stem), len(brand_stem))
            if max_stem > 0 and len(brand_stem) >= 3:
                dist_stem = _levenshtein(cand_stem, brand_stem)
                score_stem = 1.0 - (dist_stem / max_stem)

                cand_stem_norm = cand_stem.translate(_HOMOGLYPHS)
                dist_stem_norm = _levenshtein(cand_stem_norm, brand_stem)
                score_stem_norm = 1.0 - (dist_stem_norm / max_stem)

                stem_candidate = min(max(score_stem, score_stem_norm), 0.95)
                if stem_candidate > best_score:
                    best_score = stem_candidate
                    best_brand = brand

            # 3. Delimited token vs brand stem (for combosquats e.g. paypa1-verify, paypal-update)
            for tok in cand_tokens:
                if len(tok) >= 3 and len(brand_stem) >= 3:
                    max_tok = max(len(tok), len(brand_stem))
                    dist_tok = _levenshtein(tok, brand_stem)
                    score_tok = 1.0 - (dist_tok / max_tok)

                    tok_norm = tok.translate(_HOMOGLYPHS)
                    dist_tok_norm = _levenshtein(tok_norm, brand_stem)
                    score_tok_norm = 1.0 - (dist_tok_norm / max_tok)

                    tok_best = min(max(score_tok, score_tok_norm), 0.95)
                    if tok_best > best_score:
                        best_score = tok_best
                        best_brand = brand

        return round(best_score, 4), best_brand
    except (ValueError, AttributeError):
        logger.debug("lookalike_score: failed to parse url=%r", url)
        return 0.0, ""


def _has_ip_userinfo(url: str) -> bool:
    """
    Detects URLs where an IP address is embedded in the userinfo (before @).
    E.g.: http://192.168.1.1@paypa1-verify.tk/login
    Attackers use this to make the URL appear to point to a trusted IP while
    actually sending the user to a different host.
    Returns True if urlparse reveals an IP-looking username.
    """
    try:
        parsed = urlparse(url)
        username = parsed.username or ""
        if not username:
            return False
        ipaddress.ip_address(username)
        return True
    except (ValueError, AttributeError):
        return False


def _has_suspicious_path(url: str) -> bool:
    """
    Returns True when the URL path or query string contains patterns
    associated with credential-harvesting pages (login, verify, etc.).
    Internal helper — not part of the public heuristics API.
    """
    try:
        parsed = urlparse(url)
        target = (parsed.path or "") + "?" + (parsed.query or "")
        return any(p.search(target) for p in _SUSPICIOUS_PATH_PATTERNS)
    except (ValueError, AttributeError):
        return False


def run_heuristics(url: str) -> dict:
    """
    Runs all structural/offline heuristics against the given URL and
    aggregates the results into a single findings dictionary.

    Severity escalation rules (corroboration required):
    - "critical" : 4+ flags, or ip_address_url + lookalike_domain together.
    - "high"     : 3+ flags (must include at least one strong structural flag,
                   i.e. NOT only suspicious_tld or url_shortener alone).
    - "medium"   : 2+ flags (any combination).
    - "low"      : 1 flag.
    - "info"     : 0 flags.

    A single suspicious_tld flag alone NEVER reaches "high" or "critical".

    :param url: Raw URL string to analyze.
    :return: Dictionary with keys:
        - "indicators"         : list[str]  – matched indicator strings.
        - "suggested_severity" : str        – one of info/low/medium/high/critical.
        - "details"            : dict       – per-check values for transparency.
    """
    indicators: list[str] = []
    details: dict = {}

    # --- Run all checks; each one is individually exception-safe ---
    https_ok = has_https(url)
    ip_host = is_ip_address_host(url)
    ip_userinfo = _has_ip_userinfo(url)
    subdomain_count = count_subdomains(url)
    shortener = is_known_shortener(url)
    bad_tld = has_suspicious_tld(url)
    lk_score, lk_brand = lookalike_score(url)
    suspicious_path = _has_suspicious_path(url)

    details["has_https"] = https_ok
    details["is_ip_address_host"] = ip_host
    details["has_ip_in_userinfo"] = ip_userinfo
    details["subdomain_count"] = subdomain_count
    details["is_known_shortener"] = shortener
    details["has_suspicious_tld"] = bad_tld
    details["lookalike_score"] = lk_score
    details["closest_brand"] = lk_brand
    details["has_suspicious_path"] = suspicious_path

    # Collect indicators
    if not https_ok:
        indicators.append("no_https")
    if ip_host:
        indicators.append("ip_address_url")
    # IP embedded in userinfo (before @) is a strong obfuscation signal
    if ip_userinfo and "suspicious_url_structure" not in indicators:
        indicators.append("suspicious_url_structure")
    if subdomain_count > 3:
        indicators.append("excessive_subdomains")
    if shortener:
        indicators.append("url_shortener")
    if bad_tld:
        indicators.append("suspicious_tld")

    # Lookalike: flag only when score is high but NOT an exact match of the
    # real brand (score == 1.0 means the user IS on the real domain).
    if lk_score >= 0.75 and lk_score < 1.0:
        indicators.append("lookalike_domain")

    # Suspicious path adds structural flag when any strong indicator is present
    # (login/verify/credential paths on an IP host or lookalike = high-risk combo)
    if (
        suspicious_path
        and ("ip_address_url" in indicators or "lookalike_domain" in indicators)
        and "suspicious_url_structure" not in indicators
    ):
        indicators.append("suspicious_url_structure")

    # --- Severity: require corroboration, never promote lone weak signal ---
    flag_count = len(indicators)
    strong_flags = {
        "ip_address_url",
        "lookalike_domain",
        "excessive_subdomains",
        "suspicious_url_structure",
    }
    has_strong = bool(set(indicators) & strong_flags)

    # ip_address_url + lookalike → critical even at 2 flags
    if (
        "ip_address_url" in indicators and "lookalike_domain" in indicators
        or flag_count >= 4
    ):
        severity = "critical"
    elif flag_count >= 3 and has_strong or flag_count >= 2 and "ip_address_url" in indicators:
        severity = "high"
    elif flag_count >= 2:
        severity = "medium"
    elif flag_count == 1:
        # Single weak-only signal stays at "low" — suspicious_tld alone
        # is NOT promoted further
        severity = "low"
    else:
        severity = "info"

    return {
        "indicators": indicators,
        "suggested_severity": severity,
        "details": details,
    }
