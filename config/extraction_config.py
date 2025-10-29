"""
Field Extraction Configuration
Defines fields, validation rules, and extraction strategies
"""

from typing import Dict, Any, List

# Company types to detect
COMPANY_TYPES = [
    "Private Limited",
    "Public Limited", 
    "Proprietorship",
    "Partnership",
    "LLP (Limited Liability Partnership)",
    "Other"
]

# Work Order Field Definitions
WORK_ORDER_FIELDS = {
    "wo_id": {
        "name": "Work Order ID/Number",
        "description": "Unique identifier for the work order",
        "required": True,
        "type": "string",
        "examples": ["Order No 456/902804", "WO-2021-001", "PO#12345"],
        "keywords": ["Order No", "WO#", "Work Order", "Purchase Order", "PO#", "Invoice No"],
        "min_confidence": 0.7,
        "validation": {
            "min_length": 3,
            "max_length": 100
        }
    },
    
    "wo_amount": {
        "name": "Work Order Amount (Grand Total)",
        "description": "Total amount for the work order",
        "required": True,
        "type": "number",
        "examples": ["Rs. 63,090", "₹1,23,456", "$1,234.56"],
        "keywords": ["Grand Total", "Total", "Total INR", "Amount", "Total Amount"],
        "min_confidence": 0.8,
        "validation": {
            "min_value": 0,
            "currency_aware": True
        },
        "note": "Extract GRAND TOTAL only, not line items. Include currency symbol and format (Lakhs/Crores)"
    },
    
    "client_name": {
        "name": "Client/Buyer Name",
        "description": "Name of the client or organization receiving the work",
        "required": True,
        "type": "string",
        "examples": ["HIL (India) Limited", "Adwit India Pvt Ltd", "ABC Corporation"],
        "keywords": ["Client", "Buyer", "Customer", "Delivery Address", "Bill To"],
        "min_confidence": 0.7,
        "validation": {
            "min_length": 3,
            "max_length": 200
        }
    },
    
    "details": {
        "name": "Work Details/Description",
        "description": "Description of goods or services provided",
        "required": False,
        "type": "string",
        "examples": ["Magazine Printing - Rakshak Issue 10", "Software Development Services"],
        "keywords": ["Description", "Particulars", "Details", "Items", "Services"],
        "min_confidence": 0.6,
        "validation": {
            "max_length": 1000
        }
    },
    
    "date": {
        "name": "Order Date",
        "description": "Date when the order was issued",
        "required": False,
        "type": "date",
        "examples": ["2021-07-20", "20/07/2021", "20.07.2021", "July 20, 2021"],
        "keywords": ["Date", "Order Date", "Issue Date", "Dated"],
        "min_confidence": 0.8,
        "validation": {
            "formats": ["YYYY-MM-DD", "DD/MM/YYYY", "DD.MM.YYYY", "Month DD, YYYY"]
        }
    },
    
    "currency": {
        "name": "Currency",
        "description": "Currency used in the work order",
        "required": False,
        "type": "string",
        "examples": ["INR", "USD", "EUR", "Rs", "₹", "$"],
        "default": "INR",
        "min_confidence": 0.9,
        "validation": {
            "allowed_values": ["INR", "USD", "EUR", "GBP", "Rs", "₹", "$"]
        },
        "note": "Mostly INR, but detect if present"
    },
    
    "vendor_name": {
        "name": "Vendor/Supplier Name",
        "description": "Name of the vendor providing the work",
        "required": False,
        "type": "string",
        "examples": ["Adwit (India) Pvt. Ltd.", "ABC Suppliers"],
        "keywords": ["Vendor", "Supplier", "From", "Service Provider"],
        "min_confidence": 0.7
    }
}

