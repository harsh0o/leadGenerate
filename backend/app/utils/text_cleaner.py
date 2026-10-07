import re
from bs4 import BeautifulSoup
from typing import List

def strip_html(text: str) -> str:
    """Removes HTML tags from the given text."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ")

def normalize_whitespace(text: str) -> str:
    """Replaces multiple whitespaces/newlines with a single space."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def extract_urls(text: str) -> List[str]:
    """Extracts all URLs from the given text."""
    if not text:
        return []
    url_pattern = re.compile(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*')
    return url_pattern.findall(text)

def truncate_for_llm(text: str, max_chars: int = 4000) -> str:
    """Truncates text to prevent overflowing LLM context windows (word-boundary)."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars-3]
    # Prefer word boundary to avoid mid-word cut harming classification
    space = cut.rfind(" ")
    if space > max_chars * 0.5:
        cut = cut[:space]
    return cut + "..."

def clean_post(title: str, body: str) -> str:
    """Combines title and body, cleans HTML and whitespace, ready for LLM."""
    # Guard against huge HTML payloads (DoS via large pages)
    t = (title or "")[:20000]
    b = (body or "")[:100000]
    combined = f"{t} \n {b}"
    no_html = strip_html(combined)
    clean_text = normalize_whitespace(no_html)
    return truncate_for_llm(clean_text)
