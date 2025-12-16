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

## Troubleshooting

### Backend Issues

**Port 5000 already in use:**
- Change the port in `backend/app.py`: `socketio.run(app, port=5001)`
- Update frontend `.env.local` accordingly

**Database errors:**
- Delete `backend/instance/invoice_extraction.db` and restart
- The database will be recreated automatically

**Hugging Face API errors:**
- Check your API token in `.env`
- Verify internet connection
- The app will use fallback data if API fails
- Some models may take time to load (503 error) - wait and retry

### Frontend Issues

**Connection refused:**
- Ensure backend is running on port 5000
- Check `NEXT_PUBLIC_API_URL` in `.env.local`

**WebSocket connection failed:**
- Check `NEXT_PUBLIC_WS_URL` in `.env.local`
- Ensure Flask-SocketIO is running
- Check browser console for errors

## Testing with Sample Invoices

After running `generate_sample_invoices.py`, you'll have 5 sample invoices:
1. `simple_invoice.pdf` - Basic single-item invoice
2. `detailed_invoice.pdf` - Multi-item invoice with various products
3. `international_invoice.pdf` - International format invoice
4. `service_invoice.pdf` - Time-based service invoice
5. `product_invoice.pdf` - Product-heavy invoice with many SKUs

Upload these to test different invoice formats and see how the AI extracts data from each.

