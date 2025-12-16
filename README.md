# Setup Guide

## Quick Start

### Prerequisites

- Python 3.8+ installed
- Node.js 18+ and npm installed
- (Optional) Hugging Face API token for better LLM performance

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

4. (Optional) Set up environment variables:
   Create a `.env` file in the `backend` directory:

```
HUGGINGFACE_API_TOKEN=your_token_here
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///invoice_extraction.db
```

**Note**: You can get a free Hugging Face API token at https://huggingface.co/settings/tokens. The app will work without it, but may have rate limits.

5. Generate sample invoices:

```bash
python generate_sample_invoices.py
```

This creates 5 sample PDF invoices in the `sample-invoices` directory.

6. Start the Flask server:

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
