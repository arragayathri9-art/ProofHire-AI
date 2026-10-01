import requests
from html.parser import HTMLParser
import re
from typing import Tuple

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self.title = ""
        self._in_title = False
        self._skip = False

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in ('script', 'style', 'noscript', 'svg', 'iframe'):
            self._skip = True
        elif t == 'title':
            self._in_title = True

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ('script', 'style', 'noscript', 'svg', 'iframe'):
            self._skip = False
        elif t == 'title':
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data.strip() + " "
        elif not self._skip and data.strip():
            self.texts.append(data.strip())

def inspect_url(url: str, auto_inspect: bool = True) -> Tuple[str, str]:
    """
    Inspects a user-supplied URL.
    Returns:
        (extracted_content: str, evidence_access_status: str)
        where evidence_access_status is one of:
        - "retrieved": Successfully fetched and inspected by ProofHire
        - "retrieval_failed": Attempted to fetch but failed or inaccessible
        - "submitted_only": Supplied as reference without automated inspection
    """
    cleaned_url = (url or "").strip()
    if not cleaned_url:
        return ("No URL was provided.", "submitted_only")

    if not auto_inspect:
        return (
            "A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.",
            "submitted_only"
        )

    if not (cleaned_url.startswith("http://") or cleaned_url.startswith("https://")):
        cleaned_url = "https://" + cleaned_url

    headers = {
        "User-Agent": "ProofHire-Evidence-Inspector/1.0 (Candidate Evidence Verification Bot)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = requests.get(cleaned_url, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            if "html" in content_type.lower() or "text" in content_type.lower() or "json" in content_type.lower():
                parser = HTMLTextExtractor()
                parser.feed(response.text)
                title = parser.title.strip()
                body_content = " ".join(parser.texts)
                body_content = re.sub(r'\s+', ' ', body_content).strip()

                if len(body_content) > 2500:
                    body_content = body_content[:2500] + "... [truncated]"

                if body_content:
                    extracted_text = (
                        f"Target URL: {cleaned_url}\n"
                        f"Page Title: {title or 'N/A'}\n"
                        f"Retrieved Page Content Snippet:\n{body_content}"
                    )
                    return (extracted_text, "retrieved")
                else:
                    return (
                        f"Target URL: {cleaned_url}\n"
                        "A project URL was supplied as supporting evidence, but its contents could not be read or were empty. Its contents have not been independently inspected by ProofHire.",
                        "retrieval_failed"
                    )
            else:
                return (
                    f"Target URL: {cleaned_url}\nContent-Type '{content_type}' is not supported for text extraction. Its contents have not been independently inspected by ProofHire.",
                    "retrieval_failed"
                )
        else:
            return (
                f"Target URL: {cleaned_url}\n"
                f"HTTP request returned status {response.status_code}. "
                "A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.",
                "retrieval_failed"
            )
    except Exception as e:
        return (
            f"Target URL: {cleaned_url}\n"
            f"Failed to access URL ({str(e)}). "
            "A project URL was supplied as supporting evidence, but its contents have not been independently inspected by ProofHire.",
            "retrieval_failed"
        )
