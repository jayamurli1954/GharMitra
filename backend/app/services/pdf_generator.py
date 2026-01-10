"""
PDF Generator Service
Generates PDFs in memory WITHOUT storing them.
Critical: No file writes, no database storage.
"""
from io import BytesIO
from typing import Dict
import logging
import warnings
import sys
import os
import platform

logger = logging.getLogger(__name__)

# Suppress all WeasyPrint-related warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

# On Windows, skip WeasyPrint entirely (it requires system libraries that are hard to install)
# On Linux/Mac, try to use WeasyPrint, but fall back to reportlab if it fails
IS_WINDOWS = platform.system() == 'Windows'

HAS_WEASYPRINT = False
# Skip WeasyPrint on Windows - it requires system libraries (Pango, Cairo) that are difficult to install
# On Windows, we'll use reportlab which works without system dependencies
if not IS_WINDOWS:
    # Only try WeasyPrint on non-Windows systems
    try:
        from weasyprint import HTML, CSS
        HAS_WEASYPRINT = True
    except (ImportError, OSError, Exception):
        # Silently fail - we'll use reportlab instead
        HAS_WEASYPRINT = False

try:
    # Fallback: Try reportlab
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
    logger.warning("reportlab not installed. PDF generation may not work.")


class PDFGenerator:
    """
    Generate PDFs in memory WITHOUT storing.
    Critical: No file writes, no database storage.
    """
    
    def __init__(self):
        self.options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
        }
    
    def render_template(self, template_html: str, data: Dict[str, str]) -> str:
        """
        Render HTML template with data.
        Uses simple {{variable_name}} replacement.
        """
        rendered_html = template_html
        
        # Replace all {{variable}} with actual values
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            rendered_html = rendered_html.replace(placeholder, str(value))
        
        return rendered_html
    
    def html_to_pdf_weasyprint(self, html_content: str) -> bytes:
        """
        Convert HTML to PDF using weasyprint (preferred method).
        Returns PDF as bytes (NOT saved to disk).
        """
        try:
            # Generate PDF directly to BytesIO buffer (in-memory file)
            pdf_buffer = BytesIO()
            
            # Convert HTML to PDF
            HTML(string=html_content).write_pdf(pdf_buffer)
            
            # Get PDF bytes
            pdf_bytes = pdf_buffer.getvalue()
            
            # Close buffer (cleanup)
            pdf_buffer.close()
            
            return pdf_bytes
        except Exception as e:
            logger.error(f"Error generating PDF with weasyprint: {e}")
            raise
    
    def html_to_pdf_reportlab(self, html_content: str, header_data: Dict[str, str] = None) -> bytes:
        """
        Convert HTML to PDF using reportlab.
        This is the recommended method for Windows (no system dependencies).
        """
        try:
            from reportlab.lib.utils import ImageReader
            from reportlab.platypus import Table, TableStyle, Image, KeepTogether
            from reportlab.lib import colors
            from reportlab.lib.units import cm
            import re
            import requests
            from urllib.parse import urlparse
            
            pdf_buffer = BytesIO()
            
            # Create PDF document with A4 size
            doc = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=1*inch,  # More space for header
                bottomMargin=0.75*inch
            )
            
            styles = getSampleStyleSheet()
            story = []
            
            # Add header with logo, society name, and address
            if header_data and (header_data.get('society_name') or header_data.get('society_address')):
                from reportlab.lib.styles import ParagraphStyle
                
                # Left column: Logo (if available)
                logo_element = None
                if header_data.get('society_logo_url'):
                    try:
                        # Download logo image
                        import requests
                        response = requests.get(header_data['society_logo_url'], timeout=5)
                        if response.status_code == 200:
                            logo_element = Image(BytesIO(response.content), width=60, height=60)
                    except Exception as e:
                        logger.warning(f"Could not load logo: {e}")
                
                # Right column: Society name and address (combined as single paragraph)
                info_text = ""
                if header_data.get('society_name'):
                    info_text += f"<b><font size=16>{header_data['society_name']}</font></b>"
                if header_data.get('society_address'):
                    if info_text:
                        info_text += "<br/>"
                    info_text += f"<font size=10 color='#666666'>{header_data['society_address']}</font>"
                
                # Create header table: Logo on left, Name/Address on right
                header_cells = []
                if logo_element:
                    header_cells.append(logo_element)
                    header_cells.append(Paragraph(info_text, styles['Normal']))
                    
                    header_table = Table(
                        [header_cells],
                        colWidths=[2.5*cm, 14.5*cm],
                        style=TableStyle([
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('LEFTPADDING', (0, 0), (-1, -1), 6),
                            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                            ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ])
                    )
                    story.append(header_table)
                else:
                    # No logo, just add the text as a centered paragraph
                    name_style = ParagraphStyle(
                        'HeaderName',
                        parent=styles['Normal'],
                        alignment=1,  # Center alignment
                        fontSize=16,
                        textColor=colors.HexColor('#1a1a1a'),
                        spaceAfter=6
                    )
                    if header_data.get('society_name'):
                        story.append(Paragraph(header_data['society_name'], name_style))
                    if header_data.get('society_address'):
                        address_style = ParagraphStyle(
                            'HeaderAddress',
                            parent=styles['Normal'],
                            alignment=1,  # Center alignment
                            fontSize=10,
                            textColor=colors.HexColor('#666666')
                        )
                        story.append(Paragraph(header_data['society_address'], address_style))
                
                story.append(Spacer(1, 0.2*cm))
                
                # Add separator line (horizontal line)
                separator = Table(
                    [['']],
                    colWidths=[17*cm],
                    style=TableStyle([
                        ('LINEBELOW', (0, 0), (-1, -1), 1, colors.HexColor('#000000')),
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('TOPPADDING', (0, 0), (-1, -1), 0),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ])
                )
                story.append(separator)
                story.append(Spacer(1, 0.4*cm))
            
            # Parse HTML content
            # Remove script and style tags
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Extract text from HTML
            # Remove HTML tags but preserve structure
            text = re.sub(r'<[^>]+>', '\n', html_content)
            # Clean up whitespace
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Process lines and create paragraphs
            for line in lines:
                if line:
                    # Handle headings (lines that are all caps or short)
                    if len(line) < 100 and line.isupper():
                        story.append(Paragraph(line, styles['Heading1']))
                    else:
                        # Escape HTML entities that might be in the text
                        line = line.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                        story.append(Paragraph(line, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            pdf_bytes = pdf_buffer.getvalue()
            pdf_buffer.close()
            
            return pdf_bytes
        except Exception as e:
            logger.error(f"Error generating PDF with reportlab: {e}")
            raise
    
    def html_to_pdf(self, html_content: str, header_data: Dict[str, str] = None) -> bytes:
        """
        Convert HTML to PDF in memory.
        Returns PDF as bytes (NOT saved to disk).
        
        Args:
            html_content: HTML content to convert
            header_data: Optional dict with 'society_name', 'society_address', 'society_logo_url'
        """
        # Prefer reportlab on Windows (works better without system dependencies)
        if HAS_REPORTLAB:
            return self.html_to_pdf_reportlab(html_content, header_data)
        elif HAS_WEASYPRINT:
            # For weasyprint, we need to inject header into HTML
            if header_data:
                html_content = self._inject_header_to_html(html_content, header_data)
            return self.html_to_pdf_weasyprint(html_content)
        else:
            raise RuntimeError(
                "No PDF library available. Please install reportlab (recommended for Windows) or weasyprint.\n"
                "Install: pip install reportlab\n"
                "Or for weasyprint (requires system libraries): pip install weasyprint"
            )
    
    def _inject_header_to_html(self, html_content: str, header_data: Dict[str, str]) -> str:
        """Inject header with logo into HTML content for weasyprint"""
        logo_html = ''
        if header_data.get('society_logo_url'):
            logo_html = f'<img src="{header_data["society_logo_url"]}" style="width: 60px; height: 60px; float: left; margin-right: 20px;" />'
        
        name_html = ''
        if header_data.get('society_name'):
            name_html = f'<h2 style="margin: 0; font-size: 16px; color: #1a1a1a;">{header_data["society_name"]}</h2>'
        
        address_html = ''
        if header_data.get('society_address'):
            address_html = f'<p style="margin: 5px 0 0 0; font-size: 10px; color: #666666;">{header_data["society_address"]}</p>'
        
        header_html = f'''
        <div style="margin-bottom: 20px; overflow: hidden;">
            {logo_html}
            <div style="margin-left: 80px;">
                {name_html}
                {address_html}
            </div>
        </div>
        <hr style="border: 1px solid #000; margin: 10px 0 20px 0;" />
        '''
        
        # Insert header after <body> tag
        if '<body' in html_content:
            html_content = html_content.replace('<body>', f'<body>{header_html}')
            html_content = html_content.replace('<body ', f'<body {header_html}')
        else:
            # If no body tag, insert at the beginning
            html_content = header_html + html_content
        
        return html_content
    
    def generate_document(
        self,
        template_html: str,
        form_data: Dict[str, str],
        header_data: Dict[str, str] = None
    ) -> bytes:
        """
        Main method: Generate PDF from template + data.
        
        CRITICAL: This all happens in memory (RAM).
        No files written to disk.
        No database storage.
        
        Args:
            template_html: HTML template with {{variables}}
            form_data: Data to fill in template
            header_data: Optional header data (society_name, society_address, society_logo_url)
        """
        # 1. Render HTML
        rendered_html = self.render_template(template_html, form_data)
        
        # 2. Convert to PDF with header
        pdf_bytes = self.html_to_pdf(rendered_html, header_data)
        
        # 3. Return PDF bytes
        # (rendered_html and form_data will be garbage collected after return)
        return pdf_bytes


# Singleton instance
pdf_generator = PDFGenerator()

