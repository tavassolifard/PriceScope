
def normalize_price(price):
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    english_digits = "0123456789"

    translation = str.maketrans(persian_digits, english_digits)

    return int(price.translate(translation).replace(",", "").replace("٬", "").strip())