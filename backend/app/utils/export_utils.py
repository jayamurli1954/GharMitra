"""
Export Utilities for Excel and PDF Generation
Provides functions to export reports to Excel and PDF formats
"""
from io import BytesIO
from datetime import datetime
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


from decimal import Decimal

def create_maintenance_bill_pdf(
    bill_data: Dict[str, Any],
    society_info: Dict[str, Any]
) -> BytesIO:
    """
    Create a professional maintenance bill PDF
    
    Args:
        bill_data: Bill information (flat, amount, breakdown, etc.)
        society_info: Society information (name, address, logo_url)
        
    Returns:
        BytesIO: PDF file in memory
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    # Watermark for draft bills
    is_draft = not bill_data.get('is_posted', True) # Default to True (posted) if not provided
    
    def on_page(canvas, doc):
        if is_draft:
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 100)
            canvas.setFillGray(0.5, 0.2) # Gray color with 20% alpha
            canvas.translate(A4[0]/2, A4[1]/2)
            canvas.rotate(45)
            canvas.drawCentredString(0, 0, "DRAFT")
            canvas.restoreState()

    # Styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.grey,
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1f4788'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Helper to format amounts safely
    def format_val(val):
        if val is None: return "0.00"
        try:
            return f"{float(val):.2f}"
        except (ValueError, TypeError):
            return str(val)

    # Build content
    content = []
    
    # Society Header
    content.append(Paragraph(society_info.get('name', 'Housing Society'), title_style))
    if society_info.get('address'):
        content.append(Paragraph(society_info['address'], subtitle_style))
    content.append(Spacer(1, 0.2 * inch))
    
    # Bill Title
    try:
        month_name = datetime.strptime(f"{bill_data.get('year')}-{bill_data.get('month'):02d}-01", "%Y-%m-%d").strftime("%B %Y")
    except:
        month_name = f"Month: {bill_data.get('month')} Year: {bill_data.get('year')}"
    
    bill_title = f"<b>MAINTENANCE BILL</b><br/>{month_name}"
    content.append(Paragraph(bill_title, heading_style))
    content.append(Spacer(1, 0.15 * inch))
    
    # Bill Information
    bill_info_data = [
        ['Bill Number:', bill_data.get('bill_number', 'N/A')],
        ['Flat Number:', bill_data.get('flat_number', 'N/A')],
        ['Member Name:', bill_data.get('member_name', 'N/A')],
        ['Generated Date:', datetime.fromisoformat(bill_data.get('created_at', datetime.now().isoformat())).strftime('%d %b %Y')],
        ['Status:', 'DRAFT' if is_draft else bill_data.get('status', 'Unpaid').upper()],
    ]
    
    bill_info_table = Table(bill_info_data, colWidths=[2*inch, 3.5*inch])
    bill_info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#444444')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.grey),
    ]))
    content.append(bill_info_table)
    content.append(Spacer(1, 0.25 * inch))
    
    # Breakdown Heading
    content.append(Paragraph('Bill Breakdown', heading_style))
    
    # Breakdown table
    breakdown = bill_data.get('breakdown', {})
    breakdown_data = [['Description', 'Amount (₹)']]
    
    # Fixed expenses
    if 'fixed_expenses' in breakdown and breakdown['fixed_expenses']:
        fixed_list = breakdown.get('fixed_expenses_list', [])
        if fixed_list:
            for expense in fixed_list:
                breakdown_data.append([
                    f"  • {expense.get('name', 'Fixed Expense')}",
                    format_val(expense.get('amount'))
                ])
        else:
            breakdown_data.append(['Fixed Expenses', format_val(breakdown['fixed_expenses'])])
    
    # Water charges
    if 'water_charges' in breakdown and breakdown['water_charges']:
        water_exp = breakdown.get('water_expenses', {})
        if water_exp and 'flat_occupants' in water_exp:
            breakdown_data.append([
                f"Water Charges ({water_exp.get('flat_occupants', 0)} occupants × ₹{format_val(water_exp.get('per_person_charge', 0))})",
                format_val(breakdown['water_charges'])
            ])
        else:
            breakdown_data.append(['Water Charges', format_val(breakdown['water_charges'])])
    
    # Sinking fund
    if 'sinking_fund' in breakdown and breakdown['sinking_fund']:
        breakdown_data.append(['Sinking Fund', format_val(breakdown['sinking_fund'])])
    
    # Sqft calculation (for sqft-based billing)
    if 'sqft_calculation' in breakdown and breakdown['sqft_calculation']:
        # If it's a string like "1000 sq ft x ₹2 = ₹2000", just add it
        breakdown_data.append(['Square Feet Calculation', str(breakdown['sqft_calculation'])])
    
    # Total amount row
    breakdown_data.append(['', ''])  # Spacer
    breakdown_data.append(['TOTAL AMOUNT', format_val(bill_data.get('amount', 0))])
    
    breakdown_table = Table(breakdown_data, colWidths=[4*inch, 1.5*inch])
    breakdown_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold', 11),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        
        # Data rows
        ('FONT', (0, 1), (-1, -3), 'Helvetica', 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Gridlines
        ('GRID', (0, 0), (-1, -3), 0.5, colors.grey),
        ('LINEABOVE', (0, -1), (-1, -1), 1.5, colors.HexColor('#1f4788')),
        
        # Total row (bold and highlighted)
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1f4788')),
        
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    content.append(breakdown_table)
    content.append(Spacer(1, 0.3 * inch))
    
    # Payment status
    if not is_draft and bill_data.get('status') == 'paid' and bill_data.get('paid_at'):
        try:
            paid_date = datetime.fromisoformat(bill_data['paid_at']).strftime('%d %b %Y')
        except:
            paid_date = str(bill_data['paid_at'])
        payment_method = bill_data.get('payment_method', 'Not specified')
        payment_info = f"<b>Payment Status:</b> PAID on {paid_date}<br/><b>Payment Method:</b> {payment_method}"
        payment_style = ParagraphStyle(
            'PaymentInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#28a745'),
            spaceAfter=12,
            leftIndent=10
        )
        content.append(Paragraph(payment_info, payment_style))
    elif not is_draft:
        # Payment instructions for unpaid bills
        payment_instructions = """
        <b>Payment Instructions:</b><br/>
        Please make the payment by bank transfer or cash to the society office.<br/>
        For bank transfer, use the society's registered bank account.<br/>
        Keep the receipt for your records.
        """
        payment_style = ParagraphStyle(
            'PaymentInstructions',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=12,
            leftIndent=10
        )
        content.append(Paragraph(payment_instructions, payment_style))
    else:
        # Draft message
        draft_msg = "<b>This is a DRAFT bill.</b><br/>Please wait for final posting before making payment."
        draft_style = ParagraphStyle(
            'DraftInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.red,
            spaceAfter=12,
            leftIndent=10
        )
        content.append(Paragraph(draft_msg, draft_style))
    
    content.append(Spacer(1, 0.3 * inch))
    
    # Footer
    footer_text = f"""
    <i>This is a computer-generated bill. Generated on {datetime.now().strftime('%d %b %Y at %I:%M %p')}</i><br/>
    <i>For any queries, please contact the society office.</i>
    """
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    content.append(Paragraph(footer_text, footer_style))
    
    # Build PDF
    doc.build(content, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer


class ExcelExporter:
    """Excel export functionality using openpyxl"""
    
    @staticmethod
    def create_general_ledger_excel(
        report_data: Dict[str, Any],
        society_info: Dict[str, Any]
    ) -> BytesIO:
        """
        Create Excel file for General Ledger Report
        
        Args:
            report_data: Report data dictionary
            society_info: Society information (name, address, logo_url)
            
        Returns:
            BytesIO: Excel file in memory
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "General Ledger"
        
        # Styles
        header_font = Font(name='Arial', size=14, bold=True)
        title_font = Font(name='Arial', size=12, bold=True)
        subheader_font = Font(name='Arial', size=10, bold=True)
        normal_font = Font(name='Arial', size=10)
        
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Header
        row = 1
        ws.merge_cells(f'A{row}:F{row}')
        cell = ws[f'A{row}']
        cell.value = society_info.get('name', 'Society Name')
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        
        row += 1
        ws.merge_cells(f'A{row}:F{row}')
        cell = ws[f'A{row}']
        cell.value = "GENERAL LEDGER REPORT"
        cell.font = title_font
        cell.alignment = Alignment(horizontal='center')
        
        row += 1
        ws.merge_cells(f'A{row}:F{row}')
        cell = ws[f'A{row}']
        period = f"Period: {report_data.get('from_date', '')} to {report_data.get('to_date', '')}"
        cell.value = period
        cell.font = normal_font
        cell.alignment = Alignment(horizontal='center')
        
        row += 2
        
        # Column headers
        headers = ['Account', 'Date', 'Description', 'Debit', 'Credit', 'Balance']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col_num)
            cell.value = header
            cell.font = Font(name='Arial', size=10, bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = border
        
        row += 1
        
        # Data
        ledger_data = report_data.get('ledger', {})
        
        for account_code, account_info in ledger_data.items():
            # Account header
            ws.merge_cells(f'A{row}:F{row}')
            cell = ws[f'A{row}']
            cell.value = f"{account_code} - {account_info.get('account_name', '')}"
            cell.font = subheader_font
            cell.fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
            cell.border = border
            row += 1
            
            # Opening balance
            cell = ws.cell(row=row, column=1)
            cell.value = "Opening Balance"
            cell.font = normal_font
            cell.border = border
            
            opening_balance = account_info.get('opening_balance', 0)
            cell = ws.cell(row=row, column=6)
            cell.value = opening_balance
            cell.number_format = '#,##0.00'
            cell.font = normal_font
            cell.border = border
            row += 1
            
            # Transactions
            for txn in account_info.get('transactions', []):
                cell = ws.cell(row=row, column=2)
                cell.value = txn.get('date', '')
                cell.font = normal_font
                cell.border = border
                
                cell = ws.cell(row=row, column=3)
                cell.value = txn.get('description', '')
                cell.font = normal_font
                cell.border = border
                
                cell = ws.cell(row=row, column=4)
                cell.value = txn.get('debit', 0)
                cell.number_format = '#,##0.00'
                cell.font = normal_font
                cell.border = border
                
                cell = ws.cell(row=row, column=5)
                cell.value = txn.get('credit', 0)
                cell.number_format = '#,##0.00'
                cell.font = normal_font
                cell.border = border
                
                cell = ws.cell(row=row, column=6)
                cell.value = txn.get('balance', 0)
                cell.number_format = '#,##0.00'
                cell.font = normal_font
                cell.border = border
                
                row += 1
            
            # Totals
            cell = ws.cell(row=row, column=1)
            cell.value = "TOTAL"
            cell.font = subheader_font
            cell.fill = total_fill
            cell.border = border
            
            cell = ws.cell(row=row, column=4)
            cell.value = account_info.get('total_debit', 0)
            cell.number_format = '#,##0.00'
            cell.font = subheader_font
            cell.fill = total_fill
            cell.border = border
            
            cell = ws.cell(row=row, column=5)
            cell.value = account_info.get('total_credit', 0)
            cell.number_format = '#,##0.00'
            cell.font = subheader_font
            cell.fill = total_fill
            cell.border = border
            
            # Closing balance
            cell = ws.cell(row=row, column=6)
            cell.value = account_info.get('closing_balance', 0)
            cell.number_format = '#,##0.00'
            cell.font = subheader_font
            cell.fill = total_fill
            cell.border = border
            
            row += 2
        
        # Auto-adjust column widths
        for col in range(1, 7):
            column_letter = get_column_letter(col)
            ws.column_dimensions[column_letter].width = 18
        
        ws.column_dimensions['C'].width = 40  # Description column
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return output
    
    @staticmethod
    def create_simple_report_excel(
        report_data: Dict[str, Any],
        society_info: Dict[str, Any],
        report_title: str,
        columns: List[str],
        data_key: str
    ) -> BytesIO:
        """
        Create Excel file for simple table reports
        
        Args:
            report_data: Report data dictionary
            society_info: Society information
            report_title: Title of the report
            columns: Column headers
            data_key: Key in report_data containing the table data
            
        Returns:
            BytesIO: Excel file in memory
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = report_title[:31]  # Excel sheet name limit
        
        # Styles
        header_font = Font(name='Arial', size=14, bold=True)
        title_font = Font(name='Arial', size=12, bold=True)
        subheader_font = Font(name='Arial', size=10, bold=True)
        normal_font = Font(name='Arial', size=10)
        
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Header
        row = 1
        ws.merge_cells(f'A{row}:{get_column_letter(len(columns))}{row}')
        cell = ws[f'A{row}']
        cell.value = society_info.get('name', 'Society Name')
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        
        row += 1
        ws.merge_cells(f'A{row}:{get_column_letter(len(columns))}{row}')
        cell = ws[f'A{row}']
        cell.value = report_title.upper()
        cell.font = title_font
        cell.alignment = Alignment(horizontal='center')
        
        if report_data.get('from_date') and report_data.get('to_date'):
            row += 1
            ws.merge_cells(f'A{row}:{get_column_letter(len(columns))}{row}')
            cell = ws[f'A{row}']
            period = f"Period: {report_data.get('from_date')} to {report_data.get('to_date')}"
            cell.value = period
            cell.font = normal_font
            cell.alignment = Alignment(horizontal='center')
        
        row += 2
        
        # Column headers
        for col_num, header in enumerate(columns, 1):
            cell = ws.cell(row=row, column=col_num)
            cell.value = header
            cell.font = Font(name='Arial', size=10, bold=True, color="FFFFFF")
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')
            cell.border = border
        
        row += 1
        
        # Data
        data = report_data.get(data_key, [])
        for item in data:
            for col_num, col_name in enumerate(columns, 1):
                cell = ws.cell(row=row, column=col_num)
                # Try to get value by lowercase key with underscores
                key = col_name.lower().replace(' ', '_')
                value = item.get(key, item.get(col_name, ''))
                cell.value = value
                if isinstance(value, (int, float)):
                    cell.number_format = '#,##0.00'
                cell.font = normal_font
                cell.border = border
            row += 1
        
        # Auto-adjust column widths
        for col in range(1, len(columns) + 1):
            column_letter = get_column_letter(col)
            ws.column_dimensions[column_letter].width = 18
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        return output


class PDFExporter:
    """PDF export functionality using ReportLab"""
    
    @staticmethod
    def create_payment_receipt_pdf(
        receipt_number: str,
        payment_date: Any,
        payment_mode: str,
        amount: float,
        late_fee: float,
        transaction_reference: Optional[str],
        bill_number: str,
        bill_date: Any,
        billing_period: str,
        member_name: str,
        flat_number: str,
        society_name: str,
        society_address: Optional[str],
        maintenance_amount: float,
        sinking_fund: float,
        other_charges: float
    ) -> BytesIO:
        """
        Create PDF payment receipt
        
        Args:
            receipt_number: Receipt number
            payment_date: Date of payment
            payment_mode: Mode of payment (cash, cheque, UPI, etc.)
            amount: Payment amount
            late_fee: Late fee charged
            transaction_reference: Cheque no, UPI ref, etc.
            bill_number: Original bill number
            bill_date: Bill date
            billing_period: Billing period (MM/YYYY)
            member_name: Member name
            flat_number: Flat number
            society_name: Society name
            society_address: Society address
            maintenance_amount: Maintenance amount
            sinking_fund: Sinking fund amount
            other_charges: Other charges
            
        Returns:
            BytesIO: PDF file in memory
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'ReceiptTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#2E7D32'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'ReceiptHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Header: Society Name
        society_para = Paragraph(society_name, title_style)
        elements.append(society_para)
        
        if society_address:
            address_para = Paragraph(society_address, ParagraphStyle(
                'Address',
                parent=styles['Normal'],
                fontSize=10,
                alignment=TA_CENTER,
                spaceAfter=20
            ))
            elements.append(address_para)
        
        # Receipt Title
        receipt_title = Paragraph("PAYMENT RECEIPT", heading_style)
        receipt_title.alignment = TA_CENTER
        elements.append(receipt_title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Receipt Info Table
        receipt_info = [
            ['Receipt No:', receipt_number, 'Date:', str(payment_date)],
            ['Bill No:', bill_number, 'Bill Date:', str(bill_date)],
            ['Member Name:', member_name, 'Flat No:', flat_number],
            ['Billing Period:', billing_period, '', '']
        ]
        
        receipt_table = Table(receipt_info, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        receipt_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1976D2')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#1976D2')),
        ]))
        elements.append(receipt_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Payment Details Heading
        payment_heading = Paragraph("PAYMENT DETAILS", ParagraphStyle(
            'PaymentHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#1976D2'),
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        elements.append(payment_heading)
        
        # Payment Details Table
        total_bill = maintenance_amount + sinking_fund + other_charges
        total_with_late_fee = amount + late_fee
        
        payment_data = [
            ['Description', 'Amount'],
            ['Maintenance Charges', f'₹{maintenance_amount:,.2f}'],
            ['Sinking Fund', f'₹{sinking_fund:,.2f}'],
            ['Other Charges', f'₹{other_charges:,.2f}'],
            ['', ''],
            ['Bill Amount', f'₹{total_bill:,.2f}'],
        ]
        
        if late_fee > 0:
            payment_data.append(['Late Fee', f'₹{late_fee:,.2f}'])
            payment_data.append(['Total Amount Paid', f'₹{total_with_late_fee:,.2f}'])
        else:
            payment_data.append(['Total Amount Paid', f'₹{amount:,.2f}'])
        
        payment_table = Table(payment_data, colWidths=[4*inch, 2.5*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -3), 0.5, colors.grey),
            ('LINEABOVE', (0, -2), (-1, -2), 2, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E3F2FD')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#C8E6C9')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2E7D32')),
        ]))
        elements.append(payment_table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Payment Mode Info
        mode_info = [
            ['Payment Mode:', payment_mode.upper()]
        ]
        if transaction_reference:
            mode_info.append(['Transaction Reference:', transaction_reference])
        
        mode_table = Table(mode_info, colWidths=[2*inch, 4.5*inch])
        mode_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#1976D2')),
        ]))
        elements.append(mode_table)
        elements.append(Spacer(1, 0.5*inch))
        
        # Footer Note
        note = Paragraph(
            "<i>This is a computer-generated receipt and does not require a signature.</i>",
            ParagraphStyle(
                'Note',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
        )
        elements.append(note)
        
        # Thank you message
        thank_you = Paragraph(
            "<b>Thank you for your payment!</b>",
            ParagraphStyle(
                'ThankYou',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#2E7D32'),
                alignment=TA_CENTER,
                spaceAfter=20
            )
        )
        elements.append(Spacer(1, 0.2*inch))
        elements.append(thank_you)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def create_general_ledger_pdf(
        report_data: Dict[str, Any],
        society_info: Dict[str, Any]
    ) -> BytesIO:
        """
        Create PDF file for General Ledger Report
        
        Args:
            report_data: Report data dictionary
            society_info: Society information (name, address, logo_url)
            
        Returns:
            BytesIO: PDF file in memory
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=0.5*inch, leftMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#366092'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#366092'),
            spaceAfter=6,
            alignment=TA_CENTER
        )
        
        # Society name
        society_name = Paragraph(society_info.get('name', 'Society Name'), title_style)
        elements.append(society_name)
        
        # Report title
        title = Paragraph("GENERAL LEDGER REPORT", heading_style)
        elements.append(title)
        
        # Period
        period = f"Period: {report_data.get('from_date', '')} to {report_data.get('to_date', '')}"
        period_para = Paragraph(period, styles['Normal'])
        period_para.alignment = TA_CENTER
        elements.append(period_para)
        elements.append(Spacer(1, 0.2*inch))
        
        # Ledger data
        ledger_data = report_data.get('ledger', {})
        
        for account_code, account_info in ledger_data.items():
            # Account header
            account_title = f"{account_code} - {account_info.get('account_name', '')}"
            account_para = Paragraph(f"<b>{account_title}</b>", styles['Heading3'])
            elements.append(account_para)
            elements.append(Spacer(1, 0.1*inch))
            
            # Table data
            table_data = [
                ['Date', 'Description', 'Debit', 'Credit', 'Balance']
            ]
            
            # Opening balance
            opening_balance = account_info.get('opening_balance', 0)
            table_data.append(['', 'Opening Balance', '', '', f"₹{opening_balance:,.2f}"])
            
            # Transactions
            for txn in account_info.get('transactions', []):
                table_data.append([
                    txn.get('date', ''),
                    txn.get('description', ''),
                    f"₹{txn.get('debit', 0):,.2f}" if txn.get('debit', 0) > 0 else '',
                    f"₹{txn.get('credit', 0):,.2f}" if txn.get('credit', 0) > 0 else '',
                    f"₹{txn.get('balance', 0):,.2f}"
                ])
            
            # Totals
            table_data.append([
                '',
                'TOTAL',
                f"₹{account_info.get('total_debit', 0):,.2f}",
                f"₹{account_info.get('total_credit', 0):,.2f}",
                f"₹{account_info.get('closing_balance', 0):,.2f}"
            ])
            
            # Create table
            table = Table(table_data, colWidths=[1*inch, 3*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#D9E1F2')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def create_simple_report_pdf(
        report_data: Dict[str, Any],
        society_info: Dict[str, Any],
        report_title: str,
        columns: List[str],
        data_key: str
    ) -> BytesIO:
        """
        Create PDF file for simple table reports
        
        Args:
            report_data: Report data dictionary
            society_info: Society information
            report_title: Title of the report
            columns: Column headers
            data_key: Key in report_data containing the table data
            
        Returns:
            BytesIO: PDF file in memory
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                               rightMargin=0.5*inch, leftMargin=0.5*inch,
                               topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#366092'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        # Society name
        society_name = Paragraph(society_info.get('name', 'Society Name'), title_style)
        elements.append(society_name)
        
        # Report title
        title = Paragraph(report_title.upper(), title_style)
        elements.append(title)
        
        # Period (if applicable)
        if report_data.get('from_date') and report_data.get('to_date'):
            period = f"Period: {report_data.get('from_date')} to {report_data.get('to_date')}"
            period_para = Paragraph(period, styles['Normal'])
            period_para.alignment = TA_CENTER
            elements.append(period_para)
        
        elements.append(Spacer(1, 0.2*inch))
        
        # Table data
        table_data = [columns]
        
        data = report_data.get(data_key, [])
        for item in data:
            row = []
            for col_name in columns:
                key = col_name.lower().replace(' ', '_')
                value = item.get(key, item.get(col_name, ''))
                if isinstance(value, (int, float)):
                    row.append(f"₹{value:,.2f}")
                else:
                    row.append(str(value))
            table_data.append(row)
        
        # Calculate column widths
        col_width = 7.0 / len(columns)
        col_widths = [col_width * inch] * len(columns)
        
        # Create table
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer

