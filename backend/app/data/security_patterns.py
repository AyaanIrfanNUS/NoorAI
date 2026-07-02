"""
Static security-related pattern lists.
Pure data — no logic. Edit here when adding new injection phrasings to screen.
"""

# Phrasings that attempt to override the assistant's instructions or role.
# Not exhaustive — a determined rephrasing can bypass this — but it screens
# out the most common injection attempts at negligible cost.
INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "disregard previous instructions",
    "disregard all previous instructions",
    "you are now",
    "system prompt",
    "new instructions:",
    "pretend you are",
    "act as if you",
    "forget your instructions",
    "reveal your system prompt",
]