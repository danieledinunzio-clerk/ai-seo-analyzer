#!/usr/bin/env python3
"""
AI-Era Website SEO Analyzer
Methodology: Metehan Yesilyurt / AEOVision research-first framework
Covers: Traditional SEO (Layer 1) + AI Search Visibility (Layer 2)
"""

import sys
import re
import json
import time
import warnings
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional

warnings.filterwarnings("ignore")  # suppress urllib3/SSL warnings

import requests
from bs4 import BeautifulSoup
import tiktoken
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.text import Text
from rich.columns import Columns
from rich.markup import escape as rescape

console = Console()

# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class Finding:
    category: str
    severity: str  # CRITICAL / WARNING / INFO / PASS
    layer: str     # TRADITIONAL / AI / BOTH
    title: str
    detail: str
    action: str
    effort: str    # LOW / MEDIUM / HIGH
    impact: str    # LOW / MEDIUM / HIGH

@dataclass
class PageData:
    url: str
    status_code: int = 0
    title: str = ""
    meta_description: str = ""
    h1s: list = field(default_factory=list)
    h2s: list = field(default_factory=list)
    h3s: list = field(default_factory=list)
    og_tags: dict = field(default_factory=dict)
    json_ld: list = field(default_factory=list)
    canonical: str = ""
    meta_robots: str = ""
    word_count: int = 0
    token_count: int = 0
    char_count: int = 0
    sections: list = field(default_factory=list)  # (heading, word_count)
    internal_links: list = field(default_factory=list)
    external_links: list = field(default_factory=list)
    load_time_ms: float = 0
    has_viewport: bool = False
    has_schema: bool = False
    schema_types: list = field(default_factory=list)
    text_content: str = ""

@dataclass
class SiteData:
    base_url: str
    domain: str = ""
    robots_txt: str = ""
    sitemap_urls: list = field(default_factory=list)
    pages: list = field(default_factory=list)
    findings: list = field(default_factory=list)

# ─────────────────────────────────────────────
# FETCHER
# ─────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch(url: str, timeout: int = 15) -> tuple[Optional[requests.Response], float]:
    """Fetch a URL, return (response, elapsed_ms)."""
    try:
        start = time.time()
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        elapsed = (time.time() - start) * 1000
        return r, elapsed
    except Exception as e:
        return None, 0.0

def normalize_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")

def get_domain(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc

# ─────────────────────────────────────────────
# TOKEN ANALYSIS
# ─────────────────────────────────────────────

try:
    ENC = tiktoken.get_encoding("o200k_base")  # GPT-4o tokenizer
except Exception:
    ENC = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(ENC.encode(text))

def chars_per_token(text: str) -> float:
    tokens = count_tokens(text)
    if tokens == 0:
        return 0.0
    return len(text) / tokens

# ─────────────────────────────────────────────
# PAGE PARSER
# ─────────────────────────────────────────────

def parse_page(url: str) -> PageData:
    data = PageData(url=url)
    resp, elapsed = fetch(url)
    if not resp:
        return data

    data.status_code = resp.status_code
    data.load_time_ms = elapsed

    if resp.status_code != 200:
        return data

    soup = BeautifulSoup(resp.text, "lxml")

    # Title
    title_tag = soup.find("title")
    data.title = title_tag.get_text(strip=True) if title_tag else ""

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    data.meta_description = meta_desc.get("content", "").strip() if meta_desc else ""

    # Canonical
    canon = soup.find("link", rel="canonical")
    data.canonical = canon.get("href", "") if canon else ""

    # Meta robots
    meta_robots = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    data.meta_robots = meta_robots.get("content", "").lower() if meta_robots else ""

    # Viewport
    viewport = soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)})
    data.has_viewport = viewport is not None

    # OG tags
    for tag in soup.find_all("meta", property=re.compile("^og:", re.I)):
        prop = tag.get("property", "").lower()
        content = tag.get("content", "")
        data.og_tags[prop] = content

    # JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            obj = json.loads(script.string or "")
            data.json_ld.append(obj)
            schema_type = obj.get("@type", "")
            if schema_type:
                data.schema_types.append(schema_type)
        except Exception:
            pass
    data.has_schema = len(data.json_ld) > 0

    # Headings
    data.h1s = [h.get_text(strip=True) for h in soup.find_all("h1")]
    data.h2s = [h.get_text(strip=True) for h in soup.find_all("h2")]
    data.h3s = [h.get_text(strip=True) for h in soup.find_all("h3")]

    # Main content text (strip nav/footer/header/script/style)
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    body = soup.find("body")
    text = body.get_text(separator=" ", strip=True) if body else ""
    data.text_content = text
    data.word_count = len(text.split())
    data.char_count = len(text)
    data.token_count = count_tokens(text)

    # Section-level chunk analysis
    if body:
        current_heading = "Intro"
        current_words = []
        for tag in body.descendants:
            if not hasattr(tag, "name"):
                continue
            if tag.name in ("h1", "h2", "h3", "h4"):
                if current_words:
                    wc = len(" ".join(current_words).split())
                    data.sections.append((current_heading, wc))
                current_heading = tag.get_text(strip=True)
                current_words = []
            elif tag.name in ("p", "li", "td"):
                txt = tag.get_text(strip=True)
                if txt:
                    current_words.append(txt)
        if current_words:
            data.sections.append((current_heading, len(" ".join(current_words).split())))

    # Links
    parsed_base = urllib.parse.urlparse(url)
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#"):
            continue
        if href.startswith("/") or parsed_base.netloc in href:
            full = urllib.parse.urljoin(url, href)
            data.internal_links.append(full)
        elif href.startswith("http"):
            data.external_links.append(href)

    return data

# ─────────────────────────────────────────────
# ROBOTS.TXT ANALYSIS
# ─────────────────────────────────────────────

LLM_BOTS = [
    "GPTBot",
    "ClaudeBot",
    "PerplexityBot",
    "Google-Extended",
    "Googlebot",
    "anthropic-ai",
    "ChatGPT-User",
    "Bytespider",
    "FacebookBot",
    "ia_archiver",
]

