from slugify import slugify


def make_slug(value: str, fallback: str) -> str:
    slug = slugify(value, max_length=255)
    return slug or fallback
