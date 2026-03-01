import re

DANGEROUS_PATTERNS = [
    re.compile(r"url\s*\(", re.IGNORECASE),
    re.compile(r"@import", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"behavior\s*:", re.IGNORECASE),
    re.compile(r"-moz-binding", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
]


def sanitize_css(css: str) -> str:
    """Remove dangerous CSS constructs while preserving safe rules."""
    sanitized = css
    for pattern in DANGEROUS_PATTERNS:
        sanitized = pattern.sub("/* removed */", sanitized)
    return sanitized


def is_css_safe(css: str) -> bool:
    """Check if CSS contains any dangerous patterns."""
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(css):
            return False
    return True
