from typing import Optional
from yarl import URL

_CANON = {
    "text/html": "html",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "docx",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    "application/vnd.ms-powerpoint": "pptx",
}
_EXTS = {
    ".html": "html", ".htm": "html",
    ".pdf": "pdf",
    ".docx": "docx", ".doc": "docx",
    ".pptx": "pptx", ".ppt": "pptx",
}

def canonical_type(header_ct: Optional[str], url: str) -> Optional[str]:
    if header_ct and header_ct.split(";")[0].strip().lower() in _CANON:
        return _CANON[header_ct.split(";")[0].strip().lower()]
    try:
        path = URL(url).path.lower()
    except Exception:
        path = url.lower()
    for ext, typ in _EXTS.items():
        if path.endswith(ext):
            return typ
    if "." not in path.split("/")[-1]:
        return "html"
    return None