def analyze_robots(base_url: str) -> tuple[str, list]:
    robots_url = base_url.rstrip("/") + "/robots.txt"
    resp, _ = fetch(robots_url)
    if not resp or resp.status_code != 200:
        return "", [Finding(
            category="Crawl & Index",
            severity="WARNING",
            layer="BOTH",
            title="robots.txt not found or inaccessible",
            detail=f"GET {robots_url} returned {resp.status_code if resp else 'no response'}.",
            action="Create a robots.txt at your domain root. Ensure GPTBot, ClaudeBot, PerplexityBot, and Google-Extended are allowed.",
            effort="LOW",
            impact="HIGH",
        )]

    content = resp.text
    findings = []
    blocked = []
    not_mentioned = []

    content_lower = content.lower()

    for bot in LLM_BOTS:
        bot_lower = bot.lower()
        # Check if explicitly disallowed
        lines = content.splitlines()
        user_agent_match = False
        disallowed = False
        for i, line in enumerate(lines):
            if line.lower().strip().startswith("user-agent"):
                val = line.split(":", 1)[-1].strip().lower()
                if val == bot_lower or val == "*":
                    user_agent_match = True
            if user_agent_match and line.lower().strip().startswith("disallow"):
                val = line.split(":", 1)[-1].strip()
                if val == "/" or val == "":
                    disallowed = val == "/"
            if line.lower().strip().startswith("user-agent") and i > 0:
                val = line.split(":", 1)[-1].strip().lower()
                if val != bot_lower and user_agent_match:
                    break

        if bot_lower not in content_lower:
            not_mentioned.append(bot)
        else:
            # crude check: find disallow / after user-agent: bot
            idx = content_lower.find(bot_lower)
            segment = content[idx:idx+200]
            if "disallow: /" in segment.lower():
                blocked.append(bot)

    if blocked:
        findings.append(Finding(
            category="Crawl & Index",
            severity="CRITICAL",
            layer="AI",
            title=f"LLM crawlers blocked in robots.txt: {', '.join(blocked)}",
            detail=(
                f"Disallow: / found for: {', '.join(blocked)}. "
                "These bots index your content for AI training and retrieval. "
                "Blocking them makes you invisible to those LLMs."
            ),
            action=(
                "Remove Disallow: / for each blocked LLM bot. "
                "Example fix:\n  User-agent: GPTBot\n  Allow: /\n"
            ),
            effort="LOW",
            impact="HIGH",
        ))

    if not_mentioned:
        findings.append(Finding(
            category="Crawl & Index",
            severity="INFO",
            layer="AI",
            title=f"LLM bots not explicitly mentioned: {', '.join(not_mentioned[:4])}{'...' if len(not_mentioned) > 4 else ''}",
            detail="Bots fall back to the wildcard (*) rule if not specifically listed. Add explicit Allow rules to future-proof.",
            action="Add explicit User-agent: + Allow: / blocks for GPTBot, ClaudeBot, PerplexityBot, Google-Extended, anthropic-ai.",
            effort="LOW",
            impact="MEDIUM",
        ))

    if not blocked and not not_mentioned:
        findings.append(Finding(
            category="Crawl & Index",
            severity="PASS",
            layer="AI",
            title="All major LLM crawlers are allowed in robots.txt",
            detail="robots.txt correctly grants access to AI crawlers.",
            action="No action needed. Periodically check as new bots emerge.",
            effort="LOW",
            impact="HIGH",
        ))

    return content, findings

# ─────────────────────────────────────────────
# SITEMAP ANALYSIS
# ─────────────────────────────────────────────

def analyze_sitemap(base_url: str) -> tuple[list, list]:
    sitemap_url = base_url.rstrip("/") + "/sitemap.xml"
    resp, _ = fetch(sitemap_url)
    findings = []
    urls = []

    if not resp or resp.status_code != 200:
        # Try sitemap_index
        findings.append(Finding(
            category="Crawl & Index",
            severity="WARNING",
            layer="TRADITIONAL",
            title="sitemap.xml not found at default location",
            detail=f"GET {sitemap_url} → {resp.status_code if resp else 'failed'}. Sitemaps accelerate discovery by Googlebot and indexing pipelines.",
            action="Create /sitemap.xml. Submit it in Google Search Console. Add Sitemap: directive to robots.txt.",
            effort="LOW",
            impact="HIGH",
        ))
        return urls, findings

    soup = BeautifulSoup(resp.text, "xml")
    locs = soup.find_all("loc")
    urls = [loc.get_text(strip=True) for loc in locs]

    if not urls:
        findings.append(Finding(
            category="Crawl & Index",
            severity="WARNING",
            layer="TRADITIONAL",
            title="sitemap.xml exists but contains no URLs",
            detail="An empty sitemap provides no crawl guidance.",
            action="Populate sitemap.xml with all canonical page URLs. Include <lastmod> and <priority> for freshness signals.",
            effort="MEDIUM",
            impact="HIGH",
        ))
    else:
        findings.append(Finding(
            category="Crawl & Index",
            severity="PASS",
            layer="TRADITIONAL",
            title=f"sitemap.xml found with {len(urls)} URL(s)",
            detail="Sitemap is accessible and populated.",
            action="Ensure all key pages are included. Add <lastmod> for freshness. Submit via Google Search Console.",
            effort="LOW",
            impact="MEDIUM",
        ))

    return urls, findings

# ─────────────────────────────────────────────
# ON-PAGE ANALYSIS
# ─────────────────────────────────────────────

