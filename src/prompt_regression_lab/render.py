"""Variable rendering helpers."""

from __future__ import annotations

import os
import re
from typing import Any, Dict


_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def render_template(template: Any, variables: Dict[str, Any] | None = None) -> Any:
    """Render placeholders in a string with provided variables and env fallback."""
    if not isinstance(template, str):
        return template

    variables = variables or {}

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in variables:
            return str(variables[key])
        return os.environ.get(key, match.group(0))

    return _PLACEHOLDER_PATTERN.sub(replace, template)
