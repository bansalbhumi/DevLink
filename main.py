from contextlib import asynccontextmanager
from auth import verify_key
from database import get_connection, init_db
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from models import ShortenRequest, ShortenResponse, StatsResponse
from shortener import generate_code, is_valid_url

# We bake the HTML directly into the code so Vercel can never lose the file!
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevLink Shortener</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
        input { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box; }
        button { width: 90%; padding: 10px; background-color: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; margin-top: 10px; }
        button:hover { background-color: #2980b9; }
        #result { margin-top: 20px; padding: 15px; border-radius: 6px; display: none; background-color: #e8f8f5; border-left: 4px solid #2ecc71; word-wrap: break-word; }
        a { color: #3498db; font-weight: bold; text-decoration: none; }
    </style>
</head>
<body>
<div class="container">
    <h1>DevLink</h1>
    <input type="text" id="urlInput" placeholder="Enter long URL (https://...)" required>
    <input type="password" id="apiKeyInput" value="bhumi-devlink-2024" placeholder="API Key">
    <button onclick="shortenUrl()">Shorten URL</button>
    <div id="result"></div>
</div>
<script>
    async function shortenUrl() {
        const url = document.getElementById('urlInput').value;
        const apiKey = document.getElementById('apiKeyInput').value;
        const resultDiv = document.getElementById('result');
        
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = 'Shortening...';

        try {
            const response = await fetch('/shorten', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Api-Key': apiKey
                },
                body: JSON.stringify({ original_url: url })
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Failed to shorten URL');
            }
            resultDiv.innerHTML = `
                <p>Success! Your short link:</p>
                <a href="${data.short_url}" target="_blank">${data.short_url}</a>
            `;
        } catch (error) {
            resultDiv.innerHTML = `<span style="color:red;">Error: ${error.message}</span>`;
        }
    }
</script>
</body>
</html>
"""

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("DevLink running on Vercel + Neon!")
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def serve_frontend():
    # Return the baked-in HTML string directly
    return HTMLResponse(content=FRONTEND_HTML)

@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(payload: ShortenRequest, request: Request, api_key: str = Depends(verify_key)):
    if not is_valid_url(payload.original_url):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    code = None
    for _ in range(3):
        candidate = generate_code()
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM urls WHERE short_code = %s", (candidate,))
                existing = cur.fetchone()
                if not existing:
                    code = candidate
                    break

    if not code:
        raise HTTPException(status_code=500, detail="Failed to generate a unique short code")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (short_code, original_url, api_key) VALUES (%s, %s, %s)",
                (code, payload.original_url, api_key),
            )

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
            cur.execute("SELECT original_url, created_at FROM urls WHERE short_code = %s", (code,))
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