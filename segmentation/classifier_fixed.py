"""
FIXED Document Classifier
Fixes page number indexing bug that caused 0.0 confidence
"""

from typing import Dict, Any, List, Tuple
from collections import Counter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.document_types import DocumentType


class FixedClassifier:
    """Fixed classifier with robust page number matching"""
    
    def __init__(self):
        """Initialize classifier with keyword weights"""
        
        # Keywords that strongly indicate Work Order
        self.wo_keywords = [
            "work order", "purchase order", "po#", "wo#", "order no",
            "invoice", "delivery address", "vendor", "supplier",
            "gstin", "gst", "items", "quantity", "rate", "amount",
            "completion certificate", "job order"
        ]
        
        # Keywords that strongly indicate Turnover
        self.turnover_keywords = [
            "turnover", "revenue", "profit and loss", "p&l", "income statement",
            "balance sheet", "financial statement", "shareholders",
            "revenue from operations", "total revenue", "total income",
            "expenses", "profit", "loss", "fiscal year", "fy"
        ]
    
    def _extract_page_data(self, page_analyses: List[Dict[str, Any]], page_num: int) -> Dict[str, Any]:
        """
        Extract page data with multiple fallback strategies
        
        Args:
            page_analyses: List of all page analyses
            page_num: Page number to find (1-indexed)
            
        Returns:
            Page data dict or None
        """
        # Strategy 1: Match by page_number field
        for analysis in page_analyses:
            if analysis.get('page_number') == page_num and analysis.get('success'):
                return analysis.get('data', {})
        
        # Strategy 2: Use array index (0-indexed)
        try:
            idx = page_num - 1
            if 0 <= idx < len(page_analyses):
                analysis = page_analyses[idx]
                if analysis.get('success'):
                    return analysis.get('data', {})
        except:
            pass
        
        # Strategy 3: Check if data is stored differently
        for i, analysis in enumerate(page_analyses):
            # If page_number is stored in data
            if analysis.get('success'):
                data = analysis.get('data', {})
                if data.get('page_number') == page_num:
                    return data
                # Or if using array index
                if i == page_num - 1:
                    return data
        
        return None
    
    def classify_segment(
        self,
        segment_pages: List[int],
        page_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classify a document segment with robust page matching
        
        Args:
            segment_pages: List of page numbers in this segment (1-indexed)
            page_analyses: List of all page analysis results from Phase 1
            
        Returns:
            Classification result with type, confidence, and reasoning
        """
        print(f"\n🔍 Classifying segment: Pages {segment_pages[0]}-{segment_pages[-1]}")
        
        # Extract page data with robust matching
        segment_analyses = []
        for page_num in segment_pages:
            page_data = self._extract_page_data(page_analyses, page_num)
            if page_data:
                segment_analyses.append(page_data)
        
        print(f"   Found {len(segment_analyses)}/{len(segment_pages)} page analyses")
        
        if not segment_analyses:
            print(f"   ❌ No valid analyses found - trying direct array access")
            
            # Last resort: try to use pages as array indices
            for page_num in segment_pages:
                idx = page_num - 1
                if 0 <= idx < len(page_analyses):
                    analysis = page_analyses[idx]
                    if analysis.get('success'):
                        segment_analyses.append(analysis.get('data', {}))
            
            if not segment_analyses:
                return {
                    "document_type": DocumentType.UNKNOWN.value,
                    "confidence": 0.0,
                    "reasoning": "Could not extract page analyses (indexing issue)",
                    "segment_pages": segment_pages,
                    "scores": {
                        "work_order": 0.0,
                        "turnover": 0.0
                    }
                }
        
        # Score based on multiple factors
        wo_score = 0
        turnover_score = 0
        
        # Factor 1: Document type hints from Phase 1 (40% weight)
        wo_hints = 0
        turnover_hints = 0
        
        for data in segment_analyses:
            hints = data.get('document_type_hints', [])
            if 'WORK_ORDER' in hints:
                wo_hints += 1
            if 'TURNOVER' in hints:
                turnover_hints += 1
        
        print(f"   Type hints: WO={wo_hints}, Turnover={turnover_hints}")
        
        wo_score += (wo_hints / len(segment_analyses)) * 40
        turnover_score += (turnover_hints / len(segment_analyses)) * 40
        
        # Factor 2: Keyword matching (30% weight)
        all_snippets = []
        for data in segment_analyses:
            snippets = data.get('key_text_snippets', [])
            all_snippets.extend(snippets)
        
        combined_text = ' '.join(all_snippets).lower()
        
        wo_matches = sum(1 for kw in self.wo_keywords if kw in combined_text)
        turnover_matches = sum(1 for kw in self.turnover_keywords if kw in combined_text)
        
        print(f"   Keyword matches: WO={wo_matches}, Turnover={turnover_matches}")
        
        total_matches = wo_matches + turnover_matches
        if total_matches > 0:
            wo_score += (wo_matches / total_matches) * 30
            turnover_score += (turnover_matches / total_matches) * 30
        
        # Factor 3: Page types (20% weight)
        page_types = [data.get('page_type') for data in segment_analyses]
        
        if 'CERTIFICATE' in page_types:
            wo_score += 20
        
        combined_text_lower = combined_text.lower()
        if 'financial' in combined_text_lower or 'balance' in combined_text_lower or 'profit and loss' in combined_text_lower:
            turnover_score += 20
        
        # Factor 4: Document structure (10% weight)
        has_tables = any(data.get('data_assessment', {}).get('has_tables') for data in segment_analyses)
        has_forms = any(data.get('data_assessment', {}).get('has_forms') for data in segment_analyses)
        
        if has_tables:
            wo_score += 5
            turnover_score += 5
        if has_forms:
            wo_score += 5
        
        # Normalize
        wo_score = min(wo_score, 100)
        turnover_score = min(turnover_score, 100)
        
        print(f"   Final scores: WO={wo_score:.1f}, Turnover={turnover_score:.1f}")
        
        # Determine classification
        if wo_score > turnover_score:
            doc_type = DocumentType.WORK_ORDER.value
            confidence = wo_score / 100
            reasoning = self._build_reasoning("WORK_ORDER", wo_hints, wo_matches, page_types)
        elif turnover_score > wo_score:
            doc_type = DocumentType.TURNOVER.value
            confidence = turnover_score / 100
            reasoning = self._build_reasoning("TURNOVER", turnover_hints, turnover_matches, page_types)
        else:
            # Tie
            if wo_hints >= turnover_hints:
                doc_type = DocumentType.WORK_ORDER.value
                confidence = 0.5
                reasoning = "Tie - defaulting to Work Order"
            else:
                doc_type = DocumentType.TURNOVER.value
                confidence = 0.5
                reasoning = "Tie - defaulting to Turnover"
        
        print(f"   ✓ Classification: {doc_type} (confidence: {confidence:.2f})")
        
        return {
            "document_type": doc_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "segment_pages": segment_pages,
            "scores": {
                "work_order": wo_score / 100,
                "turnover": turnover_score / 100
            }
        }
    
    def _build_reasoning(
        self,
        doc_type: str,
        hint_count: int,
        keyword_count: int,
        page_types: List[str]
    ) -> str:
        """Build human-readable reasoning"""
        reasons = []
        
        if hint_count > 0:
            reasons.append(f"Found {doc_type} hints in {hint_count} page(s)")
        
        if keyword_count > 0:
            reasons.append(f"{keyword_count} keyword matches")
        
        if 'CERTIFICATE' in page_types and doc_type == "WORK_ORDER":
            reasons.append("Contains certificate page")
        
        if not reasons:
            reasons.append(f"Pattern match for {doc_type}")
        
        return "; ".join(reasons)
    
    def classify_all_segments(
        self,
        document_boundaries: List[Tuple[int, int]],
        page_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Classify all document segments"""
        print(f"\n📊 Classifying {len(document_boundaries)} segment(s)...")
        
        results = []
        
        for i, (start, end) in enumerate(document_boundaries, start=1):
            segment_pages = list(range(start, end + 1))
            
            classification = self.classify_segment(segment_pages, page_analyses)
            classification['segment_id'] = i
            
            results.append(classification)
        
        # Summary
        print(f"\n✅ Classification complete!")
        type_counts = Counter(r['document_type'] for r in results)
        for doc_type, count in type_counts.items():
            print(f"   {doc_type}: {count} document(s)")
        
        return results