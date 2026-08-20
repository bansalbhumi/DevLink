# DevLink

Built this to understand how URL shorteners actually work under the hood.
Turns any URL into a 6-character short code using Base62 encoding.

Stack: FastAPI, SQLite, Docker

## Link 
[https://dev-link-lyart-eight.vercel.app/](https://dev-link-lyart-eight.vercel.app/)

## Endpoints

- `POST /shorten` — needs `X-Api-Key` header, returns short code
- `GET /{code}` — redirects to original URL, logs the click
- `GET /stats/{code}` — returns click count and unique IP count

## Run it

Using Docker:
```bash
docker-compose up
