# DevLink 🔗
A high-performance, serverless URL shortening service with built-in click analytics. 

**[Live Demo](https://dev-link-lyart-eight.vercel.app/)** 

## 🚀 Tech Stack
* **Backend:** Python, FastAPI
* **Database:** PostgreSQL (Neon)
* **Deployment:** Vercel (Serverless Functions)
* **Algorithms:** Base62 Encoding

## ✨ Key Features
* **Collision-Resistant Shortening:** Utilizes Base62 encoding with a retry-logic mechanism to generate highly unique, compact short codes.
* **Click Analytics:** Tracks total visits and unique IP addresses per link, stored efficiently in PostgreSQL.
* **Optimized Routing:** Implements a `UNIQUE INDEX` on short codes for $O(\log n)$ database lookups, ensuring lightning-fast redirects.
* **Stateless Architecture:** Fully decoupled, serverless deployment on Vercel for infinite horizontal scaling.

## 🛠️ Local Setup
1. Clone the repository: `git clone https://github.com/bansalbhumi/DevLink.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file based on `.env.example` and add your PostgreSQL connection string.
4. Run the server: `uvicorn main:app --reload`
