# Setup Guide

## Quick Start

### Prerequisites

- Python 3.8+ installed
- Node.js 18+ and npm installed
- Google AI API token for better LLM performance

### Backend Setup

1. Navigate to backend directory:

```bash
cd backend
```

2. Create and activate virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Set up environment variables:
   Create a `.env` file in the `backend` directory:

```
GOOGLE_API_KEY=your_token_here
DATABASE_URL=sqlite:///invoice_extraction.db
```

1. Start the Flask server:

```bash
python app.py
```

The backend will run on `http://localhost:5000`

### Frontend Setup

1. Navigate to frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. (Optional) Set up environment variables:
   Create a `.env.local` file in the `frontend` directory:

```
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_WS_URL=http://localhost:5000
```

4. Start the development server:

```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Open your browser and go to `http://localhost:3000`
2. Click "Upload New Invoice" or navigate to `/upload`
3. Upload a PDF invoice (or use one of the sample invoices)
4. Wait for AI extraction (you'll see real-time updates via WebSocket)
5. Review and edit the extracted data
6. Save to database
