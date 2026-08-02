# utils/helpers.py

import jdatetime


# jdatetime.weekday():
# 0 = شنبه
# 1 = یکشنبه
# 2 = دوشنبه
# 3 = سه‌شنبه
# 4 = چهارشنبه
# 5 = پنجشنبه
# 6 = جمعه

PERSIAN_WEEKDAYS = {
    0: "شنبه",
    1: "یکشنبه",
    2: "دوشنبه",
    3: "سه‌شنبه",
    4: "چهارشنبه",
    5: "پنجشنبه",
    6: "جمعه",
}


def to_jalali_date(
    date_string: str,
) -> str:

    try:

        year, month, day = map(
            int,
            date_string.split("-"),
        )

        jalali = jdatetime.date.fromgregorian(
            year=year,
            month=month,
            day=day,
        )

        return jalali.strftime(
            "%Y/%m/%d"
        )

    except (
        ValueError,
        TypeError,
    ):

        return date_string


def to_persian_digits(
    value: str,
) -> str:

    translation = str.maketrans(
        "0123456789",
        "۰۱۲۳۴۵۶۷۸۹",
    )

    return str(value).translate(
        translation
    )


def to_persian_date(
    date_string: str,
) -> str:

    return to_persian_digits(
        to_jalali_date(
            date_string
        )
    )


def to_short_persian_date(
    date_string: str,
) -> str:

    try:

        year, month, day = map(
            int,
            date_string.split("-"),
        )

        jalali = jdatetime.date.fromgregorian(
            year=year,
            month=month,
            day=day,
        )

        short_year = (
            jalali.year % 100
        )

        result = (
            f"{short_year:02d}/"
            f"{jalali.month:02d}/"
            f"{jalali.day:02d}"
        )

        return to_persian_digits(
            result
        )

    except (
        ValueError,
        TypeError,
    ):

        return date_string


def to_date_label(
    date_string: str,
) -> str:

    try:

        year, month, day = map(
            int,
            date_string.split("-"),
        )

        jalali = (
            jdatetime.date.fromgregorian(
                year=year,
                month=month,
                day=day,
            )
        )

        weekday = PERSIAN_WEEKDAYS[
            jalali.weekday()
        ]

        return (
            f"{weekday} - "
            f"{to_short_persian_date(date_string)}"
        )

    except (
        ValueError,
        TypeError,
        KeyError,
    ):

        return date_string