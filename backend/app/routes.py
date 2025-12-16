from flask import Blueprint, request, jsonify, send_from_directory, current_app
from app import db, socketio
from app.models import SalesOrderHeader, SalesOrderDetail
from app.llm_service import HuggingFaceLLMService
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import threading
import uuid

bp = Blueprint('api', __name__)
llm_service = HuggingFaceLLMService()

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "API is running"})

@bp.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use PDF or image files."}), 400
    
    try:
        # Get upload folder from current app context
        # Use current_app which is available in request context
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
        except RuntimeError:
            # Fallback: use direct path if context issue
            upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
        
        # Save file
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Start processing in background thread with app context
        # Pass the app instance to ensure context is available
        from flask import current_app as app_instance
        app_obj = app_instance._get_current_object()
        socketio.start_background_task(
            process_document,
            job_id, file_path, file_ext, upload_folder, app_obj
        )
        
        return jsonify({
            "job_id": job_id,
            "message": "File uploaded successfully. Processing started.",
            "filename": filename
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Upload error: {error_trace}")  # Log full traceback for debugging
        return jsonify({
            "error": str(e),
            "traceback": error_trace if current_app.debug else None
        }), 500

def process_document(job_id, file_path, file_type, upload_folder, app_instance=None):
    """Process document in background and emit WebSocket updates"""
    # Import here to avoid circular imports
    from app import db, socketio
    
    # Ensure we have app context for database operations
    if app_instance is None:
        from app import create_app
        app_instance = create_app()
    
    # Use app context for all operations
    with app_instance.app_context():
        try:
            # Emit processing started
            socketio.emit('processing_status', {
                'job_id': job_id,
                'status': 'processing',
                'message': 'Extracting data from document...'
            })
            
            # Extract data using LLM
            extracted_data = llm_service.extract_invoice_data(file_path, file_type)
            
            if "error" in extracted_data and "fallback_data" not in extracted_data:
                socketio.emit('processing_status', {
                    'job_id': job_id,
                    'status': 'error',
                    'message': extracted_data.get('error', 'Unknown error occurred')
                })
                return
            
            # Use fallback data if main extraction failed
            using_fallback = "fallback_data" in extracted_data
            data = extracted_data.get('fallback_data', extracted_data) if using_fallback else extracted_data
            
            # Emit extraction complete
            message = 'Data extracted successfully (using fallback data - LLM API not available)' if using_fallback else 'Data extracted successfully'
            socketio.emit('processing_status', {
                'job_id': job_id,
                'status': 'extracted',
                'message': message,
                'data': data,
                'using_fallback': using_fallback
            })
            
            # Save to database
            try:
                # Create order header
                order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date() if data.get('order_date') else datetime.now().date()
                
                order = SalesOrderHeader(
                    customer_name=data['customer_name'],
                    customer_email=data.get('customer_email', ''),
                    order_date=order_date,
                    invoice_number=data['invoice_number'],
                    total_amount=data['total_amount'],
                    tax_amount=data.get('tax_amount', 0.0),
                    shipping_address=data.get('shipping_address', ''),
                    billing_address=data.get('billing_address', ''),
                    status='extracted'
                )
                
                db.session.add(order)
                db.session.flush()  # Get the order_id
                
                # Create order details
                for detail_data in data.get('order_details', []):
                    detail = SalesOrderDetail(
                        order_id=order.order_id,
                        product_name=detail_data['product_name'],
                        product_code=detail_data.get('product_code', ''),
                        quantity=detail_data['quantity'],
                        unit_price=detail_data['unit_price'],
                        line_total=detail_data['line_total'],
                        description=detail_data.get('description', '')
                    )
                    db.session.add(detail)
                
                db.session.commit()
                
                # Emit completion with saved data
                socketio.emit('processing_status', {
                    'job_id': job_id,
                    'status': 'completed',
                    'message': 'Invoice saved to database',
                    'order_id': order.order_id,
                    'data': order.to_dict()
                })
                
            except Exception as e:
                db.session.rollback()
                socketio.emit('processing_status', {
                    'job_id': job_id,
                    'status': 'error',
                    'message': f'Database error: {str(e)}'
                })
            
            # Clean up uploaded file (optional)
            # os.remove(file_path)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            socketio.emit('processing_status', {
                'job_id': job_id,
                'status': 'error',
                'message': f'Processing error: {str(e)}'
            })

