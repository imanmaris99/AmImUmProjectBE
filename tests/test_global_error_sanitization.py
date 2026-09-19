import re
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1] / "app"
SCAN_ROOTS = [
    APP_ROOT / "services",
    APP_ROOT / "utils",
]

RAW_ERROR_MARKERS = [
    "message=str(e)",
    "detail=str(e)",
    "Invalid response from RajaOngkir API",
    "Unknown error occurred.",
    "No shipping cost data found.",
    "No shipping cost details data found.",
    "Cloudinary upload gagal:",
    "Error creating user in Firebase:",
    "Failed to delete Firebase user:",
    "Unexpected error while deleting Firebase user:",
    "Brevo API did not respond",
    "SMTP server did not respond",
    "SMTP authentication failed",
    "Error sending email:",
]

RAW_ERROR_PATTERNS = [
    re.compile(r"message\s*=\s*f[\"'].*\{\s*str\((?:e|error|db_error|ie|de|te)\)\s*\}.*[\"']"),
    re.compile(r"detail\s*=\s*f[\"'].*\{\s*str\((?:e|error|db_error|ie|de|te)\)\s*\}.*[\"']"),
    re.compile(r"[\"']message[\"']\s*:\s*f[\"'].*\{\s*str\((?:e|error|db_error|ie|de|te)\)\s*\}.*[\"']"),
    re.compile(r"[\"']detail[\"']\s*:\s*f[\"'].*\{\s*str\((?:e|error|db_error|ie|de|te)\)\s*\}.*[\"']"),
    re.compile(r"message\s*=\s*[\"'][^\n]*[\"']\s*\+\s*str\((?:e|error|db_error|ie|de|te)\)"),
    re.compile(r"detail\s*=\s*[\"'][^\n]*[\"']\s*\+\s*str\((?:e|error|db_error|ie|de|te)\)"),
    re.compile(r"[\"']message[\"']\s*:\s*[\"'][^\n]*[\"']\s*\+\s*str\((?:e|error|db_error|ie|de|te)\)"),
    re.compile(r"message\s*=\s*f[\"'].*response\.text.*[\"']"),
    re.compile(r"detail\s*=\s*f[\"'].*response\.text.*[\"']"),
    re.compile(r"[\"']message[\"']\s*:\s*f[\"'].*response\.text.*[\"']"),
    re.compile(r"[\"']detail[\"']\s*:\s*f[\"'].*response\.text.*[\"']"),
    re.compile(r"Database conflict:\s*\{"),
    re.compile(r"Failed to reset password:\s*\{"),
    re.compile(r"Failed to create access token:\s*\{"),
    re.compile(r"Invalid or expired token:\s*\{"),
    re.compile(r"Kesalahan sistem database:\s*\{"),
    re.compile(r"Kesalahan tak terduga:\s*\{"),
    re.compile(r"Kesalahan jaringan ke Midtrans\.\s*\{"),
]


def _without_comments(source: str) -> str:
    lines = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def test_public_errors_do_not_expose_raw_exception_messages():
    offenders: list[str] = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            source = _without_comments(path.read_text())
            for marker in RAW_ERROR_MARKERS:
                if marker in source:
                    offenders.append(f"{path.relative_to(APP_ROOT)}: {marker}")
            for pattern in RAW_ERROR_PATTERNS:
                if pattern.search(source):
                    offenders.append(f"{path.relative_to(APP_ROOT)}: {pattern.pattern}")

    assert offenders == []
