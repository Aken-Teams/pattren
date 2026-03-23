"""
Global Patent Search Assistant - Multi-Agent Architecture

Agent Levels:
  [Green]  pypatent       - USPTO full-text search (basic crawling)
  [Yellow] PQAI           - AI-powered semantic patent search
  [Blue]   Google Patents  - Global patent detail extraction
  [Red]    DeepSeek AI    - Intelligent analysis & synthesis
"""

import json
import os
import re
import traceback
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response, send_from_directory
from flask_cors import CORS
from openai import OpenAI

try:
    import pypatent
    HAS_PYPATENT = True
except ImportError:
    HAS_PYPATENT = False

app = Flask(__name__, static_folder="static")
CORS(app)

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", "sk-0570792a2bf849ff84b0437ce73e02de"),
    base_url="https://api.deepseek.com/v1",
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

# ═══════════════════════════════════════════════════════════════════════════
# AGENT 1: pypatent - USPTO Full-Text Search (Basic Crawling)
# ═══════════════════════════════════════════════════════════════════════════

def agent_pypatent_search(keywords, results_limit=10, get_details=False, **field_params):
    """Search USPTO full-text patent database via pypatent."""
    results = []
    if not HAS_PYPATENT:
        return [{"source": "USPTO (pypatent)", "error": "pypatent not installed"}]
    try:
        params = {
            "results_limit": results_limit,
            "get_patent_details": get_details,
        }
        if field_params:
            params.update(field_params)
        else:
            params["string"] = keywords

        s = pypatent.Search(**params)
        patent_list = s.as_list()

        for p in patent_list:
            if isinstance(p, dict):
                title = p.get("title", "")
                url = p.get("url", "")
            else:
                title = getattr(p, "title", "")
                url = getattr(p, "url", "")

            entry = {
                "source": "USPTO (pypatent)",
                "title": title,
                "url": url,
                "patent_number": _extract_patent_number(url + " " + title) or "",
            }

            if get_details and not isinstance(p, dict):
                entry.update({
                    "patent_number": getattr(p, "patent_num", "") or entry["patent_number"],
                    "patent_date": getattr(p, "patent_date", "") or "",
                    "filing_date": getattr(p, "file_date", "") or "",
                    "abstract": (getattr(p, "abstract", "") or "")[:500],
                    "inventors": getattr(p, "inventors", "") or "",
                    "applicant": getattr(p, "applicant_name", "") or "",
                    "assignee": getattr(p, "assignee_name", "") or "",
                    "family_id": getattr(p, "family_id", "") or "",
                    "claims_preview": (getattr(p, "claims", "") or "")[:400],
                })

            results.append(entry)

    except Exception as e:
        results.append({"source": "USPTO (pypatent)", "error": str(e)[:200]})
    return results


# ═══════════════════════════════════════════════════════════════════════════
# AGENT 2: PQAI - AI-Powered Semantic Patent Search
# ═══════════════════════════════════════════════════════════════════════════

PQAI_BASE = "https://api.projectpq.ai"

