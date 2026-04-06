from __future__ import annotations

from common import latex_escape


def render_catalog_and_timing(payload: dict[str, object]) -> str:
    case_count = len(list(payload.get("cases") or []))
    procedure_count = sum(1 for line in str(payload.get("procedures_markdown_text") or "").splitlines() if line.strip().startswith("- "))
    return (
        r"\subsection{Catalogue And Timing Summary}"
        + "\n"
        + latex_escape(
            f"The staged draft currently covers {case_count} experiment cases and {procedure_count} listed procedure steps."
        )
        + "\n"
    )
