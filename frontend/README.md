# ForgeOS Mission Control Frontend

The frontend is the Next.js 16 Mission Control application for ForgeOS. It starts repository analysis through the FastAPI backend and renders every live result from the SSE stream.

## Local Development

```bash
npm ci
npm run dev
```

Open `http://localhost:3000`. The expected backend URL is `http://localhost:8000` by default. To override it, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Validation

```bash
npx tsc --noEmit
npm run lint
npm run build
```

The root [README](../README.md) and [Frontend Guide](../frontend.md) document the complete product architecture, dashboard behavior, API contract, and local runtime.