def agent_pqai_search(query, n=10):
    """AI-powered semantic patent search via PQAI API."""
    results = []
    try:
        resp = requests.get(
            f"{PQAI_BASE}/search/102",
            params={"q": query, "n": n, "type": "patent", "after": "2000-01-01"},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", []):
                pn = item.get("id", "") or item.get("publication_number", "")
                results.append({
                    "source": "PQAI (AI Search)",
                    "patent_number": pn,
                    "title": item.get("title", ""),
                    "abstract": (item.get("abstract", "") or "")[:500],
                    "score": item.get("score", 0),
                    "url": f"https://patents.google.com/patent/{pn}/en" if pn else "",
                })
        else:
            results.append({"source": "PQAI", "error": f"HTTP {resp.status_code}"})
    except Exception as e:
        results.append({"source": "PQAI", "error": str(e)[:200]})
    return results


def agent_pqai_similar(patent_number, n=10):
    """Find similar patents to a given patent number via PQAI."""
    results = []
    try:
        resp = requests.get(
            f"{PQAI_BASE}/similar/102",
            params={"pn": patent_number, "n": n, "type": "patent"},
            timeout=20,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", []):
                pn = item.get("id", "") or item.get("publication_number", "")
                results.append({
                    "source": "PQAI (Similar)",
                    "patent_number": pn,
                    "title": item.get("title", ""),
                    "abstract": (item.get("abstract", "") or "")[:500],
                    "score": item.get("score", 0),
                    "url": f"https://patents.google.com/patent/{pn}/en" if pn else "",
                })
        else:
            results.append({"source": "PQAI Similar", "error": f"HTTP {resp.status_code}"})
    except Exception as e:
        results.append({"source": "PQAI Similar", "error": str(e)[:200]})
    return results


def agent_pqai_prior_art(text, n=10):
    """Find prior art for a given technical description via PQAI."""
    results = []
    try:
        resp = requests.post(
            f"{PQAI_BASE}/prior-art/102",
            json={"q": text, "n": n, "type": "patent", "after": "2000-01-01"},
            timeout=25,
        )
        if resp.status_code == 200:
            data = resp.json()
            for item in data.get("results", []):
                pn = item.get("id", "") or item.get("publication_number", "")
                results.append({
                    "source": "PQAI (Prior Art)",
                    "patent_number": pn,
                    "title": item.get("title", ""),
                    "abstract": (item.get("abstract", "") or "")[:500],
                    "score": item.get("score", 0),
                    "url": f"https://patents.google.com/patent/{pn}/en" if pn else "",
                })
        else:
            results.append({"source": "PQAI Prior Art", "error": f"HTTP {resp.status_code}"})
    except Exception as e:
        results.append({"source": "PQAI Prior Art", "error": str(e)[:200]})
    return results


# ═══════════════════════════════════════════════════════════════════════════
# AGENT 3: Google Patents + DuckDuckGo - Global Patent Crawling
# ═══════════════════════════════════════════════════════════════════════════

def agent_google_patents_search(keywords, country=None, max_results=10):
    """Search Google Patents via DuckDuckGo site-restricted search."""
    results = []
    try:
        from duckduckgo_search import DDGS
        queries = [f'site:patents.google.com {keywords}']
        if country:
            queries.append(f'site:patents.google.com {keywords} {country}')

        with DDGS() as ddgs:
            for q in queries:
                try:
                    for r in ddgs.text(q, max_results=max_results):
                        pn = _extract_patent_number(r.get("href", "") + " " + r.get("title", ""))
                        if pn:
                            results.append({
                                "source": "Google Patents",
                                "patent_number": pn,
                                "title": r.get("title", "").replace(" - Google Patents", "").strip(),
                                "url": r.get("href", ""),
                                "snippet": r.get("body", ""),
                            })
                except Exception:
                    pass
    except Exception as e:
        results.append({"source": "Google Patents", "error": str(e)[:200]})

    return _dedupe(results, max_results)


def agent_fetch_patent_detail(patent_number):
    """Fetch detailed patent info from Google Patents by scraping."""
    detail = {"patent_number": patent_number, "source": "Google Patents"}
    try:
        clean = patent_number.strip().replace(" ", "")
        url = f"https://patents.google.com/patent/{clean}/en"
        resp = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")

            t = soup.select_one("span.title-text, h1#title")
            if t: detail["title"] = t.get_text(strip=True)

            a = soup.select_one("div.abstract, section#abstractSection div.abstract")
            if a: detail["abstract"] = a.get_text(strip=True)[:600]

            for dt in soup.select("dt"):
                key = dt.get_text(strip=True).lower()
                dd = dt.find_next_sibling("dd")
                if not dd: continue
                val = dd.get_text(strip=True)
                if "inventor" in key: detail["inventors"] = val
                elif "assignee" in key or "applicant" in key: detail["applicant"] = val
                elif "priority" in key: detail["priority_date"] = val
                elif "filed" in key or "filing" in key: detail["filing_date"] = val
                elif "publication" in key: detail["publication_date"] = val
                elif "grant" in key: detail["grant_date"] = val

            claims = soup.select("div.claim")
            if claims:
                detail["claims_count"] = len(claims)
                detail["first_claim"] = claims[0].get_text(strip=True)[:600]

            detail["url"] = url
        else:
            detail["error"] = f"HTTP {resp.status_code}"
    except Exception as e:
        detail["error"] = str(e)[:200]
    return detail


# ═══════════════════════════════════════════════════════════════════════════
# Utilities
# ═══════════════════════════════════════════════════════════════════════════

def _extract_patent_number(text):
    patterns = [
        r'(CN\d{5,13}[ABCUSY]\d?)', r'(US\d{7,11}[AB]\d?)',
        r'(US\d{10,13}[AB]\d)', r'(EP\d{7,9}[AB]\d?)',
        r'(WO\d{10,13}[AB]\d?)', r'(JP\d{7,12}[AB]\d?)',
        r'(KR\d{9,13}[AB]\d?)', r'(TW[IM]?\d{5,9}[AB]?\d?)',
        r'(DE\d{8,12}[AB]\d?)',
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m: return m.group(1).upper()
    return None


def _dedupe(results, limit=20):
    seen = set()
    out = []
    for r in results:
        key = r.get("patent_number") or r.get("url", "")
        if key and key not in seen:
            seen.add(key)
            out.append(r)
    return out[:limit]


# ═══════════════════════════════════════════════════════════════════════════
# Tool Definitions for DeepSeek Function Calling
# ═══════════════════════════════════════════════════════════════════════════

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_patents_global",
            "description": "Multi-agent global patent search. Simultaneously queries: (1) pypatent for USPTO, (2) PQAI AI for semantic search, (3) Google Patents for global coverage. Returns combined deduplicated results from all sources.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "Search keywords (original language)"},
                    "keywords_en": {"type": "string", "description": "English translation of keywords"},
                    "country": {"type": "string", "description": "Country filter: CN, US, EP, JP, KR, TW, WO (optional)"},
                    "max_results": {"type": "integer", "description": "Max results per source (default 8)"},
                },
                "required": ["keywords"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_uspto_advanced",
            "description": "Advanced USPTO search via pypatent with field-specific filters. Search by title, abstract, claims, inventor, assignee, IPC/CPC classification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "General search keywords (English)"},
                    "ttl": {"type": "string", "description": "Search in patent title"},
                    "abst": {"type": "string", "description": "Search in abstract"},
                    "aclm": {"type": "string", "description": "Search in claims"},
                    "in_": {"type": "string", "description": "Inventor name"},
                    "aanm": {"type": "string", "description": "Assignee/company name"},
                    "icl": {"type": "string", "description": "IPC classification (e.g. H01L)"},
                    "cpc": {"type": "string", "description": "CPC classification"},
                    "results_limit": {"type": "integer", "description": "Max results (default 10)"},
                    "get_details": {"type": "boolean", "description": "Fetch full details per patent (slower, default false)"},
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ai_semantic_search",
            "description": "PQAI AI-powered semantic patent search. Uses NLP/ML to find semantically similar patents. Best for: finding prior art, similarity analysis, concept-based search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Technical description or keywords (English)"},
                    "patent_number": {"type": "string", "description": "Find patents similar to this patent number (e.g. US9349679B2)"},
                    "mode": {"type": "string", "enum": ["search", "similar", "prior_art"], "description": "search=keyword search, similar=find similar to patent, prior_art=prior art search"},
                    "n": {"type": "integer", "description": "Number of results (default 10)"},
                },
                "required": ["mode"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_patent_detail",
            "description": "Fetch complete details for a specific patent from Google Patents: title, abstract, applicant, inventors, dates, claims.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patent_number": {"type": "string", "description": "Patent number (e.g. CN1770440A, US9349679B2)"},
                },
                "required": ["patent_number"]
            }
        }
    },
]


