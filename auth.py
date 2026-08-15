# TODO: pull this from environment variable before any real deployment
from fastapi import Header, HTTPException

VALID_KEYS = {"bhumi-devlink-2024"}


def verify_key(x_api_key: str = Header(...)):
  if x_api_key not in VALID_KEYS:
    raise HTTPException(status_code=401, detail="Invalid API key")
  return x_api_key