def analyze_page(page: PageData) -> list:
    findings = []
    url = page.url

    # ── Title ──
    if not page.title:
        findings.append(Finding(
            category="On-Page",
            severity="CRITICAL",
            layer="TRADITIONAL",
            title="Missing <title> tag",
            detail=f"{url} has no title tag. This is a fundamental ranking signal.",
            action="Add a descriptive <title> (50-60 chars) front-loading the primary keyword.",
            effort="LOW",
            impact="HIGH",
        ))
    elif len(page.title) > 60:
        findings.append(Finding(
            category="On-Page",
            severity="WARNING",
            layer="TRADITIONAL",
            title=f"Title too long ({len(page.title)} chars): '{page.title[:60]}...'",
            detail="Google truncates titles > 60 chars in SERPs. This reduces CTR.",
            action="Shorten title to 50-60 chars. Front-load the primary keyword. Match pCTR model: title text directly drives CTR prediction.",
            effort="LOW",
            impact="MEDIUM",
        ))
    elif len(page.title) < 30:
        findings.append(Finding(
            category="On-Page",
            severity="WARNING",
            layer="TRADITIONAL",
            title=f"Title too short ({len(page.title)} chars): '{page.title}'",
            detail="Short titles miss keyword coverage opportunities.",
            action="Expand title to 50-60 chars with primary keyword + brand name.",
            effort="LOW",
            impact="MEDIUM",
        ))

    # ── Meta description ──
    if not page.meta_description:
        findings.append(Finding(
            category="On-Page",
            severity="WARNING",
            layer="TRADITIONAL",
            title="Missing meta description",
            detail="Without a meta description, Google generates its own — often poorly. Also: AI systems use meta descriptions as summary anchors.",
            action="Add a 150-160 char meta description. Front-load the value proposition. Include a natural CTA.",
            effort="LOW",
            impact="MEDIUM",
        ))
    elif len(page.meta_description) > 160:
        findings.append(Finding(
            category="On-Page",
            severity="INFO",
            layer="TRADITIONAL",
            title=f"Meta description too long ({len(page.meta_description)} chars)",
            detail="Truncated at 160 chars in SERPs.",
            action="Trim to 150-160 chars ensuring the core value proposition is in the first 120 chars.",
            effort="LOW",
            impact="LOW",
        ))

    # ── H1 ──
    if not page.h1s:
        findings.append(Finding(
            category="On-Page",
            severity="CRITICAL",
            layer="BOTH",
            title="No H1 tag found",
            detail="H1 is the primary semantic anchor for both Google and LLM retrieval chunks. Missing H1 breaks chunk context hierarchy.",
            action="Add exactly one H1 that matches user search intent. In AI retrieval, ancestor headings are preserved with each chunk — H1 sets the page-level context.",
            effort="LOW",
            impact="HIGH",
        ))
    elif len(page.h1s) > 1:
        findings.append(Finding(
            category="On-Page",
            severity="WARNING",
            layer="BOTH",
            title=f"Multiple H1 tags found ({len(page.h1s)}): {page.h1s[:3]}",
            detail="Multiple H1s confuse both Google's topic model and LLM chunk parsers.",
            action="Keep exactly one H1 per page. Demote extras to H2.",
            effort="LOW",
            impact="MEDIUM",
        ))

    # ── Heading structure ──
    if not page.h2s:
        findings.append(Finding(
            category="Content Architecture",
            severity="WARNING",
            layer="AI",
            title="No H2 tags — flat content structure",
            detail="Google AI Mode retrieval relies on heading hierarchy to create chunk context. Without H2s, the entire page is one undifferentiated chunk, severely limiting query fan-out coverage.",
            action="Structure content with H2 subheadings every 300-500 words (150-375 tokens). Each H2 should answer a distinct sub-query.",
            effort="MEDIUM",
            impact="HIGH",
        ))
    elif len(page.h2s) < 3 and page.word_count > 500:
        findings.append(Finding(
            category="Content Architecture",
            severity="WARNING",
            layer="AI",
            title=f"Only {len(page.h2s)} H2(s) for {page.word_count} words — under-structured",
            detail=f"Pages with <5 sections average 3/10 query fan-out coverage vs 7/10 for 15+ sections.",
            action="Add more H2/H3 subheadings. Target one heading per 250-375 words. Each section = one retrievable chunk.",
            effort="MEDIUM",
            impact="HIGH",
        ))

    # ── Canonical ──
    if not page.canonical:
        findings.append(Finding(
            category="On-Page",
            severity="WARNING",
            layer="TRADITIONAL",
            title="No canonical tag",
            detail="Without a canonical, Google may index duplicate/near-duplicate URLs separately, splitting PageRank.",
            action="Add <link rel='canonical' href='...'> to every page pointing to the preferred URL version.",
            effort="LOW",
            impact="MEDIUM",
        ))

    # ── Meta robots ──
    if "noindex" in page.meta_robots:
        findings.append(Finding(
            category="Crawl & Index",
            severity="CRITICAL",
            layer="BOTH",
            title=f"Page is NOINDEX: {url}",
            detail="noindex in meta robots removes this page from Google index and LLM retrieval pipelines that rely on Google's index.",
            action="Remove noindex directive if this page should be ranked. Check if this is intentional.",
            effort="LOW",
            impact="HIGH",
        ))

    # ── Viewport ──
    if not page.has_viewport:
        findings.append(Finding(
            category="Technical",
            severity="WARNING",
            layer="TRADITIONAL",
            title="No viewport meta tag — not mobile-optimized",
            detail="Google uses mobile-first indexing. Missing viewport = poor CWV scores = ranking suppression.",
            action="Add: <meta name='viewport' content='width=device-width, initial-scale=1'>",
            effort="LOW",
            impact="HIGH",
        ))

    # ── Load time ──
    if page.load_time_ms > 3000:
        findings.append(Finding(
            category="Technical",
            severity="CRITICAL",
            layer="TRADITIONAL",
            title=f"Slow page load: {page.load_time_ms:.0f}ms",
            detail=f"Pages >3s risk poor LCP (Core Web Vitals). Google's ranking uses real CWV data from Chrome UX Report. Target: LCP < 2.5s.",
            action="Optimize: compress images (use WebP/AVIF), enable CDN, defer non-critical JS, use server-side caching. Measure with PageSpeed Insights.",
            effort="HIGH",
            impact="HIGH",
        ))
    elif page.load_time_ms > 1500:
        findings.append(Finding(
            category="Technical",
            severity="WARNING",
            layer="TRADITIONAL",
            title=f"Page load borderline: {page.load_time_ms:.0f}ms",
            detail="LCP target is < 2.5s. Network overhead and server rendering add to real-user load time.",
            action="Run PageSpeed Insights for real CWV data. Optimize TTFB and LCP resource.",
            effort="MEDIUM",
            impact="MEDIUM",
        ))

    # ── Content length ──
    if page.word_count < 300:
        findings.append(Finding(
            category="Content Architecture",
            severity="WARNING",
            layer="BOTH",
            title=f"Thin content: {page.word_count} words",
            detail="Pages under 300 words rarely rank for competitive queries. LLMs also have minimum chunk size requirements (~50 tokens / ~65 words) to include a passage.",
            action="Expand to 800+ words for informational content. Cover the full topic with structured H2/H3 sections.",
            effort="HIGH",
            impact="HIGH",
        ))
    elif page.word_count > 3000:
        findings.append(Finding(
            category="Content Architecture",
            severity="INFO",
            layer="AI",
            title=f"Long-form content: {page.word_count} words — verify chunk structure",
            detail="Long content is valuable but must be properly chunked. Each H2 section must be 150-375 words to fit MUVERA retrieval windows (150-word target, 50-250 range).",
            action="Audit section-level word counts. Break oversized sections (>400 words) with H3 subheadings.",
            effort="MEDIUM",
            impact="MEDIUM",
        ))

    # ── Token efficiency ──
    cpt = chars_per_token(page.text_content)
    if cpt < 3.5:
        findings.append(Finding(
            category="Content Architecture",
            severity="WARNING",
            layer="AI",
            title=f"Low token efficiency: {cpt:.1f} chars/token (target: 5.5+)",
            detail="Heavy use of markdown tables, special characters, or dense jargon inflates token consumption in LLM context windows. Plain prose runs 5.9 chars/token; tables only 2.2.",
            action="Replace markdown tables with structured prose or definition lists. Remove unnecessary formatting characters. Use numerals (1,234) not words ('one thousand').",
            effort="MEDIUM",
            impact="MEDIUM",
        ))
    elif cpt >= 5.5:
        findings.append(Finding(
            category="Content Architecture",
            severity="PASS",
            layer="AI",
            title=f"Good token efficiency: {cpt:.1f} chars/token",
            detail="Content is efficiently structured for LLM context windows.",
            action="Maintain this ratio as you add content. Avoid heavy markdown table usage.",
            effort="LOW",
            impact="MEDIUM",
        ))

    # ── Chunk size audit ──
    oversized = [(h, wc) for h, wc in page.sections if wc > 375]
    undersized = [(h, wc) for h, wc in page.sections if 0 < wc < 50]
    if oversized:
        findings.append(Finding(
            category="Content Architecture",
            severity="WARNING",
            layer="AI",
            title=f"{len(oversized)} section(s) exceed 375-word retrieval chunk limit",
            detail=(
                f"Oversized sections: {', '.join([f'{h[:40]} ({wc}w)' for h,wc in oversized[:3]])}. "
                "Google AI Mode chunks at ~500 tokens (~375 words). Oversized sections = partial retrieval = lower citation chance."
            ),
            action="Insert H3 subheadings to break oversized sections. Each H3 creates a new retrievable chunk with inherited heading context.",
            effort="MEDIUM",
            impact="HIGH",
        ))
    if undersized:
        findings.append(Finding(
            category="Content Architecture",
            severity="INFO",
            layer="AI",
            title=f"{len(undersized)} section(s) below 50-word minimum chunk size",
            detail=(
                f"Under-minimum sections: {', '.join([f'{h[:40]} ({wc}w)' for h,wc in undersized[:3]])}. "
                "MUVERA requires minimum ~50 words per passage to include in retrieval."
            ),
            action="Expand short sections with concrete details, examples, or data. Merge with adjacent section if topically related.",
            effort="MEDIUM",
            impact="MEDIUM",
        ))

    # ── OG tags ──
    og_findings = analyze_og_tags(page)
    findings.extend(og_findings)

    # ── JSON-LD ──
    schema_findings = analyze_schema(page)
    findings.extend(schema_findings)

    return findings

