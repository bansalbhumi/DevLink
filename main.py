from contextlib import asynccontextmanager
from auth import verify_key
from database import get_connection, init_db
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, FileResponse
from models import ShortenRequest, ShortenResponse, StatsResponse
from shortener import generate_code, is_valid_url


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("DevLink running on Vercel + Neon!")
    yield


app = FastAPI(lifespan=lifespan)

@app.get("/")
def serve_frontend():
    # We are forcing Python to label this as a web page (HTML)
    return FileResponse("index.html", media_type="text/html")


@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest, request: Request, api_key: str = Depends(verify_key)):
    if not is_valid_url(payload.original_url):
        raise HTTPException(
            status_code=400, detail="URL must start with http:// or https://"
        )

    code = None
    # retry on collision — 62^6 options means this almost never happens
    for _ in range(3):
        candidate = generate_code()
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Postgres uses %s instead of ? for variables
                cur.execute("SELECT 1 FROM urls WHERE short_code = %s", (candidate,))
                existing = cur.fetchone()
                if not existing:
                    code = candidate
                    break

    if not code:
        raise HTTPException(
            status_code=500, detail="Failed to generate a unique short code"
        )

    # print(f"generated code: {code}")  # debug, remove later

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (short_code, original_url, api_key) VALUES (%s, %s, %s)",
                (code, payload.original_url, api_key),
            )

    # Dynamically grab the Vercel URL instead of hardcoding localhost
    base_url = str(request.base_url).rstrip('/')
    return ShortenResponse(
        short_code=code,
        short_url=f"{base_url}/{code}",
        original_url=payload.original_url,
    )


@app.get("/{code}")
def redirect_url(code: str, request: Request):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT original_url FROM urls WHERE short_code = %s", (code,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Short URL not found")

    client_ip = request.client.host if request.client else "unknown"

    # log the click before redirecting
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO clicks (short_code, ip_address) VALUES (%s, %s)",
                (code, client_ip),
            )

    return RedirectResponse(url=row["original_url"], status_code=302)


@app.get("/stats/{code}", response_model=StatsResponse)
def get_stats(code: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT original_url, created_at FROM urls WHERE short_code = %s",
                (code,),
            )
            url_row = cur.fetchone()

    if not url_row:
        raise HTTPException(status_code=404, detail="Short code not found")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                    SELECT 
                        COUNT(*) as total_clicks,
                        COUNT(DISTINCT ip_address) as unique_ips
                    FROM clicks
                    WHERE short_code = %s
                """,
                (code,),
            )
            stats_row = cur.fetchone()

    return StatsResponse(
        short_code=code,
        original_url=url_row["original_url"],
        total_clicks=stats_row["total_clicks"],
        unique_ips=stats_row["unique_ips"],
        created_at=str(url_row["created_at"]),
    )