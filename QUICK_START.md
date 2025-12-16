# Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Backend Setup (Terminal 1)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate

pip install -r requirements.txt
python generate_sample_invoices.py
python app.py
```

Backend will start on `http://localhost:5000`

### Step 2: Frontend Setup (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on `http://localhost:3000`

### Step 3: Test the Application

1. Open `http://localhost:3000` in your browser
2. Click "Upload New Invoice"
3. Upload one of the sample PDFs from `sample-invoices/` folder
4. Watch real-time extraction via WebSocket
5. Review and edit the extracted data

## 📋 What's Included

✅ **Backend (Flask)**
- RESTful API endpoints
- WebSocket support (Flask-SocketIO)
- SQLite database with SQLAlchemy ORM
- Hugging Face LLM integration
- File upload handling

✅ **Frontend (Next.js)**
- Modern React UI with TypeScript
- Real-time WebSocket updates
- Invoice dashboard with search
- Edit and manage invoices
- Responsive design

✅ **Sample Data**
- 5 different invoice templates
- Generated PDFs ready to test

## 🔧 Configuration (Optional)

### Backend `.env` file:
```
HUGGINGFACE_API_TOKEN=your_token_here
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///invoice_extraction.db
```

### Frontend `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_WS_URL=http://localhost:5000
```

## 📝 API Endpoints

- `GET /api/health` - Health check
- `POST /api/upload` - Upload document
- `GET /api/invoices` - List all invoices
- `GET /api/invoices/<id>` - Get invoice details
- `PUT /api/invoices/<id>` - Update invoice
- `DELETE /api/invoices/<id>` - Delete invoice
- `PUT /api/invoices/<id>/details` - Update order items

## 🎯 Features Demonstrated

1. **Document Upload** - Drag & drop or file picker
2. **AI Extraction** - Hugging Face LLM extracts structured data
3. **Real-time Updates** - WebSocket shows processing status
4. **Data Management** - View, edit, delete invoices
5. **Database Storage** - SQLite persistence
6. **Modern UI** - Clean, responsive interface

## 🐛 Troubleshooting

**Backend won't start:**
- Check Python version (3.8+)
- Ensure all dependencies installed
- Check if port 5000 is available

**Frontend won't connect:**
- Ensure backend is running
- Check `.env.local` URLs
- Check browser console for errors

**LLM extraction fails:**
- Check internet connection
- Verify Hugging Face token (optional)
- App will use fallback data if API fails

## 📚 Next Steps

1. Upload sample invoices to test different formats
2. Edit extracted data to see real-time updates
3. Explore the codebase to understand the architecture
4. Review README.md for detailed documentation

