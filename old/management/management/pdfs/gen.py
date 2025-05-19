import base64
from datetime import datetime, timedelta
import markdown2
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
import logging
logger = logging.getLogger(__name__)
def generate_pdf_from_markdown(markdown_content: str, stylesheet=None) -> str:
    """
    Converts markdown content to PDF with optional CSS styling
    Returns base64 encoded PDF string
    """
    try:
        # Convert markdown to HTML
        html_content = markdown2.markdown(markdown_content)
        
        # Basic CSS styling if none provided
        if not stylesheet:
            stylesheet = """
            body { font-family: Arial, sans-serif; line-height: 1.6; }
            h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }
            h2 { color: #2980b9; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .footer { margin-top: 50px; font-size: 0.8em; color: #7f8c8d; }
            """
        
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        pdf = html.write_pdf(stylesheets=[stylesheet], font_config=font_config)
        
        return base64.b64encode(pdf).decode('utf-8')
    
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise RuntimeError(f"Failed to generate PDF: {str(e)}")


def generate_quotation_pdf(quotation_data: dict) -> dict:
    """
    Generates a professional quotation PDF with company branding
    """
    try:
        # Prepare the markdown content
        markdown_content = f"""
# AquaPure Solutions
**Water Treatment Specialists**  
Email: info@aquapure.co.ke | Phone: +254 700 000 000

---

## QUOTATION
**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Quotation #:** Q-{datetime.now().strftime('%Y%m%d-%H%M')}  
**Client:** {quotation_data.get('client_name', 'Client Name')}  
**Valid Until:** {(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')}

---

### Project Summary:
{quotation_data.get('project_summary', 'Water treatment system installation')}

---

### Equipment & Pricing:
{quotation_data.get('equipment_table', '')}

---

### Terms & Conditions:
1. Prices are in Kenyan Shillings (KES)
2. 50% advance payment required
3. Standard 1-year warranty on all equipment
4. Installation timeline: {quotation_data.get('timeline', '2-4 weeks after payment')}

---

**Prepared by:**  
[Your Name]  
Sales Engineer, AquaPure Solutions
        """
        
        # Generate PDF
        pdf_base64 = generate_pdf_from_markdown(markdown_content)
        
        return {
            "pdf_base64": pdf_base64,
            "quotation_id": f"Q-{datetime.now().strftime('%Y%m%d-%H%M')}",
            "metadata": quotation_data.get('metadata', {})
        }
    
    except Exception as e:
        logger.error(f"Quotation PDF generation failed: {str(e)}")
        return {"error": str(e)}


def generate_proposal_pdf(proposal_data: dict) -> dict:
    """
    Generates a comprehensive project proposal PDF
    """
    try:
        # Prepare markdown content with more sections
        markdown_content = f"""
# AquaPure Solutions
**Water Treatment Project Proposal**

---

## Project: {proposal_data.get('project_name', 'Water Treatment System')}

**Prepared for:** {proposal_data.get('client_name', 'Client Name')}  
**Date:** {datetime.now().strftime('%Y-%m-%d')}  
**Proposal #:** P-{datetime.now().strftime('%Y%m%d-%H%M')}

---

## Table of Contents
1. Executive Summary
2. Water Quality Analysis
3. Proposed Solution
4. System Design
5. Implementation Plan
6. Cost Breakdown
7. Company Profile

---

{proposal_data.get('content', '')}

---

## Authorization
We appreciate the opportunity to submit this proposal. Please sign below to indicate acceptance.

**Client Signature:** ________________________   Date: ________  
**AquaPure Representative:** ________________________   Date: ________
        """
        
        # More detailed styling for proposals
        proposal_stylesheet = """
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        h1 { color: #2c3e50; text-align: center; }
        h2 { color: #2980b9; border-bottom: 1px solid #3498db; }
        h3 { color: #16a085; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .signature-block { margin-top: 100px; }
        .page-break { page-break-after: always; }
        """
        
        pdf_base64 = generate_pdf_from_markdown(markdown_content, proposal_stylesheet)
        
        return {
            "pdf_base64": pdf_base64,
            "proposal_id": f"P-{datetime.now().strftime('%Y%m%d-%H%M')}",
            "metadata": proposal_data.get('metadata', {})
        }
    
    except Exception as e:
        logger.error(f"Proposal PDF generation failed: {str(e)}")
        return {"error": str(e)}