@bp.route('/api/invoices', methods=['GET'])
def get_invoices():
    """Get all invoices with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    invoices = SalesOrderHeader.query.order_by(SalesOrderHeader.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'invoices': [invoice.to_dict() for invoice in invoices.items],
        'total': invoices.total,
        'page': page,
        'per_page': per_page,
        'pages': invoices.pages
    })

@bp.route('/api/invoices/<int:order_id>', methods=['GET'])
def get_invoice(order_id):
    """Get a specific invoice"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    return jsonify(order.to_dict())

@bp.route('/api/invoices/<int:order_id>', methods=['PUT'])
def update_invoice(order_id):
    """Update invoice header"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    data = request.json
    
    try:
        if 'customer_name' in data:
            order.customer_name = data['customer_name']
        if 'customer_email' in data:
            order.customer_email = data['customer_email']
        if 'order_date' in data:
            order.order_date = datetime.strptime(data['order_date'], '%Y-%m-%d').date()
        if 'invoice_number' in data:
            order.invoice_number = data['invoice_number']
        if 'total_amount' in data:
            order.total_amount = data['total_amount']
        if 'tax_amount' in data:
            order.tax_amount = data['tax_amount']
        if 'shipping_address' in data:
            order.shipping_address = data['shipping_address']
        if 'billing_address' in data:
            order.billing_address = data['billing_address']
        if 'status' in data:
            order.status = data['status']
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Emit update via WebSocket
        socketio.emit('invoice_updated', {
            'order_id': order_id,
            'data': order.to_dict()
        })
        
        return jsonify(order.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@bp.route('/api/invoices/<int:order_id>', methods=['DELETE'])
def delete_invoice(order_id):
    """Delete an invoice"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    
    try:
        db.session.delete(order)
        db.session.commit()
        
        # Emit deletion via WebSocket
        socketio.emit('invoice_deleted', {'order_id': order_id})
        
        return jsonify({"message": "Invoice deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@bp.route('/api/invoices/<int:order_id>/details', methods=['GET'])
def get_invoice_details(order_id):
    """Get all details for an invoice"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    return jsonify([detail.to_dict() for detail in order.order_details])

@bp.route('/api/invoices/<int:order_id>/details', methods=['PUT'])
def update_invoice_details(order_id):
    """Update invoice details (replace all)"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    data = request.json
    
    if not isinstance(data, list):
        return jsonify({"error": "Expected array of detail objects"}), 400
    
    try:
        # Delete existing details
        SalesOrderDetail.query.filter_by(order_id=order_id).delete()
        
        # Add new details
        total_amount = 0.0
        for detail_data in data:
            detail = SalesOrderDetail(
                order_id=order_id,
                product_name=detail_data['product_name'],
                product_code=detail_data.get('product_code', ''),
                quantity=detail_data['quantity'],
                unit_price=detail_data['unit_price'],
                line_total=detail_data.get('line_total', detail_data['quantity'] * detail_data['unit_price']),
                description=detail_data.get('description', '')
            )
            db.session.add(detail)
            total_amount += float(detail.line_total)
        
        # Update order total
        order.total_amount = total_amount + float(order.tax_amount)
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Emit update via WebSocket
        socketio.emit('invoice_updated', {
            'order_id': order_id,
            'data': order.to_dict()
        })
        
        return jsonify([detail.to_dict() for detail in order.order_details])
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@bp.route('/api/invoices/<int:order_id>/details/<int:detail_id>', methods=['DELETE'])
def delete_invoice_detail(order_id, detail_id):
    """Delete a specific detail"""
    detail = SalesOrderDetail.query.filter_by(detail_id=detail_id, order_id=order_id).first_or_404()
    
    try:
        order = detail.order
        db.session.delete(detail)
        
        # Recalculate total
        total = sum(d.line_total for d in order.order_details if d.detail_id != detail_id)
        order.total_amount = total + float(order.tax_amount)
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        socketio.emit('invoice_updated', {
            'order_id': order_id,
            'data': order.to_dict()
        })
        
        return jsonify({"message": "Detail deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

