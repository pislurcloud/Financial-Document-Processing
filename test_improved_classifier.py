"""
Improved Document Classifier - VLM-Based Approach
Uses VLM directly on document segments for more robust classification
"""

from typing import Dict, Any, List, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vlm_provider import ModelManager, extract_json_from_response
from config.document_types import DocumentType


# Direct classification prompt for VLM
SEGMENT_CLASSIFICATION_PROMPT = """You are analyzing a multi-page document segment to classify it.

**Your Task:**
Classify this document as either WORK_ORDER or TURNOVER based on the content.

**WORK_ORDER characteristics:**
- Purchase orders, job orders, work orders
- Contains order numbers (PO#, WO#, Order No)
- Lists items, quantities, rates, amounts
- Has vendor/supplier and client/buyer information
- May include invoices, delivery notes, completion certificates
- Keywords: "purchase order", "work order", "vendor", "supplier", "order no", "invoice", "delivery", "GSTIN", "items", "quantity"

**TURNOVER characteristics:**
- Financial statements, P&L statements, Balance Sheets
- Contains revenue figures, income statements
- Shows financial periods (FY, year ending)
- Has shareholders' information, equity details
- Keywords: "turnover", "revenue from operations", "profit and loss", "balance sheet", "financial statement", "shareholders", "fiscal year", "income", "expenses"

**Instructions:**
1. Look at the overall structure and content
2. Identify key indicators
3. Classify as WORK_ORDER or TURNOVER
4. Provide confidence score (0.0-1.0)
5. Explain your reasoning

**Respond ONLY with valid JSON:**
{{
    "document_type": "WORK_ORDER or TURNOVER",
    "confidence": 0.0-1.0,
    "reasoning": "explain why you classified it this way",
    "key_indicators": ["list", "of", "key", "factors"]
}}

**Context:**
This is page {page_number} of {total_pages} in this document segment.
"""


