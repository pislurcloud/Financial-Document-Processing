"""
Enhanced Document Type Definitions
Hierarchical classification: Main Type → Sub-Type
"""

from enum import Enum
from typing import List, Dict, Any


class MainDocumentType(Enum):
    """Main document categories"""
    TURNOVER = "TURNOVER"
    WORK_ORDER = "WORK_ORDER"
    UNKNOWN = "UNKNOWN"


class TurnoverSubType(Enum):
    """Turnover document sub-types (priority order)"""
    PL_STATEMENT = "P&L Statement"                    # Priority 1 - Extract data
    CA_CERTIFICATE = "CA Certificate"                 # Priority 2 - Extract data
    BALANCE_SHEET = "Balance Sheet"                   # Priority 3
    AUDITOR_REPORT = "Auditor's Report"              # Priority 4
    INCOME_TAX = "Income Tax Related"                # Priority 5
    OTHER = "Other"                                   # VLM-discovered


class WorkOrderSubType(Enum):
    """Work Order document sub-types (priority order)"""
    PURCHASE_ORDER = "Purchase Order"                 # Priority 1 - Extract data
    COMPLETION_CERTIFICATE = "Completion Certificate" # Priority 2 - Extract data
    WORK_CONTRACT = "Work Contract"                   # Priority 2 - Extract data
    STATEMENT_OF_WORK = "Statement of Work"          # Priority 2 - Extract data
    CA_CERTIFICATE = "CA Certificate"                 # Priority 2 - Extract data
    OTHER = "Other"                                   # VLM-discovered


# Mapping of sub-types to main types
SUBTYPE_TO_MAINTYPE = {
    # Turnover sub-types
    TurnoverSubType.PL_STATEMENT: MainDocumentType.TURNOVER,
    TurnoverSubType.CA_CERTIFICATE: MainDocumentType.TURNOVER,
    TurnoverSubType.BALANCE_SHEET: MainDocumentType.TURNOVER,
    TurnoverSubType.AUDITOR_REPORT: MainDocumentType.TURNOVER,
    TurnoverSubType.INCOME_TAX: MainDocumentType.TURNOVER,
    
    # Work Order sub-types
    WorkOrderSubType.PURCHASE_ORDER: MainDocumentType.WORK_ORDER,
    WorkOrderSubType.COMPLETION_CERTIFICATE: MainDocumentType.WORK_ORDER,
    WorkOrderSubType.WORK_CONTRACT: MainDocumentType.WORK_ORDER,
    WorkOrderSubType.STATEMENT_OF_WORK: MainDocumentType.WORK_ORDER,
    WorkOrderSubType.CA_CERTIFICATE: MainDocumentType.WORK_ORDER,
}


# Sub-types that require data extraction
EXTRACTION_SUBTYPES = {
    MainDocumentType.TURNOVER: [
        TurnoverSubType.PL_STATEMENT,
        TurnoverSubType.CA_CERTIFICATE
    ],
    MainDocumentType.WORK_ORDER: [
        WorkOrderSubType.PURCHASE_ORDER,
        WorkOrderSubType.COMPLETION_CERTIFICATE,
        WorkOrderSubType.WORK_CONTRACT,
        WorkOrderSubType.STATEMENT_OF_WORK,
        WorkOrderSubType.CA_CERTIFICATE
    ]
}


