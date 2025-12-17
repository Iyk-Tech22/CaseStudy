from flask import Blueprint, request, jsonify, send_from_directory, current_app
from app import db, socketio
from app.models import SalesOrderHeader, SalesOrderDetail
from app.llm_service import GoogleLLMService
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import threading
import uuid
import traceback
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)
llmService = GoogleLLMService()
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}

def safe_socketio_emit(event, data, **kwargs):
    """Safely emit socketio events with error handling"""
    try:
        socketio.emit(event, data, **kwargs)
    except Exception as e:
        logger.warning(f"SocketIO emit failed for event '{event}': {str(e)}")

def allowedFile(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/api/health', methods=['GET'])
def healthCheck():
    return jsonify({"status": "healthy", "message": "API is running"})

@bp.route('/api/upload', methods=['POST'])
def uploadFile():
    """Handle file upload and start processing"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowedFile(file.filename):
        return jsonify({"error": "File type not allowed. Use PDF or image files."}), 400
    
    try:
        try:
            uploadFolder = current_app.config['UPLOAD_FOLDER']
        except RuntimeError:
            uploadFolder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
            os.makedirs(uploadFolder, exist_ok=True)
  
        filename = secure_filename(file.filename)
        fileExt = filename.rsplit('.', 1)[1].lower()
        uniqueFilename = f"{uuid.uuid4()}.{fileExt}"
        filePath = os.path.join(uploadFolder, uniqueFilename)
        file.save(filePath)
  
        jobId = str(uuid.uuid4())

        from flask import current_app as appInstance
        appObj = appInstance._get_current_object()

        socketio.start_background_task(
            processDocument,
            jobId, filePath, fileExt, uploadFolder, appObj
        )
        
        return jsonify({
            "jobId": jobId,
            "message": "File uploaded successfully. Processing started.",
            "filename": filename
        }), 200
        
    except Exception as e:
        errorTrace = traceback.format_exc()
        print(f"Upload error: {errorTrace}")
        return jsonify({
            "error": str(e),
            "traceback": errorTrace if current_app.debug else None
        }), 500

def processDocument(jobId, filePath, fileType, uploadFolder, appInstance=None):
    """Process document in background and emit web socket updates"""
    from app import db, socketio
    if appInstance is None:
        from app import createApp
        appInstance = createApp()
    
    try:
        with appInstance.app_context():
            try:
                safe_socketio_emit('processing_status', {
                    'jobId': jobId,
                    'status': 'processing',
                    'message': 'Extracting data from document...'
                })
                
                extractedData = llmService.extractInvoiceData(filePath, fileType)
                  
                # Check if extraction failed without usable data
                has_error = "error" in extractedData
                has_fallback = "fallback_data" in extractedData
                
                if has_error and not has_fallback:
                    safe_socketio_emit('processing_status', {
                        'jobId': jobId,
                        'status': 'error',
                        'message': extractedData.get('error', 'Unknown error occurred')
                    })
                    return
                
                # Use fallback only if API failed, otherwise use extracted data
                if has_error and has_fallback:
                    data = extractedData['fallback_data']
                else:
                    data = extractedData
                
                safe_socketio_emit('processing_status', {
                    'jobId': jobId,
                    'status': 'extracted',
                    'message': 'Data extracted successfully',
                    'data': data,
                })
                
                try:
                    orderDate = None
                    if data.get('order_date'):
                        try:
                            for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y'):
                                try:
                                    orderDate = datetime.strptime(data['order_date'], fmt).date()
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            orderDate = datetime.now().date()
                    else:
                        orderDate = datetime.now().date()
                    
                    order = SalesOrderHeader(
                        customerName=data.get('customer_name', ''),
                        customerEmail=data.get('customer_email', ''),
                        orderDate=orderDate,
                        invoiceNumber=data.get('invoice_number', ''),
                        totalAmount=data.get('total_amount', 0.0),
                        taxAmount=data.get('tax_amount', 0.0),
                        shippingAddress=data.get('shipping_address', ''),
                        billingAddress=data.get('billing_address', ''),
                        status='extracted',
                    )
                    
                    db.session.add(order)
                    db.session.flush()
                    
                    for detailData in data.get('order_details', []):
                        detail = SalesOrderDetail(
                            orderId=order.orderId,
                            productName=detailData['product_name'],
                            productCode=detailData.get('product_code', ''),
                            quantity=detailData['quantity'],
                            unitPrice=detailData['unit_price'],
                            lineTotal=detailData['line_total'],
                            description=detailData.get('description', '')
                        )
                        db.session.add(detail)
                    
                    db.session.commit()
                    
                    safe_socketio_emit('processing_status', {
                        'jobId': jobId,
                        'status': 'completed',
                        'message': 'Invoice saved to database',
                        'orderId': order.orderId,
                        'data': order.toDict(),
                    })
                    
                except Exception as e:
                    db.session.rollback()
                    errorTrace = traceback.format_exc()
                    print(f"Database error: {errorTrace}")
                    safe_socketio_emit('processing_status', {
                        'jobId': jobId,
                        'status': 'error',
                        'message': f'Database error: {str(e)}'
                    })
            
            except Exception as e:
                errorTrace = traceback.format_exc()
                print(f"Processing error: {errorTrace}")
                safe_socketio_emit('processing_status', {
                    'jobId': jobId,
                    'status': 'error',
                    'message': f'Processing error: {str(e)}'
                })
    except Exception as outer_error:
        # Catch any errors in app context setup
        errorTrace = traceback.format_exc()
        print(f"Outer error in processDocument: {errorTrace}")

@bp.route('/api/invoices', methods=['GET'])
def getInvoices():
    """Get all invoices with pagination"""
    page = request.args.get('page', 1, type=int)
    perPage = request.args.get('per_page', 10, type=int)
    
    invoices = SalesOrderHeader.query.order_by(SalesOrderHeader.createdAt.desc()).paginate(
        page=page, per_page=perPage, error_out=False
    )
    
    return jsonify({
        'invoices': [invoice.toDict() for invoice in invoices.items],
        'total': invoices.total,
        'page': page,
        'perPage': perPage,
        'pages': invoices.pages
    })

@bp.route('/api/invoices/<int:order_id>', methods=['GET'])
def getInvoice(order_id):
    """Get a specific invoice"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    return jsonify(order.toDict())

@bp.route('/api/invoices/<int:order_id>', methods=['PUT'])
def updateInvoice(order_id):
    """Update invoice header"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    data = request.json
    
    try:
        if 'customerName' in data:
            order.customerName = data['customerName']
        if 'customerEmail' in data:
            order.customerEmail = data['customerEmail']
        if 'orderDate' in data:
            try:
                order.orderDate = datetime.strptime(data['orderDate'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
        if 'invoiceNumber' in data:
            order.invoiceNumber = data['invoiceNumber']
        if 'totalAmount' in data:
            order.totalAmount = float(data['totalAmount'])
        if 'taxAmount' in data:
            order.taxAmount = float(data['taxAmount'])
        if 'shippingAddress' in data:
            order.shippingAddress = data['shippingAddress']
        if 'billingAddress' in data:
            order.billingAddress = data['billingAddress']
        if 'status' in data:
            order.status = data['status']
        
        order.updatedAt = datetime.utcnow()
        db.session.commit()
        
        safe_socketio_emit('invoice_updated', {
            'orderId': order_id,
            'data': order.toDict()
        }, skip_sid=None)
        
        return jsonify(order.toDict())
    except Exception as e:
        db.session.rollback()
        errorTrace = traceback.format_exc()
        print(f"Update error: {errorTrace}")
        return jsonify({"error": str(e)}), 400

@bp.route('/api/invoices/<int:order_id>', methods=['DELETE'])
def deleteInvoice(order_id):
    """Delete an invoice"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    
    try:
        db.session.delete(order)
        db.session.commit()
        
        safe_socketio_emit('invoice_deleted', {'orderId': order_id}, skip_sid=None)
        
        return jsonify({"message": "Invoice deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@bp.route('/api/invoices/<int:order_id>/details', methods=['GET'])
def getInvoiceDetails(order_id):
    """Get all details for an invoice"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    return jsonify([detail.toDict() for detail in order.orderDetails])

@bp.route('/api/invoices/<int:order_id>/details', methods=['PUT'])
def updateInvoiceDetails(order_id):
    """Update invoice details (replace all)"""
    order = SalesOrderHeader.query.get_or_404(order_id)
    data = request.json
    
    if not isinstance(data, list):
        return jsonify({"error": "Expected array of detail objects"}), 400
    
    try:
        SalesOrderDetail.query.filter_by(orderId=order_id).delete()
        
        totalAmount = 0.0
        for detailData in data:
            lineTotal = detailData.get('lineTotal', 
                float(detailData['quantity']) * float(detailData['unitPrice']))
            
            detail = SalesOrderDetail(
                orderId=order_id,
                productName=detailData['productName'],
                productCode=detailData.get('productCode', ''),
                quantity=float(detailData['quantity']),
                unitPrice=float(detailData['unitPrice']),
                lineTotal=float(lineTotal),
                description=detailData.get('description', '')
            )
            db.session.add(detail)
            totalAmount += float(lineTotal)
        
        order.totalAmount = totalAmount + float(order.taxAmount)
        order.updatedAt = datetime.utcnow()
        
        db.session.commit()
        
        safe_socketio_emit('invoice_updated', {
            'orderId': order_id,
            'data': order.toDict()
        }, skip_sid=None)
        
        return jsonify([detail.toDict() for detail in order.orderDetails])
    except Exception as e:
        db.session.rollback()
        errorTrace = traceback.format_exc()
        print(f"Update details error: {errorTrace}")
        return jsonify({"error": str(e)}), 400

@bp.route('/api/invoices/<int:order_id>/details/<int:detail_id>', methods=['DELETE'])
def deleteInvoiceDetail(order_id, detail_id):
    """Delete a specific detail"""
    detail = SalesOrderDetail.query.filter_by(detailId=detail_id, orderId=order_id).first_or_404()
    
    try:
        order = detail.order
        db.session.delete(detail)
        
        total = sum(d.lineTotal for d in order.orderDetails if d.detailId != detail_id)
        order.totalAmount = total + float(order.taxAmount)
        order.updatedAt = datetime.utcnow()
        
        db.session.commit()
        
        safe_socketio_emit('invoice_updated', {
            'orderId': order_id,
            'data': order.toDict()
        }, skip_sid=None)
        
        return jsonify({"message": "Detail deleted successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
