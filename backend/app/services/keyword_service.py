def check_keyword(text: str, page_number: int) -> list[dict]:
    keywords = ["kritisch", "dringend", "abnormal", "notfall", "sofort"]
    return [{"keyword": kw, "page_number": page_number} for kw in keywords if kw in text.lower()]
