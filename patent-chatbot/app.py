"""
Global Patent Search Assistant

Agents:
  [Blue]   Google Patents  - Global patent search & detail extraction
  [Red]    DeepSeek AI     - Intelligent analysis & synthesis
"""

import json
import os
import re
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, Response, send_from_directory
from flask_cors import CORS
from openai import OpenAI

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
# Google Patents + DuckDuckGo - Global Patent Search
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


def _download_patent_pdf(patent_number):
    """Download patent PDF from Google Patents and save locally. Returns local URL or None."""
    import os
    clean = patent_number.strip().replace(" ", "").replace(",", "")
    pdf_dir = os.path.join(os.path.dirname(__file__), "static", "pdfs")
    os.makedirs(pdf_dir, exist_ok=True)
    local_path = os.path.join(pdf_dir, f"{clean}.pdf")

    # If already downloaded, return immediately
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        return f"/static/pdfs/{clean}.pdf"

    try:
        # Step 1: Get the /pdf page which contains the real PDF URL
        pdf_page_url = f"https://patents.google.com/patent/{clean}/pdf"
        resp = httpx.get(pdf_page_url, headers=HEADERS, follow_redirects=True, timeout=20)
        if resp.status_code != 200:
            return None

        # Step 2: Extract real PDF URL from patentimages.storage.googleapis.com
        pdf_url = None
        m = re.search(r'(https://patentimages\.storage\.googleapis\.com/[^\s"\']+\.pdf)', resp.text)
        if m:
            pdf_url = m.group(1)

        if not pdf_url:
            return None

        # Step 3: Download the actual PDF
        pdf_resp = httpx.get(pdf_url, headers=HEADERS, follow_redirects=True, timeout=30)
        if pdf_resp.status_code == 200 and pdf_resp.content[:5] == b"%PDF-":
            with open(local_path, "wb") as f:
                f.write(pdf_resp.content)
            return f"/static/pdfs/{clean}.pdf"

    except Exception as e:
        print(f"PDF download failed for {patent_number}: {e}")
    return None


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

            # Download PDF
            pdf_local = _download_patent_pdf(patent_number)
            if pdf_local:
                detail["pdf_local_url"] = pdf_local
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
            "description": "Search Google Patents globally. Searches in both original language and English for comprehensive coverage across 100+ countries.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {"type": "string", "description": "Search keywords (original language)"},
                    "keywords_en": {"type": "string", "description": "English translation of keywords"},
                    "country": {"type": "string", "description": "Country filter: CN, US, EP, JP, KR, TW, WO (optional)"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"},
                },
                "required": ["keywords"]
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
        n = arguments.get("max_results", 10)

        all_results = []
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = {
                pool.submit(agent_google_patents_search, keywords, country, n): "Google (original)",
                pool.submit(agent_google_patents_search, keywords_en, country, n): "Google (EN)",
            }
            for f in as_completed(futures, timeout=30):
                try:
                    all_results.extend(f.result())
                except Exception:
                    pass

        unique = _dedupe(all_results, n * 2)
        return {
            "total_found": len(unique),
            "results": unique,
            "keywords": {"original": keywords, "english": keywords_en},
        }

    elif tool_name == "get_patent_detail":
        pn = arguments.get("patent_number", "")
        return agent_fetch_patent_detail(pn)

    return {"error": f"Unknown tool: {tool_name}"}


# ═══════════════════════════════════════════════════════════════════════════
# Agent System Prompt
# ═══════════════════════════════════════════════════════════════════════════

