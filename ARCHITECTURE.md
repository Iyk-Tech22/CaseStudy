# Architecture & Implementation Guide

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Upload   │  │Dashboard │  │  Detail  │  │  Edit    │  │
│  │  Page    │  │  Page    │  │  Page    │  │  Forms   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │         │
│       └─────────────┴─────────────┴─────────────┘         │
│                    │                                        │
│         ┌──────────▼──────────┐                           │
│         │  Socket.io Client   │                           │
│         │  (WebSocket)        │                           │
│         └──────────┬──────────┘                           │
└────────────────────┼──────────────────────────────────────┘
                     │ HTTP REST API
                     │ WebSocket
┌────────────────────▼──────────────────────────────────────┐
│                    Flask Backend                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Routes  │  │  Models  │  │   LLM    │  │ SocketIO │  │
│  │  (API)   │  │  (ORM)   │  │ Service  │  │  Server  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │         │
│       └─────────────┴─────────────┴─────────────┘         │
│                    │                                        │
│         ┌──────────▼──────────┐                           │
│         │   SQLite Database   │                           │
│         └─────────────────────┘                           │
└────────────────────┬──────────────────────────────────────┘
                     │
         ┌───────────▼───────────┐
         │  Hugging Face API     │
         │  (LLM Inference)      │
         └───────────────────────┘
```

## Component Breakdown

### 1. Frontend (Next.js 14)

**Technology Stack:**
- **Next.js 14** with App Router for modern React development
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **Socket.io Client** for WebSocket communication
- **Axios** for HTTP requests

**Key Components:**

1. **Dashboard (`/`)**
   - Lists all extracted invoices
   - Search and filter functionality
   - Statistics overview
   - Navigation to upload and detail pages

2. **Upload Page (`/upload`)**
   - Drag-and-drop file upload
   - File validation (PDF, images)
   - Real-time processing status via WebSocket
   - Automatic redirect to invoice detail after extraction

3. **Invoice Detail Page (`/invoice/[id]`)**
   - View extracted invoice data
   - Edit mode for all fields
   - Add/remove order line items
   - Save and delete operations
   - Real-time updates via WebSocket

**State Management:**
- React hooks (`useState`, `useEffect`)
- WebSocket connection management
- Form state for editing

### 2. Backend (Flask)

**Technology Stack:**
- **Flask** - Python web framework
- **Flask-SocketIO** - WebSocket support
- **SQLAlchemy** - ORM for database operations
- **Flask-CORS** - Cross-origin resource sharing
- **PyPDF2** - PDF text extraction
- **Requests** - HTTP client for API calls

**Key Modules:**

1. **Routes (`routes.py`)**
   - RESTful API endpoints
   - File upload handling
   - Background processing threads
   - WebSocket event emission

2. **Models (`models.py`)**
   - `SalesOrderHeader` - Invoice header data
   - `SalesOrderDetail` - Line items
   - Relationships and serialization methods

3. **LLM Service (`llm_service.py`)**
   - Hugging Face API integration
   - Text extraction from PDFs
   - JSON parsing and validation
   - Fallback data generation

**Processing Flow:**
1. File uploaded → saved to `uploads/` directory
2. Background thread started for processing
3. Text extracted from PDF
4. LLM API called with structured prompt
5. Response parsed and validated
6. Data saved to database
7. WebSocket events emitted at each stage

### 3. Database (SQLite)

**Schema:**

**SalesOrderHeader:**
- `order_id` (PK, auto-increment)
- `customer_name`, `customer_email`
- `order_date`, `invoice_number`
- `total_amount`, `tax_amount`
- `shipping_address`, `billing_address`
- `status`, `created_at`, `updated_at`

**SalesOrderDetail:**
- `detail_id` (PK, auto-increment)
- `order_id` (FK → SalesOrderHeader)
- `product_name`, `product_code`
- `quantity`, `unit_price`, `line_total`
- `description`

**Relationships:**
- One-to-many: Header → Details
- Cascade delete: Deleting header deletes all details

### 4. LLM Integration (Hugging Face)

**Model Selection:**
- Primary: `mistralai/Mistral-7B-Instruct-v0.2`
- Fallbacks: `meta-llama/Llama-2-7b-chat-hf`, `google/flan-t5-large`

**Extraction Process:**
1. Extract text from PDF using PyPDF2
2. Construct structured prompt with JSON schema
3. Call Hugging Face Inference API
4. Parse JSON response
5. Validate and clean extracted data
6. Handle errors with fallback data

**Prompt Engineering:**
- Clear instructions for JSON extraction
- Example structure provided
- Temperature set low (0.1) for consistency
- Max tokens: 2000

## Real-Time Communication

### WebSocket Events

**Client → Server:**
- Connection establishment
- Automatic reconnection

**Server → Client:**
- `processing_status` - Processing updates
  - Status: `processing`, `extracted`, `completed`, `error`
  - Includes job_id, message, and data
- `invoice_updated` - Invoice modification notifications
- `invoice_deleted` - Deletion notifications

**Implementation:**
- Flask-SocketIO with threading mode
- Socket.io client with auto-reconnect
- Event-driven updates for seamless UX

## Data Flow

### Upload & Extraction Flow

```
User uploads file
    ↓
