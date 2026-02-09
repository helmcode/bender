"""Shared Slack utilities — message splitting and formatting."""

import re

# Slack message character limit
SLACK_MSG_LIMIT = 4000


def md_to_mrkdwn(text: str) -> str:
    """Convert standard Markdown to Slack mrkdwn format."""
    lines = text.split("\n")
    result: list[str] = []

    for line in lines:
        # Headers → bold (Slack has no heading syntax)
        line = re.sub(r"^#{1,6}\s+(.+)$", r"*\1*", line)

        # Horizontal rules → empty line
        if re.match(r"^---+\s*$", line):
            result.append("")
            continue

        # Bold: **text** → *text*
        line = re.sub(r"\*\*(.+?)\*\*", r"*\1*", line)

        # Markdown links: [text](url) → <url|text>
        line = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<\2|\1>", line)

        result.append(line)

    return "\n".join(result)


def split_text(text: str, max_length: int = SLACK_MSG_LIMIT) -> list[str]:
    """Split text into chunks, preferring to break at newlines."""
    chunks: list[str] = []
    while len(text) > max_length:
        split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            split_pos = max_length
        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks
