# ContextOS Frontend

A minimal React frontend for the ContextOS AI agent system.

## Features

- **Chat Interface**: Interact with the AI agent
- **Source Display**: View RAG sources for each response
- **Action Tracking**: See what tools the agent executed
- **Performance Metrics**: Monitor token usage, costs, and latency

## Setup

1. Install dependencies:

```bash
npm install
```

2. Create a `.env` file:

```bash
cp .env.example .env
```

3. Update the API URL in `.env`:

```env
VITE_API_URL=http://localhost:8000
```

4. Start the development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Tech Stack

- React 19
- TypeScript
- Vite
- TailwindCSS
- Lucide Icons

## Project Structure

```
/
├── components/
│   ├── ChatInterface.tsx    # Main chat UI
│   ├── DataViewer.tsx        # Metrics dashboard
│   └── Sidebar.tsx           # Navigation
├── services/
│   └── apiService.ts         # Backend API client
├── types.ts                  # TypeScript types
├── App.tsx                   # Main app component
└── index.tsx                 # Entry point
```

## Backend Connection

The frontend connects to the FastAPI backend at the URL specified in `VITE_API_URL`.

Make sure your backend is running before starting the frontend:

```bash
cd backend
docker-compose up -d
```

## API Endpoints Used

- `POST /agent/query` - Send chat messages
- `GET /metrics` - Get system metrics
- `GET /usage` - Get usage history
- `GET /health` - Check backend status

## Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Preview Production Build

```bash
npm run preview
```