class ImprovedClassifier:
    """VLM-based classifier that directly analyzes document segments"""
    
    def __init__(self, model_manager: ModelManager):
        """
        Initialize classifier with VLM
        
        Args:
            model_manager: VLM model manager instance
        """
        self.model_manager = model_manager
    
    def classify_segment_with_vlm(
        self,
        image_paths: List[str],
        segment_pages: List[int]
    ) -> Dict[str, Any]:
        """
        Classify a document segment using VLM
        
        Args:
            image_paths: List of page image paths for this segment
            segment_pages: Page numbers in this segment
            
        Returns:
            Classification result
        """
        print(f"\n🔍 Classifying segment: Pages {segment_pages[0]}-{segment_pages[-1]} with VLM")
        
        # Strategy: Analyze key pages (first, middle, last)
        pages_to_analyze = []
        
        if len(image_paths) == 1:
            pages_to_analyze = [0]
        elif len(image_paths) == 2:
            pages_to_analyze = [0, 1]
        else:
            # Analyze first, middle, and last pages
            middle = len(image_paths) // 2
            pages_to_analyze = [0, middle, len(image_paths) - 1]
        
        print(f"   Analyzing {len(pages_to_analyze)} representative page(s)")
        
        # Collect classifications from each page
        page_classifications = []
        
        for idx in pages_to_analyze:
            if idx >= len(image_paths):
                continue
            
            image_path = image_paths[idx]
            page_num = segment_pages[idx]
            
            prompt = SEGMENT_CLASSIFICATION_PROMPT.format(
                page_number=page_num,
                total_pages=len(segment_pages)
            )
            
            print(f"   Analyzing page {page_num}...")
            
            result = self.model_manager.analyze_image_with_fallback(image_path, prompt)
            
            if result['success']:
                try:
                    classification = extract_json_from_response(result['response'])
                    page_classifications.append(classification)
                    print(f"      → {classification.get('document_type')} (conf: {classification.get('confidence', 0):.2f})")
                except Exception as e:
                    print(f"      ⚠️  Failed to parse: {e}")
            else:
                print(f"      ❌ VLM failed: {result.get('error')}")
        
        if not page_classifications:
            return {
                "document_type": DocumentType.UNKNOWN.value,
                "confidence": 0.0,
                "reasoning": "VLM classification failed for all pages",
                "segment_pages": segment_pages,
                "scores": {
                    "work_order": 0.0,
                    "turnover": 0.0
                }
            }
        
        # Aggregate results
        wo_votes = sum(1 for c in page_classifications if c.get('document_type') == 'WORK_ORDER')
        turnover_votes = sum(1 for c in page_classifications if c.get('document_type') == 'TURNOVER')
        
        # Determine final classification
        if wo_votes > turnover_votes:
            doc_type = DocumentType.WORK_ORDER.value
            # Average confidence from WO classifications
            wo_confs = [c.get('confidence', 0) for c in page_classifications 
                       if c.get('document_type') == 'WORK_ORDER']
            confidence = sum(wo_confs) / len(wo_confs) if wo_confs else 0.5
        elif turnover_votes > wo_votes:
            doc_type = DocumentType.TURNOVER.value
            # Average confidence from Turnover classifications
            turn_confs = [c.get('confidence', 0) for c in page_classifications 
                         if c.get('document_type') == 'TURNOVER']
            confidence = sum(turn_confs) / len(turn_confs) if turn_confs else 0.5
        else:
            # Tie - use highest confidence
            wo_conf = max([c.get('confidence', 0) for c in page_classifications 
                          if c.get('document_type') == 'WORK_ORDER'], default=0)
            turn_conf = max([c.get('confidence', 0) for c in page_classifications 
                            if c.get('document_type') == 'TURNOVER'], default=0)
            
            if wo_conf >= turn_conf:
                doc_type = DocumentType.WORK_ORDER.value
                confidence = wo_conf
            else:
                doc_type = DocumentType.TURNOVER.value
                confidence = turn_conf
        
        # Collect reasoning
        reasoning_parts = [c.get('reasoning', '') for c in page_classifications if c.get('reasoning')]
        reasoning = "; ".join(reasoning_parts[:2])  # Use first 2 explanations
        
        print(f"   ✓ Final: {doc_type} (confidence: {confidence:.2f})")
        
        return {
            "document_type": doc_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "segment_pages": segment_pages,
            "scores": {
                "work_order": wo_votes / len(page_classifications),
                "turnover": turnover_votes / len(page_classifications)
            },
            "page_classifications": page_classifications  # Keep details
        }
    
    def classify_all_segments_with_vlm(
        self,
        document_boundaries: List[Tuple[int, int]],
        all_image_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Classify all segments using VLM
        
        Args:
            document_boundaries: List of (start_page, end_page) tuples (1-indexed)
            all_image_paths: All page images from PDF
            
        Returns:
            List of classification results
        """
        print(f"\n📊 Classifying {len(document_boundaries)} segment(s) with VLM...")
        
        results = []
        
        for i, (start, end) in enumerate(document_boundaries, start=1):
            # Get images for this segment (convert from 1-indexed to 0-indexed)
            segment_images = all_image_paths[start-1:end]
            segment_pages = list(range(start, end + 1))
            
            classification = self.classify_segment_with_vlm(segment_images, segment_pages)
            classification['segment_id'] = i
            
            results.append(classification)
        
        # Summary
        print(f"\n✅ VLM Classification complete!")
        from collections import Counter
        type_counts = Counter(r['document_type'] for r in results)
        for doc_type, count in type_counts.items():
            print(f"   {doc_type}: {count} document(s)")
        
        return results


# Hybrid approach: Use keyword-based first, VLM as fallback
class HybridClassifier:
    """Combines keyword-based and VLM-based classification"""
    
    def __init__(self, model_manager: ModelManager):
        self.keyword_classifier = None  # Will use the original classifier
        self.vlm_classifier = ImprovedClassifier(model_manager)
        self.model_manager = model_manager
    
    def classify_segment_hybrid(
        self,
        segment_pages: List[int],
        page_analyses: List[Dict[str, Any]],
        image_paths: List[str]
    ) -> Dict[str, Any]:
        """
        Try keyword-based classification first, use VLM if confidence is low
        
        Args:
            segment_pages: Page numbers in segment
            page_analyses: Phase 1 analyses
            image_paths: Page images for this segment
            
        Returns:
            Classification result
        """
        # First try keyword-based (if we have proper Phase 1 data)
        from segmentation.classifier import DocumentClassifier
        
        keyword_result = DocumentClassifier().classify_segment(segment_pages, page_analyses)
        
        # If confidence is good, use it
        if keyword_result['confidence'] >= 0.7:
            print(f"   ✓ Using keyword-based classification (conf: {keyword_result['confidence']:.2f})")
            return keyword_result
        
        # Otherwise, use VLM
        print(f"   ⚠️  Low keyword confidence ({keyword_result['confidence']:.2f}), using VLM...")
        vlm_result = self.vlm_classifier.classify_segment_with_vlm(image_paths, segment_pages)
        
        # Add note about fallback
        vlm_result['reasoning'] = f"VLM-based (keyword conf was low). {vlm_result['reasoning']}"
        
        return vlm_result