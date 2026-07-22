# FinAgent React frontend

This Vite/React app connects to the FastAPI service in `../backend`.

```bash
npm install
npm run dev
```

The frontend runs at `http://localhost:8501`. During local development, Vite
proxies `/api` requests to `http://localhost:8000`. For a deployed backend, copy
`.env.example` to `.env` and set `VITE_API_BASE_URL` to its public base URL.
