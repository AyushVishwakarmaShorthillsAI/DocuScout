# DocuScout Frontend

Vanilla JavaScript frontend for the DocuScout application.

## Structure

```
frontend/
├── index.html      # Main HTML file
├── css/
│   └── style.css  # All styles
├── js/
│   ├── api.js     # API client for backend communication
│   └── app.js     # Main application logic
└── README.md      # This file
```

## Usage

1. Make sure the backend is running on `http://localhost:8001`
2. Open `index.html` in your web browser
   - You can double-click the file, or
   - Use a local server: `python -m http.server 3000` (then visit http://localhost:3000)

## Features

- **Chat Interface**: Send messages to the DocuScout orchestrator agent
- **Document Ingestion**: Upload documents from the DB folder
- **Agent Status**: View all available agents and their status
- **Document Status**: Track ingested documents
- **Risk Analysis**: View risk summaries (when available)

## API Endpoints

The frontend communicates with the backend API at `http://localhost:8001/api`:

- `POST /api/chat` - Send chat messages
- `POST /api/ingest` - Ingest documents
- `POST /api/query` - Query documents
- `GET /api/agents` - Get list of agents

## Browser Compatibility

Works in all modern browsers (Chrome, Firefox, Safari, Edge).

