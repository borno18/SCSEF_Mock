import re

# Phishing and credential patterns for pre-check
PHISHING_REGEXES = [
    # OTP patterns (English and Bengali)
    re.compile(r"(?i)\b(?:otp|one[- ]time[- ]password|ওয়ান[- ]টাইম[- ]পাসওয়ার্ড)\b"),
    # PIN patterns
    re.compile(r"(?i)\b(?:pin|পিন)\b"),
    # Password patterns
    re.compile(r"(?i)\b(?:password|পাসওয়ার্ড)\b"),
    # CVV / CVC patterns
    re.compile(r"(?i)\b(?:cvv|cvc)\b"),
    # Card number patterns
    re.compile(r"(?i)(?:card[- ]number|কার্ড[- ]নাম্বার)"),
    # "is this bKash" patterns
    re.compile(r"(?i)(?:is\s*this\s*bkash|bKash\s*ki|বিকাশ\s*কি|বিকাশ\s*নাকি|বিকাশ\s*বলছেন)"),
    # Impersonation phrases
    re.compile(
        r"(?i)(?:bKash[- ]agent|customer[- ]care|support[- ]representative|support[- ]officer|বিকাশ[- ]অফিসার|বিকাশ[- ]প্রতিনিধি|হেল্প[- ]ডেস্ক|help[- ]desk|বিকাশ[- ]হেল্প|bkash[- ]help|বিকাশ[- ]সাপোর্ট|bkash[- ]support|representative|officer)"
    )
]

# Sensitive credentials denylist patterns for summary validation
DENYLIST_REGEXES = [
    # OTP, PIN, password, CVV/CVC keywords (standalone or close word match)
    re.compile(r"(?i)\b(?:otp|one[- ]time[- ]password|ওয়ান[- ]টাইম[- ]পাসওয়ার্ড)\b"),
    re.compile(r"(?i)\b(?:pin|পিন)\b"),
    re.compile(r"(?i)\b(?:password|পাসওয়ার্ড)\b"),
    re.compile(r"(?i)\b(?:cvv|cvc)\b"),
    # Any 13-19 digit run (which could resemble a card or bank account number)
    re.compile(r"\b(?:\d[\s-]*){13,19}\b")
]

def check_phishing_signals(message: str) -> bool:
    """Scan message for phishing indicators. Returns True if any match."""
    for pattern in PHISHING_REGEXES:
        if pattern.search(message):
            return True
    return False

def clean_agent_summary(summary: str, case_type: str) -> str:
    """
    Validate agent_summary against the credentials denylist.
    If a match is found, discard the summary and return a safe template.
    """
    for pattern in DENYLIST_REGEXES:
        if pattern.search(summary):
            # Substitute with a safe template as required by the security prompt
            return f"Customer reports a {case_type} issue; see ticket for details."
    return summary