def execute_tool(tool_name, arguments):
    """Route tool calls to the appropriate agent."""

    if tool_name == "search_patents_global":
        keywords = arguments.get("keywords", "")
        keywords_en = arguments.get("keywords_en", keywords)
        country = arguments.get("country")
        n = arguments.get("max_results", 8)

        all_results = []
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(agent_pqai_search, keywords_en, n): "PQAI",
                pool.submit(agent_google_patents_search, keywords, country, n): "Google (original)",
                pool.submit(agent_google_patents_search, keywords_en, country, n): "Google (EN)",
                pool.submit(agent_pypatent_search, keywords_en, n, False): "pypatent",
            }
            for f in as_completed(futures, timeout=35):
                try:
                    all_results.extend(f.result())
                except Exception:
                    pass

        unique = _dedupe(all_results, n * 3)
        sources_used = list(set(r.get("source", "") for r in unique if "error" not in r))
        return {
            "total_found": len(unique),
            "results": unique,
            "sources_used": sources_used,
            "keywords": {"original": keywords, "english": keywords_en},
        }

    elif tool_name == "search_uspto_advanced":
        keywords = arguments.get("keywords", "")
        limit = arguments.get("results_limit", 10)
        details = arguments.get("get_details", False)
        fields = {}
        for f in ["ttl", "abst", "aclm", "in_", "aanm", "icl", "cpc"]:
            v = arguments.get(f)
            if v: fields[f] = v

        results = agent_pypatent_search(keywords, limit, details, **fields)
        return {
            "total_found": len([r for r in results if "error" not in r]),
            "results": results,
            "search_type": "USPTO Advanced (pypatent)",
        }

    elif tool_name == "ai_semantic_search":
        mode = arguments.get("mode", "search")
        n = arguments.get("n", 10)

        if mode == "similar":
            pn = arguments.get("patent_number", "")
            results = agent_pqai_similar(pn, n)
        elif mode == "prior_art":
            q = arguments.get("query", "")
            results = agent_pqai_prior_art(q, n)
        else:
            q = arguments.get("query", "")
            results = agent_pqai_search(q, n)

        return {
            "total_found": len([r for r in results if "error" not in r]),
            "results": results,
            "search_type": f"PQAI AI ({mode})",
        }

    elif tool_name == "get_patent_detail":
        pn = arguments.get("patent_number", "")
        return agent_fetch_patent_detail(pn)

    return {"error": f"Unknown tool: {tool_name}"}


