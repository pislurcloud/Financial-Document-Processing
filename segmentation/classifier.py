"""
Document Classifier
Classifies document segments as Work Order or Turnover
"""

from typing import Dict, Any, List, Tuple
from collections import Counter
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.document_types import DocumentType


class DocumentClassifier:
    """Classifies document segments based on page analyses"""
    
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
        
        # Page types that suggest Work Order
        self.wo_page_types = ["CERTIFICATE", "DATA_PAGE"]
        
        # Page types that suggest Turnover
        self.turnover_page_types = ["DATA_PAGE"]
    
    def classify_segment(
        self,
        segment_pages: List[int],
        page_analyses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Classify a document segment
        
        Args:
            segment_pages: List of page numbers in this segment (1-indexed)
            page_analyses: List of all page analysis results from Phase 1
            
        Returns:
            Classification result with type, confidence, and reasoning
        """
        print(f"\n🔍 Classifying segment: Pages {segment_pages[0]}-{segment_pages[-1]}")
        
        # Get analyses for pages in this segment
        segment_analyses = []
        for page_num in segment_pages:
            for analysis in page_analyses:
                if analysis.get('success') and analysis.get('page_number') == page_num:
                    segment_analyses.append(analysis['data'])
                    break
        
        if not segment_analyses:
            return {
                "document_type": DocumentType.UNKNOWN.value,
                "confidence": 0.0,
                "reasoning": "No valid page analyses available",
                "segment_pages": segment_pages,
                "scores": {
                    "work_order": 0.0,
                    "turnover": 0.0
                }
            }
        
        # Score based on multiple factors
        wo_score = 0
        turnover_score = 0
        
        # Factor 1: Document type hints from Phase 1
        wo_hints = 0
        turnover_hints = 0
        
        for analysis in segment_analyses:
            hints = analysis.get('document_type_hints', [])
            if 'WORK_ORDER' in hints:
                wo_hints += 1
            if 'TURNOVER' in hints:
                turnover_hints += 1
        
        print(f"   Type hints: WO={wo_hints}, Turnover={turnover_hints} (out of {len(segment_analyses)} pages)")
        
        # Weight: 40%
        wo_score += (wo_hints / len(segment_analyses)) * 40
        turnover_score += (turnover_hints / len(segment_analyses)) * 40
        
        # Factor 2: Keyword matching in text snippets
        wo_keyword_matches = 0
        turnover_keyword_matches = 0
        
        all_text = []
        for analysis in segment_analyses:
            snippets = analysis.get('key_text_snippets', [])
            all_text.extend([s.lower() for s in snippets])
        
        combined_text = ' '.join(all_text)
        
        for keyword in self.wo_keywords:
            if keyword in combined_text:
                wo_keyword_matches += 1
        
        for keyword in self.turnover_keywords:
            if keyword in combined_text:
                turnover_keyword_matches += 1
        
        print(f"   Keyword matches: WO={wo_keyword_matches}, Turnover={turnover_keyword_matches}")
        
        # Weight: 30%
        total_keywords = max(wo_keyword_matches + turnover_keyword_matches, 1)
        wo_score += (wo_keyword_matches / total_keywords) * 30
        turnover_score += (turnover_keyword_matches / total_keywords) * 30
        
        # Factor 3: Page types
        page_types = [a.get('page_type') for a in segment_analyses]
        
        # Weight: 20%
        if 'CERTIFICATE' in page_types:
            wo_score += 20
        
        # Check for financial keywords in text
        combined_text_lower = combined_text.lower()
        if 'financial' in combined_text_lower or 'balance' in combined_text_lower or 'profit and loss' in combined_text_lower:
            turnover_score += 20
        
        # Factor 4: Document structure indicators
        has_tables = any(a.get('data_assessment', {}).get('has_tables') for a in segment_analyses)
        has_forms = any(a.get('data_assessment', {}).get('has_forms') for a in segment_analyses)
        
        # Weight: 10%
        if has_tables:
            wo_score += 5
            turnover_score += 5  # Both can have tables
        if has_forms:
            wo_score += 5
        
        # Normalize scores to 0-100
        wo_score = min(wo_score, 100)
        turnover_score = min(turnover_score, 100)
        
        print(f"   Final scores: WO={wo_score:.1f}, Turnover={turnover_score:.1f}")
        
        # Determine classification
        if wo_score > turnover_score:
            doc_type = DocumentType.WORK_ORDER.value
            confidence = wo_score / 100
            reasoning = self._build_reasoning("WORK_ORDER", wo_hints, wo_keyword_matches, page_types)
        elif turnover_score > wo_score:
            doc_type = DocumentType.TURNOVER.value
            confidence = turnover_score / 100
            reasoning = self._build_reasoning("TURNOVER", turnover_hints, turnover_keyword_matches, page_types)
        else:
            # Tie - use hints as tiebreaker
            if wo_hints >= turnover_hints:
                doc_type = DocumentType.WORK_ORDER.value
                confidence = 0.5
                reasoning = "Tie - defaulting to Work Order based on hints"
            else:
                doc_type = DocumentType.TURNOVER.value
                confidence = 0.5
                reasoning = "Tie - defaulting to Turnover based on hints"
        
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
        """Build human-readable reasoning for classification"""
        reasons = []
        
        if hint_count > 0:
            reasons.append(f"Found {doc_type} hints in {hint_count} page(s)")
        
        if keyword_count > 0:
            reasons.append(f"{keyword_count} keyword matches")
        
        if 'CERTIFICATE' in page_types and doc_type == "WORK_ORDER":
            reasons.append("Contains certificate page")
        
        if not reasons:
            reasons.append(f"Pattern match for {doc_type} document structure")
        
        return "; ".join(reasons)
    
    def classify_all_segments(
        self,
        document_boundaries: List[Tuple[int, int]],
        page_analyses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Classify all document segments
        
        Args:
            document_boundaries: List of (start_page, end_page) tuples
            page_analyses: All page analysis results from Phase 1
            
        Returns:
            List of classification results
        """
        print(f"\n📊 Classifying {len(document_boundaries)} document segment(s)...")
        
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


# Test function
def test_classifier():
    """Test classifier with sample data"""
    import json
    
    # Load Phase 1 results
    results_path = "/mnt/user-data/outputs/commercial-doc-processor/analysis_results/page_analyses.json"
    
    if not Path(results_path).exists():
        print("❌ No Phase 1 results found. Run test_phase1.py first.")
        return
    
    with open(results_path) as f:
        page_analyses = json.load(f)
    
    # Load boundaries
    summary_path = "/mnt/user-data/outputs/commercial-doc-processor/analysis_results/analysis_summary.json"
    with open(summary_path) as f:
        summary = json.load(f)
    
    boundaries = [(b['start_page'], b['end_page']) for b in summary['document_boundaries']]
    
    # Classify
    classifier = DocumentClassifier()
    classifications = classifier.classify_all_segments(boundaries, page_analyses)
    
    # Display results
    print("\n" + "=" * 70)
    print("CLASSIFICATION RESULTS")
    print("=" * 70)
    
    for result in classifications:
        print(f"\nSegment {result['segment_id']}: Pages {result['segment_pages'][0]}-{result['segment_pages'][-1]}")
        print(f"  Type: {result['document_type']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Reasoning: {result['reasoning']}")
        print(f"  Scores: WO={result['scores']['work_order']:.2f}, Turnover={result['scores']['turnover']:.2f}")
    
    # Save results
    output_path = "/mnt/user-data/outputs/commercial-doc-processor/analysis_results/classifications.json"
    with open(output_path, 'w') as f:
        json.dump(classifications, f, indent=2)
    
    print(f"\n💾 Classifications saved to: {output_path}")


if __name__ == "__main__":
    test_classifier()