# Turnover Field Definitions
TURNOVER_FIELDS = {
    "total_turnover": {
        "name": "Total Turnover/Revenue",
        "description": "Main revenue/turnover figure for the period",
        "required": True,
        "type": "number",
        "examples": ["Rs. 9,75,87,508", "₹5.2 Crores", "₹12,34,56,789"],
        "keywords": [
            "Revenue from operations",
            "Total Revenue", 
            "Sales",
            "Turnover",
            "Total Income",
            "Operating Revenue",
            "Net Sales"
        ],
        "min_confidence": 0.9,
        "validation": {
            "min_value": 0,
            "currency_aware": True
        },
        "extraction_strategy": "FLEXIBLE - Use logical understanding. Turnover may NOT be labeled as 'Revenue from operations'. Could be 'Sales', 'Total Income', 'Operating Revenue', etc. Prioritize the MAIN revenue figure from P&L statement.",
        "note": "Store with currency symbol and format (Lakhs/Crores). Example: 'Rs. 9,75,87,508' or '₹5.2 Crores'"
    },
    
    "period": {
        "name": "Financial Period",
        "description": "The financial year or period covered",
        "required": True,
        "type": "string",
        "examples": ["FY 2023-24", "Year ending March 31, 2024", "Q4 2024", "2023-2024"],
        "keywords": ["For the year ended", "Year ending", "FY", "Financial Year", "Period ended", "As at"],
        "min_confidence": 0.8,
        "validation": {
            "patterns": ["FY", "year ending", "ended", "20\\d{2}", "Q[1-4]"]
        },
        "extraction_strategy": "SPECIFIC YEAR ONLY - Extract the specific year mentioned in the header. Do NOT extract previous year comparison data.",
        "note": "Extract from document header/title. Focus on current period only."
    },
    
    "company_name": {
        "name": "Company Name",
        "description": "Full legal name of the company",
        "required": True,
        "type": "string",
        "examples": [
            "THE INFORMATION COMPANY PRIVATE LIMITED",
            "ABC CORPORATION LIMITED",
            "XYZ INDUSTRIES"
        ],
        "keywords": ["Company", "Ltd", "Limited", "Pvt", "Private"],
        "min_confidence": 0.8,
        "validation": {
            "min_length": 5,
            "max_length": 200
        }
    },
    
    "company_type": {
        "name": "Company Type",
        "description": "Type of business organization",
        "required": False,
        "type": "string",
        "allowed_values": COMPANY_TYPES,
        "examples": ["Private Limited", "Public Limited", "Proprietorship", "Partnership", "LLP"],
        "detection_patterns": {
            "Private Limited": ["PRIVATE LIMITED", "PVT LTD", "PVT. LTD.", "PRIVATE LTD"],
            "Public Limited": ["PUBLIC LIMITED", "LTD", "LIMITED"],
            "Proprietorship": ["PROPRIETORSHIP", "PROPRIETOR"],
            "Partnership": ["PARTNERSHIP", "PARTNERS"],
            "LLP": ["LLP", "LIMITED LIABILITY PARTNERSHIP"],
            "Other": []
        },
        "min_confidence": 0.7,
        "note": "Detect from company name suffix or document text"
    },
    
    "currency": {
        "name": "Currency",
        "description": "Currency used in financial statements",
        "required": False,
        "type": "string",
        "examples": ["INR", "Rs", "₹"],
        "default": "INR",
        "min_confidence": 0.9,
        "validation": {
            "allowed_values": ["INR", "USD", "EUR", "GBP", "Rs", "₹", "$"]
        },
        "note": "Mostly INR, but detect if present"
    },
    
    "other_income": {
        "name": "Other Income",
        "description": "Income from sources other than main operations",
        "required": False,
        "type": "number",
        "examples": ["Rs. 20,47,114"],
        "keywords": ["Other Income", "Other Revenue"],
        "min_confidence": 0.7,
        "note": "Secondary field, not critical"
    }
}

# Confidence thresholds for human review
HUMAN_REVIEW_THRESHOLDS = {
    "min_confidence": 0.70,  # Below this = needs review
    "missing_required_field": True,  # Any missing required field = needs review
    "low_quality_score": 0.60  # Overall quality < 60% = needs review
}

# Quality scoring weights
QUALITY_WEIGHTS = {
    "required_fields_present": 0.5,  # 50% weight
    "average_confidence": 0.3,       # 30% weight
    "all_fields_valid": 0.2          # 20% weight
}


def get_field_config(document_type: str) -> Dict[str, Any]:
    """Get field configuration for a document type"""
    if document_type == "WORK_ORDER":
        return WORK_ORDER_FIELDS
    elif document_type == "TURNOVER":
        return TURNOVER_FIELDS
    else:
        return {}


def get_required_fields(document_type: str) -> List[str]:
    """Get list of required fields for a document type"""
    config = get_field_config(document_type)
    return [field for field, info in config.items() if info.get("required", False)]