# ─────────────────────────────────────────────
# OG TAG ANALYSIS
# ─────────────────────────────────────────────

CRITICAL_OG = ["og:title", "og:image", "og:description", "og:url", "og:type", "og:site_name"]

def analyze_og_tags(page: PageData) -> list:
    findings = []
    og = page.og_tags

    # Check critical tags
    missing = [tag for tag in CRITICAL_OG if tag not in og]
    if missing:
        findings.append(Finding(
            category="Google Discover",
            severity="WARNING",
            layer="TRADITIONAL",
            title=f"Missing OG tags: {', '.join(missing)}",
            detail=(
                "Google Discover uses OG tags for classification and pCTR prediction. "
                "og:title is directly consumed by Discover's title text model which drives CTR ranking."
            ),
            action=f"Add missing OG tags: {', '.join(missing)}. og:title and og:image are non-negotiable for Discover eligibility.",
            effort="LOW",
            impact="HIGH",
        ))

    # og:image size warning
    if "og:image" in og:
        img_url = og["og:image"]
        findings.append(Finding(
            category="Google Discover",
            severity="INFO",
            layer="TRADITIONAL",
            title=f"og:image set: {img_url[:60]}...",
            detail="Verify this image is ≥1200px wide. Google Discover requires 1200px minimum — smaller images get thumbnail treatment, reducing CTR and ranking.",
            action="Use an image ≥1200x630px. Check og:image:width and og:image:height tags are also set. Use og:image:secure_url for HTTPS.",
            effort="LOW",
            impact="HIGH",
        ))
    else:
        findings.append(Finding(
            category="Google Discover",
            severity="CRITICAL",
            layer="TRADITIONAL",
            title="og:image missing — Google Discover ineligible",
            detail="Without og:image (min 1200px), this page cannot receive Discover traffic. Discover drives massive passive discovery for content-heavy sites.",
            action="Add og:image with a 1200x630px image specific to this page's content. This single fix can unlock Discover as a traffic channel.",
            effort="LOW",
            impact="HIGH",
        ))

    # og:site_name for WPAS signal
    if "og:site_name" not in og:
        findings.append(Finding(
            category="Google Discover",
            severity="INFO",
            layer="TRADITIONAL",
            title="og:site_name missing",
            detail="og:site_name is one of the 6 OG tags that matter for Discover's WPAS signal differentiation. Register in Publisher Center for WPAS advantage.",
            action="Add og:site_name. Register site in Google Publisher Center for WPAS signal (differentiates from un-registered publishers).",
            effort="LOW",
            impact="MEDIUM",
        ))

    return findings

# ─────────────────────────────────────────────
# SCHEMA / JSON-LD ANALYSIS
# ─────────────────────────────────────────────

RECOMMENDED_SCHEMAS = {
    "Article": "For blog posts — boosts E-E-A-T signals and enables rich results",
    "FAQPage": "FAQ sections — directly feeds AI Q&A retrieval and rich results",
    "HowTo": "Step-by-step content — structured retrieval for AI and featured snippets",
    "Organization": "Brand entity declaration — key for Knowledge Graph and LLM entity recognition",
    "WebSite": "Sitelinks search box and site-level entity signals",
    "BreadcrumbList": "Navigation clarity for Googlebot and structured context for AI chunking",
    "Person": "Author E-E-A-T signals",
    "Product": "For ecommerce — required for SearchGPT/OpenAI shopping retrieval",
}

def analyze_schema(page: PageData) -> list:
    findings = []

    if not page.has_schema:
        findings.append(Finding(
            category="Structured Data",
            severity="CRITICAL",
            layer="BOTH",
            title="No JSON-LD structured data found",
            detail=(
                "Structured data is critical for: (1) Google rich results, (2) AI agent consumption without render overhead, "
                "(3) SearchGPT/OpenAI search which requires schema.org markup for machine-readable structure, "
                "(4) LLM entity recognition."
            ),
            action=(
                "Add JSON-LD structured data. Start with: Organization (brand entity), WebSite, and page-specific types (Article, FAQPage, HowTo). "
                "SearchGPT explicitly requires Schema.org markup for retrieval consideration."
            ),
            effort="MEDIUM",
            impact="HIGH",
        ))
        return findings

    found_types = set(page.schema_types)
    findings.append(Finding(
        category="Structured Data",
        severity="PASS",
        layer="BOTH",
        title=f"JSON-LD found: {', '.join(found_types) or 'type unknown'}",
        detail="Structured data enables rich results and AI agent consumption.",
        action="Validate at schema.org/validator. Ensure all required properties are populated.",
        effort="LOW",
        impact="MEDIUM",
    ))

    # Recommend missing high-value schemas
    recommended_missing = [s for s in ["FAQPage", "Organization", "WebSite"] if s not in found_types]
    if recommended_missing:
        findings.append(Finding(
            category="Structured Data",
            severity="INFO",
            layer="BOTH",
            title=f"High-value schema types missing: {', '.join(recommended_missing)}",
            detail="\n".join([f"• {s}: {RECOMMENDED_SCHEMAS[s]}" for s in recommended_missing]),
            action=f"Implement {', '.join(recommended_missing)} schema. FAQPage is especially high-value for LLM Q&A retrieval. Organization establishes your brand entity in Knowledge Graph.",
            effort="MEDIUM",
            impact="HIGH",
        ))

    return findings