# Keywords for identifying each sub-type
SUBTYPE_KEYWORDS = {
    # Turnover sub-types
    TurnoverSubType.PL_STATEMENT: [
        "profit and loss", "p&l", "statement of profit and loss",
        "income statement", "revenue from operations", "expenses",
        "profit for the year", "loss for the year", "total revenue",
        "operating profit", "net profit", "ebitda"
    ],
    
    TurnoverSubType.BALANCE_SHEET: [
        "balance sheet", "financial position", "assets", "liabilities",
        "equity and liabilities", "shareholders funds", "share capital",
        "reserves and surplus", "current assets", "non-current assets",
        "property plant and equipment"
    ],
    
    TurnoverSubType.CA_CERTIFICATE: [
        "chartered accountant", "ca certificate", "certification",
        "certified that", "examined", "audit", "icai", "membership number",
        "firm registration number", "udin"
    ],
    
    TurnoverSubType.AUDITOR_REPORT: [
        "auditor's report", "independent auditor", "audit opinion",
        "audited financial statements", "basis for opinion",
        "key audit matters", "material uncertainty", "emphasis of matter"
    ],
    
    TurnoverSubType.INCOME_TAX: [
        "income tax", "form 16", "form 16a", "tds certificate",
        "tax deducted at source", "tds", "income tax return", "itr",
        "tax computation", "advance tax", "assessment year", "pan"
    ],
    
    # Work Order sub-types
    WorkOrderSubType.PURCHASE_ORDER: [
        "purchase order", "po#", "order no", "order number",
        "vendor", "supplier", "buyer", "delivery address",
        "items", "quantity", "rate", "amount", "grand total",
        "gstin", "gst", "invoice"
    ],
    
    WorkOrderSubType.COMPLETION_CERTIFICATE: [
        "completion certificate", "work completion", "certificate of completion",
        "completed work", "satisfactory completion", "work done",
        "issued to", "certified that the work"
    ],
    
    WorkOrderSubType.WORK_CONTRACT: [
        "contract", "agreement", "contract agreement", "party of the first part",
        "party of the second part", "contractor", "contractee",
        "terms and conditions", "scope of work", "contract value",
        "contract period", "penalty clause"
    ],
    
    WorkOrderSubType.STATEMENT_OF_WORK: [
        "statement of work", "sow", "scope of work", "work breakdown",
        "deliverables", "milestones", "project scope", "work description",
        "tasks", "activities", "work items"
    ],
    
    WorkOrderSubType.CA_CERTIFICATE: [
        "chartered accountant", "ca certificate", "certification",
        "certified that", "examined", "work order", "turnover certificate"
    ]
}


def get_all_subtypes() -> List[str]:
    """Get list of all possible sub-types"""
    turnover_subtypes = [st.value for st in TurnoverSubType]
    wo_subtypes = [st.value for st in WorkOrderSubType]
    return turnover_subtypes + wo_subtypes


def requires_extraction(main_type: MainDocumentType, sub_type: str) -> bool:
    """Check if a sub-type requires data extraction"""
    if main_type not in EXTRACTION_SUBTYPES:
        return False
    
    extraction_list = EXTRACTION_SUBTYPES[main_type]
    
    # Check if sub_type matches any in extraction list
    for extract_subtype in extraction_list:
        if extract_subtype.value == sub_type:
            return True
    
    return False


def get_subtype_priority(main_type: MainDocumentType, sub_type: str) -> int:
    """Get priority of a sub-type (lower number = higher priority)"""
    priority_map = {
        # Turnover priorities
        TurnoverSubType.PL_STATEMENT.value: 1,
        TurnoverSubType.CA_CERTIFICATE.value: 2,
        TurnoverSubType.BALANCE_SHEET.value: 3,
        TurnoverSubType.AUDITOR_REPORT.value: 4,
        TurnoverSubType.INCOME_TAX.value: 5,
        TurnoverSubType.OTHER.value: 10,
        
        # Work Order priorities
        WorkOrderSubType.PURCHASE_ORDER.value: 1,
        WorkOrderSubType.COMPLETION_CERTIFICATE.value: 2,
        WorkOrderSubType.WORK_CONTRACT.value: 2,
        WorkOrderSubType.STATEMENT_OF_WORK.value: 2,
        WorkOrderSubType.CA_CERTIFICATE.value: 2,
        WorkOrderSubType.OTHER.value: 10
    }
    
    return priority_map.get(sub_type, 99)


def classify_ca_certificate_context(
    page_classifications: List[Dict[str, Any]]
) -> MainDocumentType:
    """
    Determine if CA Certificate belongs to Turnover or Work Order
    based on context (surrounding documents)
    
    Args:
        page_classifications: List of page classifications with main_type
        
    Returns:
        MainDocumentType for the CA Certificate
    """
    # Count main types in surrounding pages
    turnover_count = sum(1 for p in page_classifications 
                         if p.get('main_type') == MainDocumentType.TURNOVER.value)
    wo_count = sum(1 for p in page_classifications 
                   if p.get('main_type') == MainDocumentType.WORK_ORDER.value)
    
    # CA Certificate takes the context of majority
    if turnover_count > wo_count:
        return MainDocumentType.TURNOVER
    elif wo_count > turnover_count:
        return MainDocumentType.WORK_ORDER
    else:
        # Default to Turnover if ambiguous
        return MainDocumentType.TURNOVER