"""
backend/actions/web_search.py — Websuche via DuckDuckGo mit HTTP-Fallback.
"""

from __future__ import annotations
import urllib.parse
import requests
from bs4 import BeautifulSoup

def web_search(parameters: dict, **kwargs) -> str:
    query = str(parameters.get("query", "")).strip()
    if not query:
        return "Keine Suchanfrage übergeben."

    # 1. DuckDuckGo Search API
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if results:
                formatted = []
                for r in results:
                    title = r.get("title", "Kein Titel")
                    link = r.get("href", "")
                    body = r.get("body", "")
                    formatted.append(f"• [{title}]({link})\n  {body}")
                return f"Suchergebnisse für '{query}':\n\n" + "\n\n".join(formatted)
    except Exception:
        pass

    # 2. Fallback: DuckDuckGo HTML Scraping
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"}
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for res in soup.find_all("div", class_="result__body", limit=5):
            title_tag = res.find("a", class_="result__snippet") or res.find("a", class_="result__url")
            snip_tag = res.find("a", class_="result__snippet")
            if title_tag:
                results.append(f"• {title_tag.text.strip()}\n  {snip_tag.text.strip() if snip_tag else ''}")
        if results:
            return f"Suchergebnisse (HTML Fallback) für '{query}':\n\n" + "\n\n".join(results)
    except Exception as e:
        return f"Fehler bei Websuche: {e}"

    return f"Keine Suchergebnisse für '{query}' gefunden."

TOOL = {
    "name": "web_search",
    "description": "Führt eine Websuche über DuckDuckGo durch und gibt aktuelle Informationen, Nachrichten oder Recherche-Snippets zurück.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Suchbegriff oder Fragestellung."
            }
        },
        "required": ["query"]
    },
    "handler": web_search
}
