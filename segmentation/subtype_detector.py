"""
Enhanced Page Analyzer with Sub-Type Detection
Analyzes pages and identifies specific document sub-types
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.document_types_enhanced import (
    MainDocumentType, TurnoverSubType, WorkOrderSubType,
    SUBTYPE_KEYWORDS, get_all_subtypes
)


# VLM Prompt for sub-type detection
SUBTYPE_DETECTION_PROMPT = """Analyze this document page and identify its SPECIFIC type.

**TURNOVER Document Types:**
1. P&L Statement (Profit & Loss / Income Statement) - Shows revenue, expenses, profit/loss
2. Balance Sheet - Shows assets, liabilities, equity
3. CA Certificate - Chartered Accountant certification
4. Auditor's Report - Independent auditor's opinion
5. Income Tax Related - Form 16, TDS certificates, ITR, tax computation
6. Other - Any other financial document type

**WORK ORDER Document Types:**
1. Purchase Order - Order for goods/services with items, quantities, amounts
2. Completion Certificate - Certificate confirming work completion
3. Work Contract - Legal agreement for work/services
4. Statement of Work - Detailed scope, deliverables, milestones
5. CA Certificate - Chartered Accountant certification for work/turnover
6. Other - Any other work-related document type

**Your Task:**
1. Identify the MAIN category: TURNOVER or WORK_ORDER
2. Identify the SPECIFIC sub-type from the lists above
3. If it's a NEW type not in the lists, describe it as "Other: [Your Description]"
4. Provide confidence (0.0-1.0)
5. List key indicators you found

**Context-based CA Certificate:**
- If with financial statements (P&L, Balance Sheet) → TURNOVER CA Certificate
- If with work orders, contracts → WORK_ORDER CA Certificate

**Respond ONLY with valid JSON:**
{{
    "main_type": "TURNOVER or WORK_ORDER",
    "sub_type": "exact sub-type name from list above",
    "confidence": 0.0-1.0,
    "key_indicators": ["list", "of", "key", "text", "found"],
    "reasoning": "explain why you classified it this way"
}}

**Examples:**

Page with "Revenue from operations: Rs. 9,75,87,508" and "Profit for the year":
{{
    "main_type": "TURNOVER",
    "sub_type": "P&L Statement",
    "confidence": 0.95,
    "key_indicators": ["Revenue from operations", "Profit for the year", "Statement of Profit and Loss"],
    "reasoning": "Clear P&L structure with revenue and profit figures"
}}

Page with "Purchase Order No: 12345" and "Supplier: ABC Ltd" and item list:
{{
    "main_type": "WORK_ORDER",
    "sub_type": "Purchase Order",
    "confidence": 0.92,
    "key_indicators": ["Purchase Order", "Order No", "Supplier", "Items", "Grand Total"],
    "reasoning": "Purchase order format with supplier, items, and pricing"
}}
"""


def detect_subtype_from_keywords(text_snippets: list) -> tuple:
    """
    Detect sub-type based on keyword matching
    Fallback method when VLM doesn't provide sub-type
    
    Args:
        text_snippets: List of text snippets from page
        
    Returns:
        (main_type, sub_type, confidence) tuple
    """
    if not text_snippets:
        return None, None, 0.0
    
    combined_text = ' '.join(text_snippets).lower()
    
    # Score each sub-type
    scores = {}
    
    # Check Turnover sub-types
    for subtype in TurnoverSubType:
        keywords = SUBTYPE_KEYWORDS.get(subtype, [])
        matches = sum(1 for kw in keywords if kw in combined_text)
        if matches > 0:
            scores[subtype] = matches
    
    # Check Work Order sub-types
    for subtype in WorkOrderSubType:
        keywords = SUBTYPE_KEYWORDS.get(subtype, [])
        matches = sum(1 for kw in keywords if kw in combined_text)
        if matches > 0:
            scores[subtype] = matches
    
    if not scores:
        return None, None, 0.0
    
    # Get best match
    best_subtype = max(scores, key=scores.get)
    max_matches = scores[best_subtype]
    
    # Determine main type
    if isinstance(best_subtype, TurnoverSubType):
        main_type = MainDocumentType.TURNOVER.value
        sub_type = best_subtype.value
    else:
        main_type = MainDocumentType.WORK_ORDER.value
        sub_type = best_subtype.value
    
    # Calculate confidence
    total_keywords = len(SUBTYPE_KEYWORDS.get(best_subtype, []))
    confidence = min(max_matches / (total_keywords * 0.3), 1.0)  # Need 30% match for 1.0 confidence
    confidence = max(confidence, 0.3)  # Minimum 30% confidence
    
    return main_type, sub_type, confidence


def enhance_page_analysis_with_subtype(
    page_analysis: dict,
    use_vlm: bool = True
) -> dict:
    """
    Enhance existing page analysis with sub-type detection
    
    Args:
        page_analysis: Existing page analysis from Phase 1
        use_vlm: Whether to use VLM for sub-type detection
        
    Returns:
        Enhanced analysis with sub-type information
    """
    if not page_analysis.get('success'):
        return page_analysis
    
    data = page_analysis.get('data', {})
    text_snippets = data.get('key_text_snippets', [])
    
    # Detect sub-type using keywords (always do this as fallback)
    main_type, sub_type, confidence = detect_subtype_from_keywords(text_snippets)
    
    # Add to analysis
    if main_type and sub_type:
        data['main_type'] = main_type
        data['sub_type'] = sub_type
        data['sub_type_confidence'] = confidence
        data['detection_method'] = 'keyword'
    else:
        # Unknown
        data['main_type'] = MainDocumentType.UNKNOWN.value
        data['sub_type'] = 'Unknown'
        data['sub_type_confidence'] = 0.0
        data['detection_method'] = 'none'
    
    page_analysis['data'] = data
    return page_analysis


def get_subtype_analysis_prompt() -> str:
    """Get the VLM prompt for sub-type detection"""
    return SUBTYPE_DETECTION_PROMPT