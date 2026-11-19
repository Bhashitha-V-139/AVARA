# AVARA – Deployment Guide

## 1. Prerequisites

- Python 3.11+
- Node.js and npm
- Gemini API key

## 2. Environment Setup

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Never commit `.env` or expose API keys in the frontend.

## 3. Run the Backend

From the project root:

```powershell
cd backend
uvicorn app.main:app --reload
```

- Backend: `http://127.0.0.1:8000`
- API documentation: `http://127.0.0.1:8000/docs`

## 4. Run the Frontend

Open a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open: `http://localhost:5173`

## 5. Configuration for Deployment

### Backend API URL

The frontend API base URL is configured in:

`frontend/src/api.js`

Update the default local backend URL to the deployed backend URL when hosting the application.

### CORS

CORS configuration is located in:

`backend/app/main.py`

Update the allowed origins to include the deployed frontend URL.

## 6. Persistent Storage

AVARA stores uploaded documents, ChromaDB data, and SQLite data in the `data/` directory.

For cloud deployment, configure persistent storage to prevent uploaded documents, vector indexes, and application data from being lost when the server restarts or redeploys.
