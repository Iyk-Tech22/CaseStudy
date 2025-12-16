from app import db
from datetime import datetime

class SalesOrderHeader(db.Model):
    __tablename__ = 'sales_order_header'
    
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_name = db.Column(db.String(200), nullable=False)
    customer_email = db.Column(db.String(200))
    order_date = db.Column(db.Date, nullable=False)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0.00)
    shipping_address = db.Column(db.Text)
    billing_address = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    order_details = db.relationship('SalesOrderDetail', backref='order', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        return {
            'order_id': self.order_id,
            'customer_name': self.customer_name,
            'customer_email': self.customer_email,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'invoice_number': self.invoice_number,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0.0,
            'shipping_address': self.shipping_address,
            'billing_address': self.billing_address,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'order_details': [detail.to_dict() for detail in self.order_details]
        }

class SalesOrderDetail(db.Model):
    __tablename__ = 'sales_order_detail'
    
    detail_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('sales_order_header.order_id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    product_code = db.Column(db.String(100))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'detail_id': self.detail_id,
            'order_id': self.order_id,
            'product_name': self.product_name,
            'product_code': self.product_code,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price) if self.unit_price else 0.0,
            'line_total': float(self.line_total) if self.line_total else 0.0,
            'description': self.description
        }