Frontend sends POST /api/upload
    ↓
Backend saves file, generates job_id
    ↓
Background thread starts processing
    ↓
WebSocket: "processing" status
    ↓
Extract text from PDF
    ↓
Call Hugging Face API
    ↓
WebSocket: "extracted" status with data
    ↓
Save to database
    ↓
WebSocket: "completed" status with order_id
    ↓
Frontend redirects to invoice detail page
```

### Edit Flow

```
User clicks Edit
    ↓
Form fields become editable
    ↓
User modifies data
    ↓
User clicks Save
    ↓
Frontend sends PUT requests
    ↓
Backend updates database
    ↓
WebSocket: "invoice_updated" event
    ↓
All connected clients receive update
```

## Error Handling

### LLM API Failures
- Multiple fallback models
- Retry logic with delays
- Fallback data generation
- User-friendly error messages

### Database Errors
- Transaction rollback on errors
- Validation before save
- Error messages via WebSocket

### File Upload Errors
- File type validation
- Size limits (16MB)
- Secure filename handling
- Error responses to client

## Security Considerations

1. **File Upload**
   - File type validation
   - Secure filename generation
   - Size limits
   - Path traversal prevention

2. **API Security**
   - CORS configuration
   - Input validation
   - SQL injection prevention (SQLAlchemy ORM)
   - Error message sanitization

3. **Environment Variables**
   - API tokens in `.env` (not committed)
   - Secret keys for sessions
   - Database URLs configurable

## Performance Optimizations

1. **Background Processing**
   - Non-blocking file processing
   - Thread-based execution
   - WebSocket for real-time updates

2. **Database**
   - Indexed primary keys
   - Efficient queries with ORM
   - Connection pooling ready

3. **Frontend**
   - Client-side routing
   - Optimistic UI updates
   - Efficient re-renders

## Scalability Strategies

### Current Implementation
- Single-threaded Flask server
- SQLite database
- Synchronous LLM API calls

### Production Scaling Options

1. **Backend Scaling**
   - Gunicorn with multiple workers
   - Celery for async task processing
   - Redis for caching and queues
   - Load balancer for multiple instances

2. **Database Scaling**
   - PostgreSQL for production
   - Read replicas for read-heavy workloads
   - Database connection pooling
   - Indexing strategy

3. **LLM Processing**
   - Queue system (RabbitMQ, AWS SQS)
   - Batch processing
   - Caching common extractions
   - Model selection based on document type

4. **Frontend Scaling**
   - CDN for static assets
   - Server-side rendering (SSR)
   - Code splitting
   - Image optimization

## Testing Strategy

### Manual Testing
- Upload different invoice formats
- Test edit functionality
- Verify WebSocket updates
- Test error scenarios

### Automated Testing (Future)
- Unit tests for LLM service
- API endpoint tests
- Frontend component tests
- Integration tests
- E2E tests with Playwright

## Deployment Considerations

### Development
- SQLite database
- Flask development server
- Next.js dev server
- Local file storage

### Production
- PostgreSQL database
- Gunicorn/Uvicorn WSGI server
- Next.js production build
- Cloud storage (S3, etc.)
- Environment variables
- HTTPS/SSL
- Monitoring and logging

## Future Enhancements

1. **Document Types**
   - Support for receipts, purchase orders
   - Document classification
   - Template matching

2. **AI Improvements**
   - Fine-tuned models
   - OCR for images
   - Multi-language support
   - Confidence scores

3. **Features**
   - User authentication
   - Batch upload
   - Export to Excel/CSV
   - Invoice templates
   - Email notifications

4. **Analytics**
   - Extraction accuracy metrics
   - Processing time tracking
   - User activity logs
   - Performance monitoring

