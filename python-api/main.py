import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from seo_analyzer import (
    normalize_url,
    get_domain,
    SiteData,
    analyze_domain,
    analyze_robots,
    analyze_sitemap,
    check_agent_files,
    collect_pages_to_analyze,
    parse_page,
    analyze_page,
    analyze_ai_signals,
    analyze_internal_links,
    chars_per_token,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    url: str
    maxPages: int = 5


def build_result(site: SiteData) -> dict:
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

    return {
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


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(body: AnalyzeRequest):
    async def generate():
        try:
            base_url = normalize_url(body.url)
            domain = get_domain(base_url)
            site = SiteData(base_url=base_url, domain=domain)

            def sse(obj: dict) -> str:
                return f"data: {json.dumps(obj)}\n\n"

            yield sse({"type": "progress", "stage": "domain"})
            site.findings.extend(await asyncio.to_thread(analyze_domain, base_url))

            yield sse({"type": "progress", "stage": "robots"})
            robots_content, robots_findings = await asyncio.to_thread(analyze_robots, base_url)
            site.robots_txt = robots_content
            site.findings.extend(robots_findings)

            yield sse({"type": "progress", "stage": "sitemap"})
            sitemap_urls, sitemap_findings = await asyncio.to_thread(analyze_sitemap, base_url)
            site.sitemap_urls = sitemap_urls
            site.findings.extend(sitemap_findings)

            yield sse({"type": "progress", "stage": "agent_files"})
            site.findings.extend(await asyncio.to_thread(check_agent_files, base_url))

            urls_to_analyze = collect_pages_to_analyze(base_url, sitemap_urls, body.maxPages)
            for url in urls_to_analyze:
                yield sse({"type": "progress", "stage": "page", "detail": url})
                page = await asyncio.to_thread(parse_page, url)
                site.pages.append(page)

                page_path = url.replace(base_url, "") or "/"
                page_findings = await asyncio.to_thread(analyze_page, page)
                for f in page_findings:
                    f.title = f"(page:{page_path}) " + f.title
                site.findings.extend(page_findings)

                ai_findings = await asyncio.to_thread(analyze_ai_signals, page)
                for f in ai_findings:
                    f.title = f"(page:{page_path}) " + f.title
                site.findings.extend(ai_findings)

            yield sse({"type": "progress", "stage": "internal_links"})
            site.findings.extend(await asyncio.to_thread(analyze_internal_links, site.pages))

            yield sse({"type": "progress", "stage": "complete"})
            yield sse(build_result(site))
            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
