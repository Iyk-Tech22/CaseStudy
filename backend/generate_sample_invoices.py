"""
Generate sample PDF invoices with different templates
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from datetime import datetime, timedelta
import os
import random

def create_sample_invoices():
    """Generate 5 sample invoices with different templates"""
    output_dir = 'sample-invoices'
    os.makedirs(output_dir, exist_ok=True)
    
    # Sample data for different invoice types
    invoices = [
        {
            'filename': 'simple_invoice.pdf',
            'title': 'SIMPLE INVOICE',
            'customer': 'John Smith',
            'email': 'john.smith@email.com',
            'invoice_num': 'INV-2024-001',
            'date': datetime.now() - timedelta(days=5),
            'items': [
                {'name': 'Web Development Service', 'code': 'WEB-001', 'qty': 1, 'price': 5000.00, 'desc': 'Website development and design'}
            ],
            'tax': 500.00,
            'address': '123 Main Street, New York, NY 10001'
        },
        {
            'filename': 'detailed_invoice.pdf',
            'title': 'DETAILED INVOICE',
            'customer': 'Tech Solutions Inc.',
            'email': 'billing@techsolutions.com',
            'invoice_num': 'INV-2024-002',
            'date': datetime.now() - timedelta(days=3),
            'items': [
                {'name': 'Laptop Computer', 'code': 'LAP-001', 'qty': 5, 'price': 1200.00, 'desc': 'Dell XPS 15 Laptop'},
                {'name': 'Wireless Mouse', 'code': 'MOU-001', 'qty': 10, 'price': 25.00, 'desc': 'Logitech MX Master 3'},
                {'name': 'USB-C Cable', 'code': 'CAB-001', 'qty': 20, 'price': 15.00, 'desc': 'USB-C to USB-C Cable 6ft'},
                {'name': 'Monitor Stand', 'code': 'MON-001', 'qty': 3, 'price': 150.00, 'desc': 'Ergonomic Monitor Stand'}
            ],
            'tax': 450.00,
            'address': '456 Business Park, San Francisco, CA 94102'
        },
        {
            'filename': 'international_invoice.pdf',
            'title': 'INTERNATIONAL INVOICE',
            'customer': 'Global Trading Ltd.',
            'email': 'orders@globaltrading.co.uk',
            'invoice_num': 'INV-2024-003',
            'date': datetime.now() - timedelta(days=2),
            'items': [
                {'name': 'Premium Software License', 'code': 'SW-LIC-001', 'qty': 50, 'price': 299.99, 'desc': 'Annual Enterprise License'},
                {'name': 'Support Package', 'code': 'SUP-001', 'qty': 50, 'price': 99.99, 'desc': '24/7 Technical Support'},
            ],
            'tax': 2000.00,
            'address': '789 Oxford Street, London, UK, W1D 2HX',
            'currency': 'GBP'
        },
        {
            'filename': 'service_invoice.pdf',
            'title': 'SERVICE INVOICE',
            'customer': 'Sarah Johnson',
            'email': 'sarah.j@consulting.com',
            'invoice_num': 'INV-2024-004',
            'date': datetime.now() - timedelta(days=1),
            'items': [
                {'name': 'Consulting Hours', 'code': 'CONS-001', 'qty': 40, 'price': 150.00, 'desc': 'Business Strategy Consulting'},
                {'name': 'Report Preparation', 'code': 'RPT-001', 'qty': 1, 'price': 2000.00, 'desc': 'Market Analysis Report'},
                {'name': 'Presentation Delivery', 'code': 'PRES-001', 'qty': 2, 'price': 500.00, 'desc': 'Client Presentation Sessions'}
            ],
            'tax': 300.00,
            'address': '321 Corporate Blvd, Chicago, IL 60601'
        },
        {
            'filename': 'product_invoice.pdf',
            'title': 'PRODUCT INVOICE',
            'customer': 'Retail Store Chain',
            'email': 'procurement@retailchain.com',
            'invoice_num': 'INV-2024-005',
            'date': datetime.now(),
            'items': [
                {'name': 'Product A', 'code': 'PROD-A-001', 'qty': 100, 'price': 29.99, 'desc': 'Standard Product A'},
                {'name': 'Product B', 'code': 'PROD-B-002', 'qty': 75, 'price': 39.99, 'desc': 'Premium Product B'},
                {'name': 'Product C', 'code': 'PROD-C-003', 'qty': 50, 'price': 49.99, 'desc': 'Deluxe Product C'},
                {'name': 'Product D', 'code': 'PROD-D-004', 'qty': 25, 'price': 59.99, 'desc': 'Ultimate Product D'},
                {'name': 'Product E', 'code': 'PROD-E-005', 'qty': 200, 'price': 19.99, 'desc': 'Basic Product E'},
            ],
            'tax': 1124.75,
            'address': '555 Commerce Drive, Dallas, TX 75201'
        }
    ]
    
    for invoice_data in invoices:
        create_invoice_pdf(invoice_data, output_dir)
        print(f"Generated: {invoice_data['filename']}")
    
    print(f"\nAll sample invoices generated in '{output_dir}' directory")

def create_invoice_pdf(invoice_data, output_dir):
    """Create a PDF invoice with the given data"""
    filename = os.path.join(output_dir, invoice_data['filename'])
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12
    )
    
    # Title
    story.append(Paragraph(invoice_data['title'], title_style))
    story.append(Spacer(1, 0.3*inch))
    
    # Company info and invoice details side by side
    company_info = [
        ['<b>From:</b>', ''],
        ['ABC Company Inc.', ''],
        ['123 Business Street', ''],
        ['New York, NY 10001', ''],
        ['Phone: (555) 123-4567', ''],
        ['Email: billing@abccompany.com', '']
    ]
    
    invoice_info = [
        ['<b>Invoice Number:</b>', invoice_data['invoice_num']],
        ['<b>Date:</b>', invoice_data['date'].strftime('%B %d, %Y')],
        ['<b>Customer:</b>', invoice_data['customer']],
        ['<b>Email:</b>', invoice_data['email']],
        ['<b>Address:</b>', invoice_data['address']]
    ]
    
    # Create tables for layout
    info_table = Table([
        [Paragraph(row[0], header_style) if i < len(company_info) else '', 
         Paragraph(row[1], header_style) if i < len(invoice_info) else '']
        for i, row in enumerate(zip(company_info, invoice_info))
    ], colWidths=[3*inch, 3*inch])
    
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.5*inch))
    
    # Items table
    items_data = [['Product Code', 'Product Name', 'Quantity', 'Unit Price', 'Total']]
    
    subtotal = 0
    for item in invoice_data['items']:
        line_total = item['qty'] * item['price']
        subtotal += line_total
        items_data.append([
            item['code'],
            f"{item['name']}<br/><i>{item['desc']}</i>",
            str(item['qty']),
            f"${item['price']:.2f}",
            f"${line_total:.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(items_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Totals
    tax = invoice_data['tax']
    total = subtotal + tax
    
    totals_data = [
        ['Subtotal:', f"${subtotal:.2f}"],
        ['Tax:', f"${tax:.2f}"],
        ['<b>Total:</b>', f"<b>${total:.2f}</b>"]
    ]
    
    totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (1, -1), 14),
        ('TOPPADDING', (0, -1), (1, -1), 12),
        ('BOTTOMPADDING', (0, -1), (1, -1), 12),
    ]))
    
    story.append(Paragraph('<br/>', styles['Normal']))
    story.append(totals_table)
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph('Thank you for your business!', footer_style))
    story.append(Paragraph('Payment terms: Net 30 days', footer_style))
    
    doc.build(story)

if __name__ == '__main__':
    create_sample_invoices()

