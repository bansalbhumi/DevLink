from pydantic import BaseModel


class ShortenRequest(BaseModel):
  original_url: str


class ShortenResponse(BaseModel):
  short_code: str
  short_url: str
  original_url: str


class StatsResponse(BaseModel):
  short_code: str
  original_url: str
  total_clicks: int
  unique_ips: int
  created_at: str