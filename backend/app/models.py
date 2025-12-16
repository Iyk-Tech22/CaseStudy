from app import db
from datetime import datetime

class SalesOrderHeader(db.Model):
    __tablename__ = 'sales_order_header'
    orderId = db.Column(db.Integer, primary_key=True, autoincrement=True, name='order_id')
    customerName = db.Column(db.String(200), nullable=False, name='customer_name')
    customerEmail = db.Column(db.String(200), name='customer_email')
    orderDate = db.Column(db.Date, nullable=False, name='order_date')
    invoiceNumber = db.Column(db.String(100), unique=True, nullable=False, name='invoice_number')
    totalAmount = db.Column(db.Numeric(10, 2), nullable=False, name='total_amount')
    taxAmount = db.Column(db.Numeric(10, 2), default=0.00, name='tax_amount')
    shippingAddress = db.Column(db.Text, name='shipping_address')
    billingAddress = db.Column(db.Text, name='billing_address')
    status = db.Column(db.String(50), default='pending')
    createdAt = db.Column(db.DateTime, default=datetime.utcnow, name='created_at')
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, name='updated_at')
    orderDetails = db.relationship('SalesOrderDetail', backref='order', cascade='all, delete-orphan', lazy=True)
    
    def toDict(self):
        return {
            'orderId': self.orderId,
            'customerName': self.customerName,
            'customerEmail': self.customerEmail,
            'orderDate': self.orderDate.isoformat() if self.orderDate else None,
            'invoiceNumber': self.invoiceNumber,
            'totalAmount': float(self.totalAmount) if self.totalAmount else 0.0,
            'taxAmount': float(self.taxAmount) if self.taxAmount else 0.0,
            'shippingAddress': self.shippingAddress,
            'billingAddress': self.billingAddress,
            'status': self.status,
            'createdAt': self.createdAt.isoformat() if self.createdAt else None,
            'updatedAt': self.updatedAt.isoformat() if self.updatedAt else None,
            'orderDetails': [detail.toDict() for detail in self.orderDetails]
        }

class SalesOrderDetail(db.Model):
    __tablename__ = 'sales_order_detail'
    detailId = db.Column(db.Integer, primary_key=True, autoincrement=True, name='detail_id')
    orderId = db.Column(db.Integer, db.ForeignKey('sales_order_header.order_id'), nullable=False, name='order_id')
    productName = db.Column(db.String(200), nullable=False, name='product_name')
    productCode = db.Column(db.String(100), name='product_code')
    quantity = db.Column(db.Integer, nullable=False)
    unitPrice = db.Column(db.Numeric(10, 2), nullable=False, name='unit_price')
    lineTotal = db.Column(db.Numeric(10, 2), nullable=False, name='line_total')
    description = db.Column(db.Text)
    
    def toDict(self):
        return {
            'detailId': self.detailId,
            'orderId': self.orderId,
            'productName': self.productName,
            'productCode': self.productCode,
            'quantity': self.quantity,
            'unitPrice': float(self.unitPrice) if self.unitPrice else 0.0,
            'lineTotal': float(self.lineTotal) if self.lineTotal else 0.0,
            'description': self.description
        }
