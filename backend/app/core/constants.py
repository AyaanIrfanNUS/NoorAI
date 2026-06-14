"""
Application-wide constants.
"""

PRAYER_NAMES = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

# Valid Aladhan calculation method IDs (1-15, excluding 6 which is a
# duplicate of method 2). Method 0 (Shia Ithna-Ansari) and 99 (custom)
# are intentionally excluded from this app's supported methods.
VALID_CALCULATION_METHODS = {1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15}