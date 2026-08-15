from contextlib import asynccontextmanager
from auth import verify_key
from database import get_connection, init_db
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from models import ShortenRequest, ShortenResponse, StatsResponse
from shortener import generate_code, is_valid_url


@asynccontextmanager
async def lifespan(app: FastAPI):
  init_db()
  print("DevLink running")
  yield


app = FastAPI(lifespan=lifespan)


@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest, api_key: str = Depends(verify_key)):
  if not is_valid_url(payload.original_url):
    raise HTTPException(
        status_code=400, detail="URL must start with http:// or https://"
    )

  code = None
  # retry on collision — 62^6 options means this almost never happens
  for _ in range(3):
    candidate = generate_code()
    with get_connection() as conn:
      existing = conn.execute(
          "SELECT 1 FROM urls WHERE short_code = ?", (candidate,)
      ).fetchone()
      if not existing:
        code = candidate
        break

  if not code:
    raise HTTPException(
        status_code=500, detail="Failed to generate a unique short code"
    )

  # print(f"generated code: {code}")  # debug, remove later

  with get_connection() as conn:
    conn.execute(
        "INSERT INTO urls (short_code, original_url, api_key) VALUES (?, ?,"
        " ?)",
        (code, payload.original_url, api_key),
    )
    conn.commit()

  return ShortenResponse(
      short_code=code,
      short_url=f"http://localhost:8000/{code}",
      original_url=payload.original_url,
  )


@app.get("/{code}")
def redirect_url(code: str, request: Request):
  with get_connection() as conn:
    row = conn.execute(
        "SELECT original_url FROM urls WHERE short_code = ?", (code,)
    ).fetchone()

  if not row:
    raise HTTPException(status_code=404, detail="Short URL not found")

  client_ip = request.client.host if request.client else "unknown"

  # log the click before redirecting
  with get_connection() as conn:
    conn.execute(
        "INSERT INTO clicks (short_code, ip_address) VALUES (?, ?)",
        (code, client_ip),
    )
    conn.commit()

  return RedirectResponse(url=row["original_url"], status_code=302)


@app.get("/stats/{code}", response_model=StatsResponse)
def get_stats(code: str):
  with get_connection() as conn:
    url_row = conn.execute(
        "SELECT original_url, created_at FROM urls WHERE short_code = ?",
        (code,),
    ).fetchone()

  if not url_row:
    raise HTTPException(status_code=404, detail="Short code not found")

  with get_connection() as conn:
    stats_row = conn.execute(
        """
            SELECT 
                COUNT(*) as total_clicks,
                COUNT(DISTINCT ip_address) as unique_ips
            FROM clicks
            WHERE short_code = ?
        """,
        (code,),
    ).fetchone()

  return StatsResponse(
      short_code=code,
      original_url=url_row["original_url"],
      total_clicks=stats_row["total_clicks"],
      unique_ips=stats_row["unique_ips"],
      created_at=str(url_row["created_at"]),
  )