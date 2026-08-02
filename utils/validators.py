# utils/validators.py

import re


PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"


_DIGIT_TRANSLATION = str.maketrans(
    PERSIAN_DIGITS + ARABIC_DIGITS,
    ENGLISH_DIGITS + ENGLISH_DIGITS,
)


def normalize_digits(
    value: str,
) -> str:

    return str(value).translate(
        _DIGIT_TRANSLATION
    )


def normalize_text(
    value: str,
) -> str:

    value = str(value).strip()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value


def validate_full_name(
    value: str,
) -> bool:

    value = normalize_text(
        value
    )

    if not value:
        return False

    if len(value) < 3:
        return False

    if len(value) > 100:
        return False

    return bool(
        re.fullmatch(
            r"[\u0600-\u06FFa-zA-Z]+"
            r"(?: [\u0600-\u06FFa-zA-Z]+)+",
            value,
        )
    )


def split_full_name(
    value: str,
) -> tuple[str, str]:

    value = normalize_text(
        value
    )

    parts = value.split(
        " "
    )

    if len(parts) < 2:
        return (
            value,
            "",
        )

    return (
        parts[0],
        " ".join(
            parts[1:]
        ),
    )


def validate_national_id(
    value: str,
) -> bool:

    value = normalize_digits(
        value.strip()
    )

    if not re.fullmatch(
        r"\d{10}",
        value,
    ):
        return False

    # Reject the well-known invalid
    # repeated-digit national IDs.
    if len(set(value)) == 1:
        return False

    digits = [
        int(char)
        for char in value
    ]

    checksum = sum(
        digits[index]
        * (10 - index)
        for index in range(9)
    )

    remainder = checksum % 11

    control = digits[9]

    if remainder < 2:
        return control == remainder

    return control == 11 - remainder


def validate_phone_number(
    value: str,
) -> bool:

    value = normalize_digits(
        value.strip()
    )

    return bool(
        re.fullmatch(
            r"09\d{9}",
            value,
        )
    )


def validate_gender(
    value: str,
) -> bool:

    value = normalize_text(
        value
    )

    return value in {
        "آقا",
        "خانم",
    }


def validate_insurance(
    value: str,
) -> bool:

    value = normalize_text(
        value
    )

    return value in {
        "سلامت",
        "تامین اجتماعی",
        "تأمین اجتماعی",
        "نیروهای مسلح",
        "بدون بیمه",
    }