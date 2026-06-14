"""
Application-wide constants.
"""

PRAYER_NAMES = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

# Supported Aladhan calculation method IDs.
# Method 0 (Shia Ithna-Ashari) and method 99 (Custom) are intentionally
# excluded because they require special handling or custom parameters.
VALID_CALCULATION_METHODS = {
    1, 2, 3, 4, 5,
    7, 8, 9, 10, 11,
    12, 13, 14, 15,
    16, 17, 18, 19,
    20, 21, 22, 23
}

# Maps ISO 3166-1 alpha-2 country codes to Aladhan calculation method IDs,
# used as sensible regional defaults during registration.
CALCULATION_METHOD_BY_COUNTRY: dict[str, int] = {
    # North Africa - Egyptian General Authority of Survey
    "DZ": 1,
    "MA": 1,
    "TN": 1,
    "LY": 1,

    # North America - ISNA
    "US": 2,
    "CA": 2,

    # South Asia - University of Islamic Sciences, Karachi
    "PK": 3,
    "IN": 3,
    "BD": 3,

    # Saudi Arabia - Umm al-Qura
    "SA": 4,

    # Gulf countries
    "QA": 10,  # Qatar
    "KW": 9,   # Kuwait
    "AE": 16,  # UAE / Dubai
    "BH": 8,   # Gulf Region

    # Southeast Asia
    "SG": 11,  # Majlis Ugama Islam Singapura (MUIS)
    "MY": 17,  # JAKIM Malaysia
    "ID": 20,  # Ministry of Religious Affairs Indonesia
    "BN": 17,  # Closest regional equivalent: JAKIM

    # Turkey
    "TR": 13,  # Diyanet İşleri Başkanlığı

    # Europe
    "FR": 12,  # Union Organization Islamic de France
    "BE": 12,
    "NL": 12,
    "DE": 3,   # Muslim World League
    "GB": 3,   # Muslim World League

    # Russia
    "RU": 14,  # Spiritual Administration of Muslims of Russia

    # Jordan
    "JO": 18,

    # Portugal
    "PT": 21,

    # Andorra
    "AD": 22,
}

# Fallback for unlisted countries
CALCULATION_METHOD_DEFAULT = 3  # Muslim World League (MWL)