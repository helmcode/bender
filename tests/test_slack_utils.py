"""Tests for the Slack utilities module."""

from bender.slack_utils import SLACK_MSG_LIMIT, md_to_mrkdwn, split_text


class TestSlackMsgLimit:
    """Tests for the SLACK_MSG_LIMIT constant."""

    def test_limit_value(self) -> None:
        """SLACK_MSG_LIMIT is 4000 characters."""
        assert SLACK_MSG_LIMIT == 4000


class TestSplitText:
    """Tests for the split_text function."""

    def test_short_text_no_split(self) -> None:
        """Text under limit is returned as single chunk."""
        result = split_text("short text", 100)
        assert result == ["short text"]

    def test_split_at_newline(self) -> None:
        """Prefers splitting at newlines."""
        text = "line1\nline2\nline3"
        result = split_text(text, 10)
        assert result[0] == "line1"
        assert "line2" in result[1]

    def test_split_at_limit_when_no_newline(self) -> None:
        """Splits at max_length when no newline is available."""
        text = "a" * 20
        result = split_text(text, 10)
        assert result[0] == "a" * 10
        assert result[1] == "a" * 10

    def test_empty_text_returns_empty_list(self) -> None:
        """Empty text returns empty list."""
        result = split_text("", 100)
        assert result == []

    def test_exact_limit_no_split(self) -> None:
        """Text exactly at limit is returned as single chunk."""
        text = "a" * 100
        result = split_text(text, 100)
        assert result == ["a" * 100]

    def test_multiple_splits(self) -> None:
        """Text requiring multiple splits produces correct chunks."""
        text = "a" * 30
        result = split_text(text, 10)
        assert len(result) == 3
        assert all(chunk == "a" * 10 for chunk in result)

    def test_default_max_length(self) -> None:
        """Default max_length uses SLACK_MSG_LIMIT."""
        short_text = "hello"
        result = split_text(short_text)
        assert result == ["hello"]

    def test_newline_stripped_between_chunks(self) -> None:
        """Leading newlines are stripped from subsequent chunks."""
        text = "abcde\n\n\nfghij"
        result = split_text(text, 6)
        assert result[0] == "abcde"
        assert result[1] == "fghij"


class TestMdToMrkdwn:
    """Tests for the md_to_mrkdwn function."""

    def test_headers_to_bold(self) -> None:
        """Markdown headers become bold text."""
        assert md_to_mrkdwn("## Hello") == "*Hello*"
        assert md_to_mrkdwn("### World") == "*World*"
        assert md_to_mrkdwn("# Title") == "*Title*"

    def test_bold_double_asterisk(self) -> None:
        """Double asterisks become single asterisks."""
        assert md_to_mrkdwn("this is **bold** text") == "this is *bold* text"

    def test_links(self) -> None:
        """Markdown links become Slack links."""
        assert md_to_mrkdwn("[click](https://example.com)") == "<https://example.com|click>"

    def test_horizontal_rule(self) -> None:
        """Horizontal rules become empty lines."""
        assert md_to_mrkdwn("above\n---\nbelow") == "above\n\nbelow"

    def test_plain_text_unchanged(self) -> None:
        """Plain text passes through unchanged."""
        assert md_to_mrkdwn("just plain text") == "just plain text"

    def test_code_blocks_preserved(self) -> None:
        """Code blocks are not modified."""
        text = "```\nkubectl get pods\n```"
        assert md_to_mrkdwn(text) == text

    def test_combined(self) -> None:
        """Multiple conversions in one message."""
        md = "## Task\n**Client:** helmcode\n[Link](https://example.com)"
        expected = "*Task*\n*Client:* helmcode\n<https://example.com|Link>"
        assert md_to_mrkdwn(md) == expected
