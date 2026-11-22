"""Keep the exact source assignment PDF in the repository.

This is an offline integrity test, not a Plant Simulation runtime check.
"""
from pathlib import Path
import hashlib


def test_original_assignment_pdf_is_unchanged():
    pdf = Path(__file__).resolve().parents[1] / "docs" / "assignment" / "PS_beadando_original.pdf"
    data = pdf.read_bytes()
    assert len(data) == 382278
    assert data.startswith(b"%PDF-1.7")
    assert hashlib.sha256(data).hexdigest() == (
        "167c81993741f6a333a08109e595cc12b98ed03aa1973d562886030f0aed06f1"
    )