# ─────────────────────────────────────────────
# ENTITY & AI SIGNAL ANALYSIS
# ─────────────────────────────────────────────

ATTRIBUTION_PATTERNS = [
    r"\baccording to\b",
    r"\bstudy\b",
    r"\bresearch\b",
    r"\breport\b",
    r"\bdata shows?\b",
    r"\bsurvey\b",
    r"\banalysis\b",
    r"\bsource[s]?\b",
]

ENTITY_PATTERNS = [
    r"\b(is|are) a\b",
    r"\bprovides?\b",
    r"\bspecializes? in\b",
    r"\bfounded in\b",
    r"\bbased in\b",
]

def analyze_ai_signals(page: PageData) -> list:
    findings = []
    text = page.text_content.lower()

    # Attribution signals
    attr_count = sum(
        len(re.findall(pat, text, re.I)) for pat in ATTRIBUTION_PATTERNS
    )
    words = page.word_count or 1
    attr_rate = attr_count / (words / 100)  # per 100 words

    if attr_rate < 1.0 and page.word_count > 200:
        findings.append(Finding(
            category="AI Citability",
            severity="WARNING",
            layer="AI",
            title=f"Low attribution signal density: {attr_count} signals in {page.word_count} words",
            detail=(
                "Attribution patterns ('according to', 'research shows', 'study found') are primary citability signals for LLMs. "
                "LLMs prefer content that itself cites sources — it validates claim confidence and reduces hallucination risk. "
                "Target: at least 1 attribution signal per 2-3 factual claims."
            ),
            action="Add source citations and attribution language throughout the content. Link to original studies/reports. Add: 'According to [source]...' constructs every 2-3 paragraphs.",
            effort="MEDIUM",
            impact="HIGH",
        ))
    elif attr_rate >= 2.0:
        findings.append(Finding(
            category="AI Citability",
            severity="PASS",
            layer="AI",
            title=f"Strong attribution signal density: {attr_count} signals ({attr_rate:.1f}/100 words)",
            detail="Good use of attribution patterns improves LLM citability.",
            action="Maintain this pattern. Ensure citations link to authoritative sources (studies, official reports).",
            effort="LOW",
            impact="HIGH",
        ))

    # Entity definition patterns
    entity_count = sum(
        len(re.findall(pat, text, re.I)) for pat in ENTITY_PATTERNS
    )
    if entity_count < 2 and page.word_count > 200:
        findings.append(Finding(
            category="AI Citability",
            severity="INFO",
            layer="AI",
            title="Weak entity definition patterns",
            detail=(
                "LLMs build entity understanding from '[Entity] is...' and '[Entity] provides...' constructs. "
                "Without explicit entity definitions, LLMs may misattribute or hallucinate around your brand."
            ),
            action="Add explicit entity declarations: '[Brand] is a [category] that...', '[Brand] provides...', '[Brand] specializes in...'. These patterns anchor your entity in LLM context.",
            effort="LOW",
            impact="MEDIUM",
        ))

    # Query fan-out coverage estimate
    section_count = len(page.sections)
    if section_count < 5:
        coverage_est = "~30%"
        findings.append(Finding(
            category="AI Citability",
            severity="WARNING",
            layer="AI",
            title=f"Low query fan-out coverage estimate: ~{coverage_est} ({section_count} sections)",
            detail=(
                "Google AI Mode breaks a topic into a network of sub-queries. "
                f"Pages with <5 sections average 3/10 query coverage. Your page has {section_count} section(s). "
                "AI systems will only retrieve content for queries your sections explicitly address."
            ),
            action=(
                "Generate 8-10 likely questions a user might have about this topic. "
                "Add a dedicated H2 section for each unanswered question. "
                "Consider adding an FAQ schema section covering top sub-queries."
            ),
            effort="HIGH",
            impact="HIGH",
        ))
    elif section_count >= 10:
        findings.append(Finding(
            category="AI Citability",
            severity="PASS",
            layer="AI",
            title=f"Strong query fan-out potential: {section_count} sections",
            detail="Well-sectioned content covers more sub-queries in AI retrieval.",
            action="Map each H2/H3 to a specific user question. Remove sections that don't answer a distinct query.",
            effort="LOW",
            impact="MEDIUM",
        ))

    return findings

# ─────────────────────────────────────────────
# DOMAIN STRATEGY CHECK
# ─────────────────────────────────────────────

SHARED_PLATFORMS = [
    "medium.com", "substack.com", "wordpress.com", "blogspot.com",
    "tumblr.com", "wix.com", "squarespace.com", "weebly.com",
    "blogger.com", "ghost.io", "beehiiv.com", "linkedin.com",
]

def analyze_domain(base_url: str) -> list:
    findings = []
    domain = get_domain(base_url)

    is_shared = any(plat in domain for plat in SHARED_PLATFORMS)
    if is_shared:
        findings.append(Finding(
            category="Domain Strategy",
            severity="CRITICAL",
            layer="AI",
            title=f"Content on shared platform: {domain}",
            detail=(
                "ChatGPT uses the Public Suffix List (PSL) for attribution. Content on shared platforms "
                f"(e.g., medium.com, substack.com) attributes authority to the PLATFORM, not your brand. "
                f"Your content on {domain} builds Medium/Substack's LLM authority, not yours. "
                ".com domains capture 80.41% of all LLM citations."
            ),
            action=(
                "Migrate to your own registered domain (yourband.com). "
                "Cross-post from your domain first, then syndicate to platforms with canonical pointing to your domain. "
                "This is the #1 structural barrier to LLM attribution."
            ),
            effort="HIGH",
            impact="HIGH",
        ))
    else:
        tld = domain.split(".")[-1]
        if tld != "com":
            findings.append(Finding(
                category="Domain Strategy",
                severity="INFO",
                layer="AI",
                title=f"Non-.com TLD: .{tld}",
                detail=".com domains capture 80.41% of all LLM citations. Non-.com TLDs face statistical underrepresentation in LLM responses.",
                action="If possible, acquire the .com equivalent. Ensure consistent cross-platform branding to compensate for TLD disadvantage.",
                effort="MEDIUM",
                impact="MEDIUM",
            ))
        else:
            findings.append(Finding(
                category="Domain Strategy",
                severity="PASS",
                layer="AI",
                title=f"Own .com domain: {domain}",
                detail="Correct domain strategy for LLM attribution. PSL-compliant.",
                action="Maintain consistent entity presence across GitHub, LinkedIn, Wikipedia (if notable), and other authoritative platforms.",
                effort="LOW",
                impact="HIGH",
            ))

    return findings