AGENT_SYSTEM_PROMPT = """You are the "Global Patent Search Assistant", an AI Agent with patent search capabilities.

## Your Tools

### `search_patents_global` (Recommended first step)
Searches Google Patents globally in both original language and English.
Always provide both `keywords` (original language) and `keywords_en` (English translation).

### `get_patent_detail`
Fetch complete info for a specific patent number.

## Workflow Rules

1. **Always search first** - Use `search_patents_global` to get real data before answering
2. **Multi-language keywords** - Translate user's keywords to English for `keywords_en`
3. **Only use get_patent_detail when explicitly asked** - Do NOT auto-fetch details for every result
4. **Respond in user's language** - Match the user's conversation language
5. **MANDATORY: Every patent number MUST be a clickable link** - Format: `[CN103597579B](https://patents.google.com/patent/CN103597579B/zh)`. Never show a patent number as plain text.
6. **PDF download links** - If the search result or patent detail contains a `pdf_local_url` field, add a PDF download link: `[📥 下載PDF](pdf_local_url)`. Always show it next to the patent number.
6. **Structured output** - Use Markdown tables, lists, headers
7. **Be concise** - Summarize results directly, don't over-explain

## Response Template

After searching, structure your response EXACTLY like this:

### 搜索摘要
- 搜索關鍵詞: ...
- 總結果數: X項專利

### 專利結果表格

| 專利號 | 標題 | 申請人 | PDF |
|--------|------|--------|-----|
| [US12345678B2](https://patents.google.com/patent/US12345678B2/zh) | Title here | Applicant | [📥 PDF](/static/pdfs/US12345678B2.pdf) |
| [CN112233445A](https://patents.google.com/patent/CN112233445A/zh) | Title here | Applicant | [📥 PDF](/static/pdfs/CN112233445A.pdf) |

IMPORTANT: The patent number column MUST contain a Markdown hyperlink to Google Patents. The URL format is: https://patents.google.com/patent/{PATENT_NUMBER}/zh (remove all commas and spaces from the patent number in the URL).
IMPORTANT: If the tool result contains a `pdf_local_url` field, use that exact URL for the PDF download link. If no `pdf_local_url` is available, still provide a PDF link in the format `/static/pdfs/{PATENT_NUMBER}.pdf` — the server will attempt to download it on demand.

### 關鍵發現分析
...

### 擴展搜索建議
...
"""


# ═══════════════════════════════════════════════════════════════════════════
# Flask Routes
# ═══════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/patent-pdf/<patent_number>")
def api_patent_pdf(patent_number):
    """On-demand PDF download. If the PDF doesn't exist locally, download it from Google Patents."""
    import os
    clean = patent_number.strip().replace(" ", "").replace(",", "")
    pdf_dir = os.path.join(os.path.dirname(__file__), "static", "pdfs")
    local_path = os.path.join(pdf_dir, f"{clean}.pdf")

    # If already exists, serve it
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        return send_from_directory(pdf_dir, f"{clean}.pdf", mimetype="application/pdf")

    # Try to download
    pdf_local = _download_patent_pdf(patent_number)
    if pdf_local and os.path.exists(local_path):
        return send_from_directory(pdf_dir, f"{clean}.pdf", mimetype="application/pdf")

    return {"error": f"PDF not available for {patent_number}"}, 404


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

            for iteration in range(2):
                # First round: allow tool calls; second round: no tools at all
                api_kwargs = {
                    "model": "deepseek-chat",
                    "messages": current_messages,
                    "temperature": 0.7,
                    "max_tokens": 4096,
                }
                if iteration == 0:
                    api_kwargs["tools"] = TOOL_DEFINITIONS
                    api_kwargs["tool_choice"] = "auto"

                response = client.chat.completions.create(**api_kwargs)
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
                        if len(result_str) > 6000:
                            result_str = result_str[:6000] + "...(truncated)"

                        current_messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": result_str
                        })

                        # Result count status + save to DB
                        total = result.get("total_found", 0)
                        if total:
                            s2 = f">> Found {total} results\n\n"
                            yield f"data: {json.dumps({'content': s2}, ensure_ascii=False)}\n\n"
                            try:
                                query_text = args.get("keywords", "") or args.get("patent_number", "")
                                database.save_search(None, query_text, total, result.get("results", [])[:5])
                                database.log_activity(None, "search", f"搜尋完成: {query_text}", f"找到 {total} 筆結果")
                            except Exception:
                                pass

                    # Before second round, instruct AI to summarize (not call tools)
                    current_messages.append({
                        "role": "user",
                        "content": "Now please summarize and analyze the search results above. Present them in a structured format with a Markdown table. Do NOT attempt to call any more functions or output XML. Respond in the same language as my original query."
                    })
                    continue

                else:
                    # Stream the final response - filter out XML tool call artifacts
                    def _clean_xml(text):
                        """Remove DeepSeek XML tool call hallucinations."""
                        return re.sub(r'<\|?\s*DSML[^>]*>.*?</?\|?\s*DSML[^>]*>', '', text, flags=re.DOTALL)

                    if msg.content:
                        cleaned = _clean_xml(msg.content)
                        if cleaned.strip():
                            yield f"data: {json.dumps({'content': cleaned}, ensure_ascii=False)}\n\n"
                        break

                    try:
                        stream = client.chat.completions.create(
                            model="deepseek-chat",
                            messages=current_messages,
                            stream=True,
                            temperature=0.7,
                            max_tokens=4096,
                        )
                        got_content = False
                        buffer = ""
                        for chunk in stream:
                            if chunk.choices and chunk.choices[0].delta.content:
                                token = chunk.choices[0].delta.content
                                # Skip XML-like tool call content
                                if '<' in token and ('DSML' in token or 'function_call' in token or 'invoke' in token):
                                    continue
                                buffer += token
                                # Flush buffer periodically, filtering XML
                                if len(buffer) > 50 or '\n' in token:
                                    cleaned = _clean_xml(buffer)
                                    if cleaned:
                                        got_content = True
                                        yield f"data: {json.dumps({'content': cleaned}, ensure_ascii=False)}\n\n"
                                    buffer = ""
                        # Flush remaining
                        if buffer:
                            cleaned = _clean_xml(buffer)
                            if cleaned:
                                got_content = True
                                yield f"data: {json.dumps({'content': cleaned}, ensure_ascii=False)}\n\n"
                        if not got_content:
                            yield f"data: {json.dumps({'content': '搜尋完成，但 AI 合成回應為空。請重試。'}, ensure_ascii=False)}\n\n"
                    except Exception as stream_err:
                        traceback.print_exc()
                        yield f"data: {json.dumps({'content': f'AI 回應錯誤: {str(stream_err)[:200]}'}, ensure_ascii=False)}\n\n"
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
        return f"[Agent] Searching globally: \"{kw}\"\n  > Google Patents (100+ countries)\n\n"
    elif fn == "get_patent_detail":
        pn = args.get("patent_number", "")
        return f"[Google Patents] Fetching detail: {pn}\n\n"
    return f"[Agent] {fn}...\n\n"


