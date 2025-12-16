# Invoice Extraction Application

A full-stack document extraction application built with Next.js (frontend) and Flask (backend) that uses Hugging Face LLM API to extract structured data from invoice documents.

## Features

- 📄 **Document Upload**: Upload PDF or image files (PNG, JPG, JPEG, GIF)
- 🤖 **AI-Powered Extraction**: Uses Hugging Face LLM API to extract invoice data automatically
- 🔄 **Real-time Processing**: WebSocket-based real-time updates during document processing
- ✏️ **Edit & Manage**: View, edit, and save extracted invoice data
- 💾 **Database Storage**: SQLite database for persistent storage
- 📊 **Dashboard**: View all invoices with search and filtering capabilities
- 🎨 **Modern UI**: Clean, responsive interface built with Tailwind CSS

## Tech Stack

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **Socket.io Client** (for WebSocket communication)
- **Axios** (for API calls)

### Backend
- **Flask** (Python web framework)
- **Flask-SocketIO** (WebSocket support)
- **SQLAlchemy** (ORM)
- **SQLite** (Database)
- **Hugging Face API** (LLM for document extraction)
- **PyPDF2** (PDF text extraction)
- **Pillow** (Image processing)

## Project Structure

```
CaseStudy/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Flask app initialization
│   │   ├── models.py            # Database models
│   │   ├── routes.py            # API routes
│   │   └── llm_service.py       # Hugging Face LLM integration
│   ├── app.py                   # Application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── generate_sample_invoices.py  # Script to generate sample PDFs
│   └── uploads/                 # Uploaded files directory
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Dashboard
│   │   ├── upload/
│   │   │   └── page.tsx         # Upload page
│   │   └── invoice/
│   │       └── [id]/
│   │           └── page.tsx     # Invoice detail/edit page
│   ├── package.json
│   └── tsconfig.json
└── sample-invoices/             # Generated sample invoices
```

## Prerequisites

- **Python 3.8+**
- **Node.js 18+** and **npm** or **yarn**
- **Hugging Face API Token** (optional, but recommended for better performance)

## Setup Instructions

### 1. Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables (optional):
Create a `.env` file in the `backend` directory:
```
HUGGINGFACE_API_TOKEN=your_token_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///invoice_extraction.db
```

**Note**: The app will work without a Hugging Face API token, but you may experience rate limiting. Get your free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

5. Generate sample invoices (optional):
```bash
python generate_sample_invoices.py
```

This will create 5 sample PDF invoices in the `sample-invoices` directory.

6. Run the Flask server:
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

### 2. Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
Create a `.env.local` file in the `frontend` directory:
```
NEXT_PUBLIC_API_URL=http://localhost:5000
NEXT_PUBLIC_WS_URL=http://localhost:5000
```

4. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. **Upload an Invoice**:
   - Navigate to the Upload page
   - Drag and drop or select a PDF/image file
   - Click "Upload and Process"
   - Wait for AI extraction (real-time updates via WebSocket)

2. **View Invoices**:
   - Dashboard shows all extracted invoices
   - Search by customer name or invoice number
   - Click "View" to see details

3. **Edit Invoice**:
   - Open an invoice detail page
   - Click "Edit" button
   - Modify any fields
   - Add/remove order items
   - Click "Save" to update

4. **Delete Invoice**:
   - Open an invoice detail page
   - Click "Delete" button
   - Confirm deletion

## API Endpoints

### Backend API

- `GET /api/health` - Health check
- `POST /api/upload` - Upload a document file
- `GET /api/invoices` - Get all invoices (with pagination)
- `GET /api/invoices/<id>` - Get a specific invoice
- `PUT /api/invoices/<id>` - Update invoice header
- `DELETE /api/invoices/<id>` - Delete an invoice
- `GET /api/invoices/<id>/details` - Get invoice details
- `PUT /api/invoices/<id>/details` - Update invoice details

### WebSocket Events

- `processing_status` - Real-time processing updates
- `invoice_updated` - Invoice update notifications
- `invoice_deleted` - Invoice deletion notifications

## Database Schema

### SalesOrderHeader
- `order_id` (Primary Key)
- `customer_name`
- `customer_email`
- `order_date`
- `invoice_number`
- `total_amount`
- `tax_amount`
- `shipping_address`
- `billing_address`
- `status`
- `created_at`
- `updated_at`

### SalesOrderDetail
- `detail_id` (Primary Key)
- `order_id` (Foreign Key)
- `product_name`
- `product_code`
- `quantity`
- `unit_price`
- `line_total`
- `description`

## Scaling Strategies

### Performance Optimization
1. **Async Processing**: Implement Celery with Redis for background job processing
2. **Caching**: Use Redis for caching frequently accessed data
3. **CDN**: Serve static assets via CDN
4. **Database Indexing**: Add indexes on frequently queried fields
5. **Connection Pooling**: Use connection pooling for database connections

### Scalability
1. **Horizontal Scaling**: Deploy multiple backend instances behind a load balancer
2. **Queue System**: Use message queues (RabbitMQ, AWS SQS) for document processing
3. **Database Scaling**: 
   - Use PostgreSQL for production
   - Implement read replicas
   - Consider database sharding for very large datasets
4. **Microservices**: Split into separate services (upload, processing, storage)

### Additional Document Types
1. **Plugin System**: Create a plugin-based extraction system
2. **Document Classification**: Use ML to classify document types automatically
3. **Template Matching**: Store and match document templates
4. **Custom Prompts**: Maintain LLM prompts per document type

### Production Readiness
1. **Authentication**: Implement JWT or OAuth2
2. **Authorization**: Role-based access control (RBAC)
3. **Rate Limiting**: Prevent abuse with rate limiting
4. **Logging**: Structured logging (ELK stack, CloudWatch)
5. **Monitoring**: APM tools (New Relic, Datadog)
6. **Error Tracking**: Sentry for error tracking
7. **CI/CD**: Automated testing and deployment
8. **Containerization**: Docker and Kubernetes for deployment
9. **Security**: 
   - Input validation and sanitization
   - File type verification
   - SQL injection prevention (already handled by SQLAlchemy)
   - XSS protection

## Troubleshooting

### Backend Issues

1. **Port already in use**:
   - Change the port in `app.py`: `socketio.run(app, port=5001)`

2. **Database errors**:
   - Delete `instance/invoice_extraction.db` and restart the server
   - The database will be recreated automatically

3. **Hugging Face API errors**:
   - Check your API token in `.env`
   - Verify internet connection
   - The app will use fallback data if API fails

### Frontend Issues

1. **Connection refused**:
   - Ensure backend is running on port 5000
   - Check `NEXT_PUBLIC_API_URL` in `.env.local`

2. **WebSocket connection failed**:
   - Check `NEXT_PUBLIC_WS_URL` in `.env.local`
   - Ensure Flask-SocketIO is running

## Development

### Running Tests
```bash
# Backend tests (if implemented)
cd backend
pytest

# Frontend tests (if implemented)
cd frontend
npm test
```

### Building for Production

**Frontend**:
```bash
cd frontend
npm run build
npm start
```

**Backend**:
```bash
cd backend
# Use a production WSGI server like Gunicorn
gunicorn -k eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

## License

This project is created for assessment purposes.

## Author

Created as part of a technical assessment case study.

