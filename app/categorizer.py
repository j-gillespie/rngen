"""Sort raw release notes into template sections by relevance."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

ISSUE_ID_PATTERN = re.compile(
    r"\b(?:BUG|ISSUE|TICKET|DEFECT|ACME)[-_]?\d+\b",
    re.IGNORECASE,
)
KNOWN_ISSUE_LINE = re.compile(
    r"^\s*(?:\[?((?:BUG|ISSUE|TICKET|DEFECT|ACME)[-_]?\d+)\]?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*$",
    re.IGNORECASE,
)
RESOLVED_ISSUE_LINE = re.compile(
    r"^\s*(?:\[?((?:BUG|ISSUE|TICKET|DEFECT|ACME)[-_]?\d+)\]?)\s*[:\-]?\s*(.+?)\s*$",
    re.IGNORECASE,
)

SECTION_KEYWORDS: dict[str, tuple[str, ...]] = {
    "overview": (
        "overview",
        "summary",
        "scope",
        "goal",
        "highlight",
        "release includes",
        "high-level",
        "high level",
    ),
    "new_features": (
        "new feature",
        "new capability",
        "added",
		"new",
        "introduces",
        "enhancement",
        "improvement",
        "performance",
        "workflow",
        "user interface",
        " ui ",
        "dashboard",
        "capability",
        "supports",
        "now allows",
        "enables",
    ),
    "resolved_issues": (
        "fixed",
        "resolved",
        "corrected",
        "patched",
        "addressed",
        "bug fix",
        "no longer",
        "issue fixed",
    ),
    "known_issues": (
        "known issue",
        "workaround",
        "limitation",
        "unresolved",
        "still occurs",
        "does not yet",
        "pending fix",
        "temporary",
    ),
    "system_requirements": (
        "requirement",
        "compatible",
        "compatibility",
        "windows",
        "linux",
        "macos",
        "mac os",
        "platform",
        "hardware",
        "memory",
        "disk space",
        "processor",
        "dependency",
        "dependencies",
        ".net",
        "java",
        "sql server",
        "minimum",
        "supported os",
    ),
    "installation": (
        "install",
        "installation",
        "setup",
        "deploy",
        "upgrade",
        "update",
        "patch",
        "uninstall",
        "msi",
        "installer",
        "download",
        "run the",
        "extract",
        "configure",
    ),
    "technical_support": (
        "support",
        "contact",
        "help desk",
        "report an issue",
        "service desk",
        "email",
        "phone",
    ),
}


@dataclass
class CategorizedNotes:
    overview: list[str] = field(default_factory=list)
    new_features: list[str] = field(default_factory=list)
    resolved_issues: list[str] = field(default_factory=list)
    known_issues: list[str] = field(default_factory=list)
    system_requirements: list[str] = field(default_factory=list)
    installation: list[str] = field(default_factory=list)
    technical_support: list[str] = field(default_factory=list)


def _normalize_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"^[-*•]\s+", "", line)
    line = re.sub(r"^\d+[.)]\s+", "", line)
    return line.strip()


def _split_details(details: str) -> list[str]:
    chunks: list[str] = []
    paragraph: list[str] = []

    for raw_line in details.splitlines():
        line = _normalize_line(raw_line)
        if not line:
            if paragraph:
                chunks.append(" ".join(paragraph))
                paragraph = []
            continue

        if ISSUE_ID_PATTERN.search(line) or len(line) < 120:
            if paragraph:
                chunks.append(" ".join(paragraph))
                paragraph = []
            chunks.append(line)
        else:
            paragraph.append(line)

    if paragraph:
        chunks.append(" ".join(paragraph))

    return [chunk for chunk in chunks if chunk.strip()]


def _score_section(text: str, section: str) -> int:
    lowered = f" {text.lower()} "
    score = sum(2 for keyword in SECTION_KEYWORDS[section] if keyword in lowered)
    if section == "resolved_issues" and RESOLVED_ISSUE_LINE.match(text):
        score += 5
    if section == "known_issues" and (
        KNOWN_ISSUE_LINE.match(text) or "workaround" in lowered
    ):
        score += 5
    if section == "resolved_issues" and ISSUE_ID_PATTERN.search(text):
        if any(word in lowered for word in ("fix", "resolved", "corrected", "patched")):
            score += 4
    if section == "known_issues" and ISSUE_ID_PATTERN.search(text):
        if any(word in lowered for word in ("known", "workaround", "limitation")):
            score += 4
    return score


def _classify_chunk(text: str) -> str:
    known_match = KNOWN_ISSUE_LINE.match(text)
    if known_match:
        return "known_issues"

    resolved_match = RESOLVED_ISSUE_LINE.match(text)
    if resolved_match and "|" not in text:
        return "resolved_issues"

    scores = {section: _score_section(text, section) for section in SECTION_KEYWORDS}
    best_section, best_score = max(scores.items(), key=lambda item: item[1])

    if best_score == 0:
        if ISSUE_ID_PATTERN.search(text):
            if "workaround" in text.lower() or "|" in text:
                return "known_issues"
            return "resolved_issues"
        return "overview"

    return best_section


def _format_resolved_issue(text: str, index: int) -> str:
    match = RESOLVED_ISSUE_LINE.match(text)
    if match:
        issue_id, description = match.group(1).upper(), match.group(2).strip()
        if not issue_id.startswith("["):
            issue_id = issue_id.replace("_", "-")
        return f"[{issue_id}] {description}"

    issue_match = ISSUE_ID_PATTERN.search(text)
    if issue_match:
        issue_id = issue_match.group(0).upper().replace("_", "-")
        description = ISSUE_ID_PATTERN.sub("", text).strip(" :-")
        description = re.sub(
            r"^(?:fixed|resolved|corrected|patched)\s+",
            "",
            description,
            flags=re.IGNORECASE,
        ).strip()
        return f"[{issue_id}] {description or text}"

    return f"[BUG-{index:03d}] {text}"


def _format_known_issue(text: str, index: int) -> str:
    match = KNOWN_ISSUE_LINE.match(text)
    if match:
        issue_id = match.group(1).upper().replace("_", "-")
        description = match.group(2).strip()
        workaround = match.group(3).strip() or "None."
        return f"[{issue_id}] | {description} | {workaround}"

    issue_match = ISSUE_ID_PATTERN.search(text)
    if issue_match:
        issue_id = issue_match.group(0).upper().replace("_", "-")
        remainder = ISSUE_ID_PATTERN.sub("", text).strip(" :-")
        workaround = "None."
        if "workaround" in remainder.lower():
            parts = re.split(r"workaround\s*:?\s*", remainder, flags=re.IGNORECASE)
            if len(parts) == 2:
                remainder, workaround = parts[0].strip(" |"), parts[1].strip() or "None."
        return f"[{issue_id}] | {remainder or text} | {workaround}"

    return f"[BUG-{index:03d}] | {text} | None."


def categorize_details(details: str) -> CategorizedNotes:
    notes = CategorizedNotes()
    resolved_counter = 1
    known_counter = 1

    for chunk in _split_details(details):
        section = _classify_chunk(chunk)
        if section == "resolved_issues":
            notes.resolved_issues.append(_format_resolved_issue(chunk, resolved_counter))
            resolved_counter += 1
        elif section == "known_issues":
            notes.known_issues.append(_format_known_issue(chunk, known_counter))
            known_counter += 1
        else:
            getattr(notes, section).append(chunk)

    if not notes.overview and (
        notes.new_features
        or notes.resolved_issues
        or notes.known_issues
        or notes.system_requirements
        or notes.installation
    ):
        feature_count = len(notes.new_features)
        fix_count = len(notes.resolved_issues)
        notes.overview.append(
            f"This release delivers {feature_count} new feature update(s) "
            f"and resolves {fix_count} issue(s)."
        )

    return notes
