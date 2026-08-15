import secrets
import string

# Base62 = 62 chars, length 6 gives 62^6 = ~56 billion possible codes
# using secrets instead of random because secrets is cryptographically secure
BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase


def generate_code(length: int = 6) -> str:
  return "".join(secrets.choice(BASE62_ALPHABET) for _ in range(length))


# quick test: generate_code() gives stuff like "aB3kP9" — looks right


def is_valid_url(url: str) -> bool:
  return url.startswith("http://") or url.startswith("https://")