# ═══════════════════════════════════════════════════════════════════════════
# Agent System Prompt
# ═══════════════════════════════════════════════════════════════════════════

AGENT_SYSTEM_PROMPT = """You are the "Global Patent Search Assistant", a top-tier AI Agent with multi-level patent search capabilities.

## Your Agent Architecture

You have FOUR specialized agents at your disposal, each with different strengths:

### Agent 1: pypatent (USPTO Full-Text Search)
- **Tool:** `search_patents_global` or `search_uspto_advanced`
- **Strength:** Direct access to USPTO full-text patent database
- **Best for:** US patent search, field-specific search (by title, abstract, claims, inventor, assignee, IPC/CPC)
- **Language:** English only

### Agent 2: PQAI (AI-Powered Semantic Search)
- **Tool:** `ai_semantic_search`
- **Modes:**
  - `search` - Keyword-based semantic search using NLP/ML
  - `similar` - Find patents similar to a given patent number
  - `prior_art` - Prior art search based on technical description
- **Strength:** AI understands technical concepts, not just keywords
- **Best for:** Prior art search, similarity analysis, concept-based search
- **Language:** English only

### Agent 3: Google Patents (Global Coverage)
- **Tool:** `search_patents_global` (included automatically) or `get_patent_detail`
- **Strength:** Covers 100+ countries, all patent offices
- **Best for:** Non-US patents (CN, EP, JP, KR, TW, etc.), detailed patent info extraction

### Agent 4: DeepSeek AI (You - Analysis & Synthesis)
- **Strength:** Multilingual analysis, claim comparison, design-around strategy, report generation
- **Best for:** Analyzing search results, translating, comparing patents, strategic advice

## How to Use Your Tools

### `search_patents_global` (Recommended first step)
Runs pypatent + PQAI + Google Patents **simultaneously** and returns combined results.
Always provide both `keywords` (original language) and `keywords_en` (English translation).

### `search_uspto_advanced`
For precise USPTO queries with field-specific filters.
Example: Search by assignee Samsung AND IPC H01L:
  aanm="Samsung", icl="H01L"

### `ai_semantic_search`
For AI-powered patent intelligence:
- mode="search": Semantic keyword search
- mode="similar": Input a patent_number, find similar patents
- mode="prior_art": Input technical description, find prior art

### `get_patent_detail`
Fetch complete info for a specific patent number.

## Workflow Rules

1. **Always search first** - Use tools to get real data before answering
2. **Multi-language keywords** - Translate user's keywords to English for tool calls
3. **Use multiple tools** - Combine results from different agents for comprehensive coverage
4. **Mark sources** - Always indicate which agent found each result
5. **Respond in user's language** - Match the user's conversation language
6. **Include links** - Add Google Patents links: `https://patents.google.com/patent/{PN}/zh`
7. **Structured output** - Use Markdown tables, lists, headers
8. **Search links** - Append clickable search URLs for Google Patents, Espacenet, WIPO, The Lens

## Agent Status Icons (use in responses)
- pypatent results
- PQAI AI results
- Google Patents results
- Analysis by AI

## Response Template

After searching, structure your response like this:

1. Search summary (keywords used, agents activated, total results)
2. Results table (patent number, title, applicant, source, relevance)
3. Key findings analysis
4. Extended search links for manual searching
"""