# ─────────────────────────────────────────────
# AGENT FILE CHECK
# ─────────────────────────────────────────────

def check_agent_files(base_url: str) -> list:
    findings = []

    # Check llms.txt
    llms_url = base_url.rstrip("/") + "/llms.txt"
    resp, _ = fetch(llms_url)
    if resp and resp.status_code == 200:
        findings.append(Finding(
            category="AI Agent Readiness",
            severity="PASS",
            layer="AI",
            title="llms.txt found",
            detail="llms.txt helps LLMs understand your site structure and content priorities.",
            action="Keep llms.txt updated with your key pages, purpose, and content hierarchy.",
            effort="LOW",
            impact="MEDIUM",
        ))
    else:
        findings.append(Finding(
            category="AI Agent Readiness",
            severity="INFO",
            layer="AI",
            title="llms.txt not found",
            detail=(
                "llms.txt is an emerging standard (llmstxt.org) for declaring your site's purpose and structure to LLM agents — "
                "analogous to robots.txt for traditional crawlers. Early adopters gain discoverability advantages as AI agents proliferate."
            ),
            action=(
                "Create /llms.txt following the llmstxt.org spec. Include: site purpose, key pages with descriptions, "
                "preferred content format, and contact/about information for AI agent consumption."
            ),
            effort="LOW",
            impact="MEDIUM",
        ))

    return findings

# ─────────────────────────────────────────────
# INTERNAL LINK ANALYSIS
# ─────────────────────────────────────────────

def analyze_internal_links(pages: list) -> list:
    findings = []
    if len(pages) <= 1:
        return findings

    link_counts = {}
    for page in pages:
        for link in page.internal_links:
            link_counts[link] = link_counts.get(link, 0) + 1

    orphan_pages = [p for p in pages if p.url not in link_counts and p.url != pages[0].url]
    if orphan_pages:
        findings.append(Finding(
            category="Internal Linking",
            severity="WARNING",
            layer="TRADITIONAL",
            title=f"{len(orphan_pages)} page(s) appear to have no internal links pointing to them",
            detail="Orphan pages receive no PageRank flow and are harder for Googlebot to discover.",
            action="Add contextual internal links from high-authority pages to orphan pages. Build topic clusters with pillar → supporting page link structure.",
            effort="MEDIUM",
            impact="HIGH",
        ))

    return findings

# ─────────────────────────────────────────────
# REPORT RENDERER
# ─────────────────────────────────────────────

SEVERITY_COLORS = {
    "CRITICAL": "red",
    "WARNING": "yellow",
    "INFO": "cyan",
    "PASS": "green",
}

SEVERITY_ORDER = {"CRITICAL": 0, "WARNING": 1, "INFO": 2, "PASS": 3}
IMPACT_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

def severity_icon(s: str) -> str:
    return {"CRITICAL": "✗", "WARNING": "!", "INFO": "i", "PASS": "✓"}.get(s, "?")

