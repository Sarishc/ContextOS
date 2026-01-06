# Frontend Setup Guide

## Quick Start

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Create environment file**:
   ```bash
   echo "VITE_API_URL=http://localhost:8000" > .env
   ```

3. **Start the backend** (in another terminal):
   ```bash
   cd backend
   docker-compose up -d
   ```

4. **Start the frontend**:
   ```bash
   npm run dev
   ```

5. **Open in browser**:
   Navigate to `http://localhost:3000`

## Features

### Chat Interface
- Send messages to the AI agent
- View responses with sources and tool calls
- Track token usage and costs per query

### Sources Display
- Each response shows the RAG sources used
- View document titles and content snippets
- See relevance scores for each source

### Actions Tracking
- View which tools were called by the agent
- See the arguments passed to each tool
- Monitor execution status

### Performance Dashboard
- Total requests and tokens used
- Average latency and total costs
- Requests breakdown by endpoint
- Recent query history with metrics

## API Connection

The frontend connects to your FastAPI backend. Make sure:

1. Backend is running on the port specified in `.env`
2. CORS is enabled in the backend
3. All required endpoints are available:
   - `POST /agent/query`
   - `GET /metrics`
   - `GET /usage`
   - `GET /health`

## Troubleshooting

### Backend Connection Failed
- Check if backend is running: `docker-compose ps`
- Verify the API URL in `.env`
- Check backend logs: `docker-compose logs -f api`

### Port Already in Use
- Change the port in `vite.config.ts`
- Or kill the process using port 3000

### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Clear Vite cache: `rm -rf node_modules/.vite`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL |

## Development

### Project Structure
```
/
├── components/           # React components
│   ├── ChatInterface.tsx # Chat UI
│   ├── DataViewer.tsx    # Metrics dashboard
│   └── Sidebar.tsx       # Navigation
├── services/             # API services
│   └── apiService.ts     # Backend client
├── types.ts              # TypeScript types
├── App.tsx               # Main component
└── index.tsx             # Entry point
```

### Adding New Features

1. **Add a new component**:
   ```bash
   touch components/NewComponent.tsx
   ```

2. **Update types**:
   Edit `types.ts` to add new interfaces

3. **Add API methods**:
   Edit `services/apiService.ts` to add new endpoints

### Building for Production

```bash
npm run build
```

Output will be in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Technology Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling (via CDN)
- **Lucide React** - Icons

## Next Steps

- Add authentication
- Implement real-time updates with WebSockets
- Add more visualization for metrics
- Create admin dashboard
- Add export functionality for chat history

