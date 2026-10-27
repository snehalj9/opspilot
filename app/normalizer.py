import re

ID_PATTERN = re.compile(r"\b[A-Z]\d{3,}\b")   # P48213, O12345
NUMBER_PATTERN = re.compile(r"\d+")           # 30000, 503, 123


def normalize(message):
    """Replace IDs and numbers with placeholders to get a 'template'."""
    message = ID_PATTERN.sub("<ID>", message)
    message = NUMBER_PATTERN.sub("<NUM>", message)
    return message