# ═══════════════════════════════════════════════════════════════════════════
# Flask Routes
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "messages" not in data:
        return {"error": "Missing messages"}, 400

    messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
    for msg in data["messages"]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    def generate():
        try:
            current_messages = list(messages)

            for iteration in range(6):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=current_messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=4096,
                )
                choice = response.choices[0]
                msg = choice.message

                if msg.tool_calls:
                    # Send status updates
                    for tc in msg.tool_calls:
                        fn = tc.function.name
                        args = json.loads(tc.function.arguments)
                        status = _tool_status_message(fn, args)
                        yield f"data: {json.dumps({'content': status}, ensure_ascii=False)}\n\n"

                    # Add assistant message
                    current_messages.append({
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [
                            {"id": tc.id, "type": "function",
                             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                            for tc in msg.tool_calls
                        ]
                    })

                    # Execute tools
                    for tc in msg.tool_calls:
                        fn = tc.function.name
                        args = json.loads(tc.function.arguments)
                        result = execute_tool(fn, args)
                        result_str = json.dumps(result, ensure_ascii=False, default=str)
                        if len(result_str) > 12000:
                            result_str = result_str[:12000] + "...(truncated)"

                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result_str
                        })

                        # Result count status
                        total = result.get("total_found", 0)
                        if total:
                            s2 = f">> Found {total} results\n\n"
                            yield f"data: {json.dumps({'content': s2}, ensure_ascii=False)}\n\n"

                    continue

                else:
                    # Stream final response
                    stream = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=current_messages,
                        stream=True,
                        temperature=0.7,
                        max_tokens=4096,
                    )
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            token = chunk.choices[0].delta.content
                            yield f"data: {json.dumps({'content': token}, ensure_ascii=False)}\n\n"
                    break

            yield "data: [DONE]\n\n"

        except Exception as e:
            traceback.print_exc()
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"

    return Response(generate(), mimetype="text/event-stream")


def _tool_status_message(fn, args):
    """Generate a user-friendly status message for tool calls."""
    if fn == "search_patents_global":
        kw = args.get("keywords", "")
        return f"[Agent] Searching globally: \"{kw}\"\n  > pypatent (USPTO) + PQAI (AI) + Google Patents\n\n"
    elif fn == "search_uspto_advanced":
        parts = []
        for k in ["keywords", "ttl", "abst", "aclm", "in_", "aanm", "icl", "cpc"]:
            v = args.get(k)
            if v: parts.append(f"{k}={v}")
        return f"[pypatent] USPTO advanced search: {', '.join(parts)}\n\n"
    elif fn == "ai_semantic_search":
        mode = args.get("mode", "search")
        q = args.get("query", "") or args.get("patent_number", "")
        return f"[PQAI AI] {mode}: \"{q}\"\n\n"
    elif fn == "get_patent_detail":
        pn = args.get("patent_number", "")
        return f"[Google Patents] Fetching detail: {pn}\n\n"
    return f"[Agent] {fn}...\n\n"


if __name__ == "__main__":
    print("\n  Global Patent Search Assistant (Multi-Agent)")
    print("  Agents: pypatent | PQAI AI | Google Patents | DeepSeek")
    print("  Server running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