# ═══════════════════════════════════════════════════════════════════════════
# Database API Routes
# ═══════════════════════════════════════════════════════════════════════════

import db as database
from datetime import datetime, date
from decimal import Decimal

def _serialize(obj):
    """JSON serializer for DB objects."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)


@app.route("/api/dashboard/stats")
def api_dashboard_stats():
    try:
        stats = database.get_dashboard_stats()
        return json.dumps(stats, default=_serialize)
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/projects", methods=["GET"])
def api_projects():
    try:
        status = request.args.get("status")
        projects = database.get_projects(status=status)
        return json.dumps(projects, default=_serialize, ensure_ascii=False)
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/projects", methods=["POST"])
def api_create_project():
    try:
        data = request.json
        pid = database.create_project(data["name"], data.get("description", ""), data.get("owner_id"))
        database.log_activity(data.get("owner_id"), "project_update", f"新專案建立: {data['name']}")
        return {"id": pid}
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/projects/<int:pid>", methods=["GET"])
def api_project_detail(pid):
    try:
        project = database.get_project(pid)
        if not project:
            return {"error": "Not found"}, 404
        return json.dumps(project, default=_serialize, ensure_ascii=False)
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/projects/<int:pid>", methods=["PUT"])
def api_update_project(pid):
    try:
        data = request.json
        database.update_project(pid, **data)
        return {"ok": True}
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/patents", methods=["GET"])
def api_patents():
    try:
        project_id = request.args.get("project_id", type=int)
        patents = database.get_patents(project_id=project_id)
        return json.dumps(patents, default=_serialize, ensure_ascii=False)
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/patents", methods=["POST"])
def api_save_patent():
    try:
        data = request.json
        pid = database.save_patent(data, data.get("project_id"))
        return {"id": pid}
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/search-history", methods=["GET"])
def api_search_history():
    try:
        history = database.get_search_history()
        return json.dumps(history, default=_serialize, ensure_ascii=False)
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/activity", methods=["GET"])
def api_activity():
    try:
        logs = database.get_activity_log()
        return json.dumps(logs, default=_serialize, ensure_ascii=False)
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/drafts", methods=["GET"])
def api_drafts():
    try:
        drafts = database.get_drafts()
        return json.dumps(drafts, default=_serialize, ensure_ascii=False)
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/drafts", methods=["POST"])
def api_save_draft():
    try:
        data = request.json
        did = database.save_draft(
            data.get("user_id"), data["title"], data.get("tech_field", ""),
            data.get("core_description", ""), data.get("prior_art_issues", ""),
            data.get("reference_patents", ""), data.get("generated_content", "")
        )
        return {"id": did}
    except Exception as e:
        return {"error": str(e)}, 500


@app.route("/api/users", methods=["GET"])
def api_users():
    try:
        users = database.get_users()
        return json.dumps(users, default=_serialize, ensure_ascii=False)
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    print("\n  Global Patent Search Assistant")
    print("  Agents: Google Patents | DeepSeek AI")
    print("  Server running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
