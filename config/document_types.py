"""
Document Type Definitions for Commercial Documents
Defines Work Orders and Turnover (Financial Statement) types
"""

from enum import Enum
from typing import Dict, List


class DocumentType(Enum):
    """Supported commercial document types"""
    WORK_ORDER = "work_order"
    TURNOVER = "turnover"
    UNKNOWN = "unknown"


# Document type configurations
DOCUMENT_CONFIGS: Dict[DocumentType, Dict] = {
    DocumentType.TURNOVER: {
        "name": "Turnover Document",
        "description": "Financial turnover/revenue reports (P&L Statement)",
        "keywords": [
            "turnover", "revenue", "sales", "financial statement",
            "income statement", "profit and loss", "P&L",
            "Revenue from operations", "Total income"
        ],
        "required_fields": [
            "period",
            "total_turnover",
            "currency"
        ],
        "optional_fields": [
            "breakdown",
            "comparison",
            "growth_rate",
            "margins",
            "company_name",
            "company_type"  # Pvt Ltd, Public Ltd, Proprietorship, Partnership
        ],
        "typical_pages": "2-10",
        "page_indicators": [
            "Balance Sheet",
            "Statement of Profit and Loss",
            "Revenue from operations",
            "Total income",
            "Shareholders' Funds"
        ]
    },
    
    DocumentType.WORK_ORDER: {
        "name": "Work Order",
        "description": "Job orders with line items and pricing",
        "keywords": [
            "work order", "job order", "service order", "WO#",
            "purchase order", "PO#", "delivery address",
            "completion certificate", "invoice"
        ],
        "required_fields": [
            "work_order_number",
            "date",
            "line_items",
            "total"
        ],
        "optional_fields": [
            "customer",
            "project",
            "location",
            "status",
            "client_name",
            "details"  # Description of work or items supplied
        ],
        "typical_pages": "1-5",
        "page_indicators": [
            "PURCHASE ORDER",
            "Work Order",
            "WO",
            "Order No",
            "Delivery Address",
            "GSTIN",
            "Invoice No"
        ]
    }
}


# Page type classification
class PageType(Enum):
    """Types of pages in documents"""
    TITLE_PAGE = "title_page"           # Cover page with main title
    DATA_PAGE = "data_page"             # Contains extractable business data
    SEPARATOR = "separator"              # Blank or separator page
    TOC = "toc"                         # Table of contents
    CONTINUATION = "continuation"        # Middle of multi-page document
    END_PAGE = "end_page"               # Last page (may have signature)
    MAGAZINE_LAYOUT = "magazine_layout" # Magazine/brochure pages
    CERTIFICATE = "certificate"         # Completion certificates


# VLM prompt templates
PAGE_ANALYSIS_PROMPT = """You are analyzing page {page_number} of {total_pages} from a business document.

**Your Task:**
Analyze this page and determine:

1. **Page Type:**
   - TITLE_PAGE: Cover page with main title
   - DATA_PAGE: Contains extractable business data (tables, forms, key values)
   - SEPARATOR: Blank or separator page between documents
   - TOC: Table of contents
   - CONTINUATION: Middle of a multi-page document
   - END_PAGE: Last page (may have signature, "end of document")
   - MAGAZINE_LAYOUT: Magazine/brochure design pages
   - CERTIFICATE: Completion or achievement certificates

2. **Document Type Hints:**
   Based on visible text and layout, what type of document might this be from:
   - TURNOVER: Financial turnover/revenue report (keywords: revenue, sales, turnover, P&L, profit and loss, income statement)
   - WORK_ORDER: Work/job order (keywords: work order, WO#, job order, service order, purchase order, PO#)
   - OTHER: Something else

3. **Document Boundaries:**
   - is_document_start: Does this look like the FIRST page of a new document?
     (Has document title, "Page 1 of X", fresh header, etc.)
   - is_document_end: Does this look like the LAST page of a document?
     (Has "Page X of X", signature, "End of document", etc.)
   - continues_previous: Does this seem to continue from previous page?

4. **Key Identifiers:**
   Extract any visible:
   - Document ID/Number (e.g., "WO-2024-001", "Turnover Report Q4-2024")
   - Dates
   - Company/Customer names
   - Page numbers (e.g., "Page 3 of 5")

5. **Data Assessment:**
   - has_tables: Are there data tables?
   - has_forms: Are there fillable forms?
   - has_key_values: Key-value pairs (e.g., "Total: $1000")?
   - data_density: LOW, MEDIUM, HIGH (how much extractable data?)

**Respond ONLY with valid JSON in this exact format:**
{{
    "page_type": "TITLE_PAGE|DATA_PAGE|SEPARATOR|TOC|CONTINUATION|END_PAGE|MAGAZINE_LAYOUT|CERTIFICATE",
    "document_type_hints": ["TURNOVER", "WORK_ORDER"],
    "is_document_start": true/false,
    "is_document_end": true/false,
    "continues_previous": true/false,
    "identifiers": {{
        "document_id": "string or null",
        "document_title": "string or null",
        "date": "YYYY-MM-DD or null",
        "page_indicator": "Page 3 of 5 or null",
        "company_name": "string or null"
    }},
    "data_assessment": {{
        "has_tables": true/false,
        "has_forms": true/false,
        "has_key_values": true/false,
        "data_density": "LOW|MEDIUM|HIGH"
    }},
    "confidence": 0.0-1.0,
    "key_text_snippets": ["snippet1", "snippet2"],
    "notes": "any observations"
}}"""


def get_page_analysis_prompt(page_number: int, total_pages: int) -> str:
    """Get formatted page analysis prompt"""
    return PAGE_ANALYSIS_PROMPT.format(
        page_number=page_number,
        total_pages=total_pages
    )