def render_report(site: SiteData):
    findings = site.findings
    pages = site.pages

    # ── Header ──
    console.print()
    console.print(Panel.fit(
        f"[bold white]AI-Era SEO Audit Report[/bold white]\n"
        f"[dim]Site: {site.base_url}[/dim]\n"
        f"[dim]Pages analyzed: {len(pages)} | Total findings: {len(findings)}[/dim]",
        border_style="blue",
        title="[bold blue]AI SEO Analyzer[/bold blue]",
    ))

    # ── Score card ──
    critical = [f for f in findings if f.severity == "CRITICAL"]
    warnings = [f for f in findings if f.severity == "WARNING"]
    info_items = [f for f in findings if f.severity == "INFO"]
    passes = [f for f in findings if f.severity == "PASS"]

    score = max(0, 100 - len(critical) * 15 - len(warnings) * 5 - len(info_items) * 1)
    score_color = "red" if score < 50 else "yellow" if score < 75 else "green"

    score_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    score_table.add_column("", style="bold")
    score_table.add_column("")
    score_table.add_row(f"[{score_color}]Overall Score: {score}/100[/{score_color}]", "")
    score_table.add_row(f"[red]Critical: {len(critical)}[/red]", f"[yellow]Warnings: {len(warnings)}[/yellow]")
    score_table.add_row(f"[cyan]Info: {len(info_items)}[/cyan]", f"[green]Passing: {len(passes)}[/green]")
    console.print(score_table)

    # ── Layer breakdown ──
    trad = [f for f in findings if f.layer in ("TRADITIONAL", "BOTH")]
    ai_layer = [f for f in findings if f.layer in ("AI", "BOTH")]
    trad_issues = [f for f in trad if f.severity in ("CRITICAL", "WARNING")]
    ai_issues = [f for f in ai_layer if f.severity in ("CRITICAL", "WARNING")]

    console.print(Panel(
        f"[bold]Layer 1 — Traditional Search (Google/Bing)[/bold]\n"
        f"  Issues: [{'red' if trad_issues else 'green'}]{len(trad_issues)}[/{'red' if trad_issues else 'green'}] requiring action\n\n"
        f"[bold]Layer 2 — AI Search (ChatGPT, Perplexity, Gemini)[/bold]\n"
        f"  Issues: [{'red' if ai_issues else 'green'}]{len(ai_issues)}[/{'red' if ai_issues else 'green'}] requiring action",
        title="Dual-Layer Diagnostic",
        border_style="dim",
    ))

    # ── Page snapshot ──
    if pages:
        pt = Table(title="Page Snapshot", box=box.SIMPLE_HEAD, show_lines=False)
        pt.add_column("URL", style="dim", max_width=45)
        pt.add_column("Status", justify="center")
        pt.add_column("Words", justify="right")
        pt.add_column("Tokens", justify="right")
        pt.add_column("CPT", justify="right")
        pt.add_column("Load", justify="right")
        pt.add_column("H1s", justify="center")
        pt.add_column("H2s", justify="center")
        pt.add_column("Schema", justify="center")

        for p in pages:
            cpt = chars_per_token(p.text_content) if p.text_content else 0
            status_color = "green" if p.status_code == 200 else "red"
            short_url = p.url.replace(site.base_url, "") or "/"
            pt.add_row(
                short_url[:45],
                f"[{status_color}]{p.status_code}[/{status_color}]",
                str(p.word_count),
                str(p.token_count),
                f"{cpt:.1f}",
                f"{p.load_time_ms:.0f}ms",
                str(len(p.h1s)),
                str(len(p.h2s)),
                "[green]Yes[/green]" if p.has_schema else "[red]No[/red]",
            )
        console.print(pt)

    # ── All findings grouped by category ──
    categories = {}
    for f in findings:
        categories.setdefault(f.category, []).append(f)

    sorted_cats = sorted(categories.items())
    for cat, cat_findings in sorted_cats:
        sorted_findings = sorted(cat_findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))
        console.print(f"\n[bold underline]{cat}[/bold underline]")
        for f in sorted_findings:
            color = SEVERITY_COLORS.get(f.severity, "white")
            icon = severity_icon(f.severity)
            layer_badge = f"[dim][{f.layer}][/dim]"
            console.print(f"  [{color}]{icon} [{f.severity}][/{color}] {layer_badge} [bold]{rescape(f.title)}[/bold]")
            if f.detail:
                for line in f.detail.strip().split("\n"):
                    console.print(f"     [dim]{rescape(line)}[/dim]")
            console.print(f"     [italic]→ {rescape(f.action)}[/italic]")
            console.print(f"     [dim]Effort: {f.effort} | Impact: {f.impact}[/dim]")

    # ── Priority Action Matrix ──
    console.print()
    console.print(Panel.fit(
        "[bold]Priority Action Matrix[/bold]\n[dim]Ranked by Impact (HIGH first) then Effort (LOW first)[/dim]",
        border_style="bright_blue",
    ))

    actionable = [f for f in findings if f.severity in ("CRITICAL", "WARNING")]
    actionable.sort(key=lambda f: (
        IMPACT_ORDER.get(f.impact, 9),
        {"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get(f.effort, 9),
        SEVERITY_ORDER.get(f.severity, 9),
    ))

    mat = Table(box=box.SIMPLE_HEAD, show_lines=True)
    mat.add_column("#", style="dim", width=3)
    mat.add_column("Priority", width=10)
    mat.add_column("Layer", width=12)
    mat.add_column("Finding", max_width=40)
    mat.add_column("Effort", width=8)
    mat.add_column("Impact", width=8)

    for i, f in enumerate(actionable[:20], 1):
        sev_color = SEVERITY_COLORS.get(f.severity, "white")
        imp_color = "red" if f.impact == "HIGH" else "yellow" if f.impact == "MEDIUM" else "dim"
        eff_color = "green" if f.effort == "LOW" else "yellow" if f.effort == "MEDIUM" else "red"
        mat.add_row(
            str(i),
            f"[{sev_color}]{f.severity}[/{sev_color}]",
            f.layer,
            rescape(f.title[:40]),
            f"[{eff_color}]{f.effort}[/{eff_color}]",
            f"[{imp_color}]{f.impact}[/{imp_color}]",
        )

    console.print(mat)

    # ── Quick Wins ──
    quick_wins = [f for f in findings if f.effort == "LOW" and f.severity in ("CRITICAL", "WARNING")]
    if quick_wins:
        console.print()
        console.print("[bold green]Quick Wins (Low Effort / High-Medium Impact):[/bold green]")
        for f in quick_wins[:8]:
            console.print(f"  [green]→[/green] [{rescape(f.category)}] {rescape(f.title)}")

    # ── 30/60/90 Roadmap ──
    console.print()
    console.print(Panel(
        "[bold]30-Day (Foundation)[/bold]\n"
        "  • Fix all CRITICAL findings immediately (canonical, H1, noindex, robots.txt LLM access)\n"
        "  • Add JSON-LD structured data: Organization + WebSite + page-specific types\n"
        "  • Optimize og:image (1200px+) and all OG tags for Discover eligibility\n"
        "  • Add viewport meta tag and audit Core Web Vitals via PageSpeed Insights\n"
        "  • Create/fix sitemap.xml and submit to Google Search Console\n"
        "  • Add llms.txt at domain root\n\n"
        "[bold]60-Day (Content Architecture)[/bold]\n"
        "  • Re-chunk all pages: ensure each section is 150-375 words under a clear H2/H3\n"
        "  • Generate 8-10 sub-queries per content page; add sections for uncovered queries\n"
        "  • Add attribution patterns ('according to...', 'research shows...') every 2-3 claims\n"
        "  • Add explicit entity declarations ('[Brand] is...', '[Brand] provides...')\n"
        "  • Improve token efficiency: replace markdown tables with prose, use numerals\n"
        "  • Add FAQPage schema to all informational pages\n\n"
        "[bold]90-Day (Authority & AI Visibility)[/bold]\n"
        "  • Establish entity presence: GitHub, LinkedIn, YouTube, Product Hunt, Wikipedia (if notable)\n"
        "  • Acquire high-Harmonic-Centrality backlinks (WordPress.org plugin, GitHub repos, podcasts)\n"
        "  • Check CC Rank at webgraph.metehan.ai vs competitors — target <1M rank\n"
        "  • Run manual LLM citation audit: test in ChatGPT, Perplexity, Gemini for your key queries\n"
        "  • Map GSC queries to conversational prompts; track AI vs Google visibility gap\n"
        "  • Implement Discover freshness strategy: 7-day content publication cadence",
        title="[bold]30/60/90 Day Roadmap to #1 + LLM Citations[/bold]",
        border_style="green",
    ))

    console.print()
    console.print("[dim]Methodology: Metehan Yesilyurt / AEOVision research-first framework[/dim]")
    console.print("[dim]For CC Rank data: webgraph.metehan.ai | LLM citation audit: test manually in ChatGPT, Perplexity, Gemini[/dim]")
    console.print()

# ─────────────────────────────────────────────
# JSON OUTPUT (--json mode)
# ─────────────────────────────────────────────

def emit_progress(stage: str, detail: str = "") -> None:
    """Print a progress event as NDJSON to stdout."""
    obj: dict = {"type": "progress", "stage": stage}
    if detail:
        obj["detail"] = detail
    print(json.dumps(obj), flush=True)


def output_json(site: "SiteData") -> None:
    """Print final result as NDJSON to stdout."""
    findings = site.findings
    pages = site.pages

    critical = [f for f in findings if f.severity == "CRITICAL"]
    warnings_list = [f for f in findings if f.severity == "WARNING"]
    info_items = [f for f in findings if f.severity == "INFO"]
    passes = [f for f in findings if f.severity == "PASS"]

    score = max(0, 100 - len(critical) * 15 - len(warnings_list) * 5 - len(info_items) * 1)

    trad = [f for f in findings if f.layer in ("TRADITIONAL", "BOTH")]
    ai_layer = [f for f in findings if f.layer in ("AI", "BOTH")]
    trad_issues = [f for f in trad if f.severity in ("CRITICAL", "WARNING")]
    ai_issues = [f for f in ai_layer if f.severity in ("CRITICAL", "WARNING")]

    pages_data = []
    for p in pages:
        cpt = chars_per_token(p.text_content) if p.text_content else 0.0
        pages_data.append({
            "url": p.url,
            "status_code": p.status_code,
            "title": p.title,
            "word_count": p.word_count,
            "token_count": p.token_count,
            "chars_per_token": round(cpt, 2),
            "load_time_ms": round(p.load_time_ms, 0),
            "h1_count": len(p.h1s),
            "h2_count": len(p.h2s),
            "has_schema": p.has_schema,
            "schema_types": p.schema_types,
            "canonical": p.canonical,
            "meta_description": p.meta_description,
        })

    findings_data = [
        {
            "category": f.category,
            "severity": f.severity,
            "layer": f.layer,
            "title": f.title,
            "detail": f.detail,
            "action": f.action,
            "effort": f.effort,
            "impact": f.impact,
        }
        for f in findings
    ]

    result = {
        "type": "result",
        "data": {
            "score": score,
            "url": site.base_url,
            "domain": site.domain,
            "pages_analyzed": len(pages),
            "pages": pages_data,
            "findings": findings_data,
            "summary": {
                "critical": len(critical),
                "warning": len(warnings_list),
                "info": len(info_items),
                "passing": len(passes),
            },
            "layer_summary": {
                "traditional_issues": len(trad_issues),
                "ai_issues": len(ai_issues),
                "traditional_total": len(trad),
                "ai_total": len(ai_layer),
            },
        },
    }
    print(json.dumps(result), flush=True)


# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

def collect_pages_to_analyze(base_url: str, sitemap_urls: list, max_pages: int = 5) -> list:
    """Collect a representative set of URLs to analyze."""
    urls_to_check = [base_url]

    # Add all sitemap URLs on the same domain
    for url in sitemap_urls:
        parsed = urllib.parse.urlparse(url)
        base_parsed = urllib.parse.urlparse(base_url)
        if parsed.netloc == base_parsed.netloc:
            if url not in urls_to_check:
                urls_to_check.append(url)

    # 0 = no limit (analyze all)
    if max_pages == 0:
        return urls_to_check
    return urls_to_check[:max_pages]

def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red] python3 seo_analyzer.py <url> [max_pages]")
        console.print("  Example: python3 seo_analyzer.py https://example.com 5")
        sys.exit(1)

    args = sys.argv[1:]
    json_mode = "--json" in args
    positional = [a for a in args if not a.startswith("--")]

    raw_url = positional[0]
    max_pages = int(positional[1]) if len(positional) > 1 else 5

    base_url = normalize_url(raw_url)
    domain = get_domain(base_url)

    site = SiteData(base_url=base_url, domain=domain)

    if json_mode:
        # Redirect Rich console output to stderr so stdout is clean NDJSON
        import io
        console._file = sys.stderr

        emit_progress("domain")
        site.findings.extend(analyze_domain(base_url))

        emit_progress("robots")
        robots_content, robots_findings = analyze_robots(base_url)
        site.robots_txt = robots_content
        site.findings.extend(robots_findings)

        emit_progress("sitemap")
        sitemap_urls, sitemap_findings = analyze_sitemap(base_url)
        site.sitemap_urls = sitemap_urls
        site.findings.extend(sitemap_findings)

        emit_progress("agent_files")
        site.findings.extend(check_agent_files(base_url))

        urls_to_analyze = collect_pages_to_analyze(base_url, sitemap_urls, max_pages)
        for url in urls_to_analyze:
            emit_progress("page", url)
            page = parse_page(url)
            site.pages.append(page)

            page_path = url.replace(base_url, "") or "/"
            page_findings = analyze_page(page)
            for f in page_findings:
                f.title = f"(page:{page_path}) " + f.title
            site.findings.extend(page_findings)

            ai_findings = analyze_ai_signals(page)
            for f in ai_findings:
                f.title = f"(page:{page_path}) " + f.title
            site.findings.extend(ai_findings)

        emit_progress("internal_links")
        site.findings.extend(analyze_internal_links(site.pages))

        emit_progress("complete")
        output_json(site)
    else:
        console.print(f"\n[bold blue]AI-Era SEO Analyzer[/bold blue] — analyzing [underline]{base_url}[/underline]")
        console.print(f"[dim]Max pages: {max_pages} | Methodology: Metehan Yesilyurt / AEOVision[/dim]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:

            # Domain strategy
            task = progress.add_task("Checking domain strategy...", total=None)
            site.findings.extend(analyze_domain(base_url))
            progress.remove_task(task)

            # robots.txt
            task = progress.add_task("Fetching robots.txt...", total=None)
            robots_content, robots_findings = analyze_robots(base_url)
            site.robots_txt = robots_content
            site.findings.extend(robots_findings)
            progress.remove_task(task)

            # sitemap
            task = progress.add_task("Fetching sitemap.xml...", total=None)
            sitemap_urls, sitemap_findings = analyze_sitemap(base_url)
            site.sitemap_urls = sitemap_urls
            site.findings.extend(sitemap_findings)
            progress.remove_task(task)

            # agent files
            task = progress.add_task("Checking AI agent files (llms.txt)...", total=None)
            site.findings.extend(check_agent_files(base_url))
            progress.remove_task(task)

            # pages
            urls_to_analyze = collect_pages_to_analyze(base_url, sitemap_urls, max_pages)
            for url in urls_to_analyze:
                task = progress.add_task(f"Analyzing: {url[:60]}...", total=None)
                page = parse_page(url)
                site.pages.append(page)

                # Page-level analysis
                page_path = url.replace(base_url, "") or "/"
                page_findings = analyze_page(page)
                for f in page_findings:
                    f.title = f"(page:{page_path}) " + f.title
                site.findings.extend(page_findings)

                # AI signal analysis
                ai_findings = analyze_ai_signals(page)
                for f in ai_findings:
                    f.title = f"(page:{page_path}) " + f.title
                site.findings.extend(ai_findings)

                progress.remove_task(task)

            # Internal linking
            task = progress.add_task("Analyzing internal link structure...", total=None)
            site.findings.extend(analyze_internal_links(site.pages))
            progress.remove_task(task)

        # Render full report
        render_report(site)

if __name__ == "__main__":
    main()
