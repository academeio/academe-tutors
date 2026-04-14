"""TutorBot soul templates."""

from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent

SOUL_TEMPLATE = (_TEMPLATE_DIR / "SOUL.md").read_text()
