# DocuScout Frontend (Next.js)

## Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Create `.env.local` file (optional):
```env
NEXT_PUBLIC_API_URL=http://localhost:8001/api
```

3. Run development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Main page (upload/post-ingestion)
│   └── globals.css         # Global styles
├── components/
│   ├── UploadModal.tsx     # File upload modal with drag & drop
│   ├── PostIngestionPage.tsx  # Post-ingestion page (Q&A + Predict Warnings)
│   ├── LoadingOverlay.tsx  # Loading overlay component
│   └── Notification.tsx    # Notification component
└── lib/
    └── api.ts              # API client for backend communication
```

## Features

- **Upload Page**: Initial page with "Upload PDFs" button
- **Upload Modal**: Drag & drop file upload with file selection
- **Post-Ingestion Page**: 
  - Left: "Predict Warnings in Clauses in Files" button
  - Right: Q&A Assistant for document queries

## Development

- Uses Next.js 14 with App Router
- TypeScript for type safety
- Client-side components for interactivity

