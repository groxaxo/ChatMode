"""
Content filtering module for ChatMode.

This module provides content filtering capabilities to block, censor, or flag
inappropriate content based on configurable word lists and rules.
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class FilterResult:
    """Result of content filtering."""

    allowed: bool
    content: str
    action: str  # "block", "censor", "warn", "allow"
    matched_words: List[str]
    message: Optional[str] = None


class ContentFilter:
    """Content filter for agent conversations."""

    def __init__(
        self,
        enabled: bool = True,
        blocked_words: Optional[List[str]] = None,
        action: str = "block",
        filter_message: Optional[str] = None,
    ):
        self.enabled = enabled
        self.blocked_words = blocked_words or []
        self.action = action
        self.filter_message = (
            filter_message
            or "This message contains inappropriate content and has been blocked."
        )
        self._compiled_patterns: List[Tuple[str, re.Pattern]] = []
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for blocked words."""
        self._compiled_patterns = []
        for word in self.blocked_words:
            if word:
                # Escape special regex characters and make case-insensitive
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                self._compiled_patterns.append((word, pattern))

    def check_content(self, content: str) -> FilterResult:
        """
        Check content against blocked words.

        Args:
            content: The content to check

        Returns:
            FilterResult with filtering outcome
        """
        if not self.enabled or not self.blocked_words:
            return FilterResult(
                allowed=True, content=content, action="allow", matched_words=[]
            )

        matched_words = []
        for word, pattern in self._compiled_patterns:
            if pattern.search(content):
                matched_words.append(word)

        if not matched_words:
            return FilterResult(
                allowed=True, content=content, action="allow", matched_words=[]
            )

        # Handle different filter actions
        if self.action == "block":
            return FilterResult(
                allowed=False,
                content=content,
                action="block",
                matched_words=matched_words,
                message=self.filter_message,
            )

        elif self.action == "censor":
            censored_content = content
            for word, pattern in self._compiled_patterns:
                if word in matched_words:
                    # Replace with asterisks of same length
                    censored_content = pattern.sub(
                        lambda m: "*" * len(m.group()), censored_content
                    )
            return FilterResult(
                allowed=True,
                content=censored_content,
                action="censor",
                matched_words=matched_words,
            )

        elif self.action == "warn":
            return FilterResult(
                allowed=True,
                content=content,
                action="warn",
                matched_words=matched_words,
                message=f"Warning: Content flagged for containing: {', '.join(matched_words)}",
            )

        # Default: allow
        return FilterResult(
            allowed=True, content=content, action="allow", matched_words=[]
        )

    def filter_content(self, content: str) -> Tuple[bool, str, Optional[str]]:
        """
        Filter content and return result.

        Args:
            content: The content to filter

        Returns:
            Tuple of (allowed, filtered_content, message)
        """
        result = self.check_content(content)

        if result.action == "block":
            return False, result.message, result.message

        return result.allowed, result.content, result.message


def create_filter_from_permissions(permissions: Optional[Dict]) -> ContentFilter:
    """
    Create a ContentFilter from agent permissions dict.

    Args:
        permissions: Agent permissions dictionary

    Returns:
        Configured ContentFilter instance
    """
    if not permissions:
        return ContentFilter(enabled=False)

    return ContentFilter(
        enabled=permissions.get("filter_enabled", True),
        blocked_words=permissions.get("blocked_words", []),
        action=permissions.get("filter_action", "block"),
        filter_message=permissions.get("filter_message"),
    )
