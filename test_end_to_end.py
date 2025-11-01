"""
End-to-End Test: Phase 1 + Phase 2A Combined
Tests complete pipeline: PDF → Segmentation → Classification
"""

import sys
from pathlib import Path
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from utils.pdf_processor import prepare_pdf_for_analysis
from segmentation.page_analyzer import PageAnalyzer
from segmentation.classifier_fixed import FixedClassifier
from utils.vlm_provider import ModelManager


def test_end_to_end(pdf_path: str, max_pages: int = None):
    """
    Test complete pipeline on a new document
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to analyze (None for all)
    """
    print("=" * 80)
    print("🚀 END-TO-END TEST: PHASE 1 + PHASE 2A")
    print("=" * 80)
    print(f"📄 Document: {Path(pdf_path).name}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # ========================================================================
    # PHASE 1: SEGMENTATION
    # ========================================================================
    
    print("=" * 80)
    print("PHASE 1: PDF PROCESSING & DOCUMENT SEGMENTATION")
    print("=" * 80)
    print()
    
    # Step 1.1: Initialize VLM
    print("📌 Step 1.1: Initialize VLM")
    print("-" * 80)
    try:
        model_manager = ModelManager(
            primary_model="openrouter_gemini",
            fallback_model="groq_llama_scout"
        )
        print("✅ VLM initialized")
    except Exception as e:
        print(f"❌ VLM initialization failed: {e}")
        print()
        print("💡 Make sure your .env file has:")
        print("   OPENROUTER_API_KEY=sk-or-v1-...")
        print("   GROQ_API_KEY=gsk_...")
        return False
    print()
    
    # Step 1.2: Convert PDF to images
    print("📌 Step 1.2: Convert PDF to Images")
    print("-" * 80)
    try:
        image_paths, page_count, metadata = prepare_pdf_for_analysis(pdf_path)
        print(f"✅ Converted {page_count} pages to images")
        
        if max_pages and max_pages < len(image_paths):
            print(f"⚠️  Limiting analysis to first {max_pages} pages")
            image_paths = image_paths[:max_pages]
            page_count = max_pages
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        return False
    print()
    
    # Step 1.3: Analyze pages with VLM
    print("📌 Step 1.3: Analyze Pages with VLM")
    print("-" * 80)
    try:
        analyzer = PageAnalyzer(model_manager)
        page_analyses = analyzer.analyze_all_pages(image_paths)
        
        successful = sum(1 for a in page_analyses if a.get('success'))
        print(f"✅ Analyzed {successful}/{len(page_analyses)} pages successfully")
    except Exception as e:
        print(f"❌ Page analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # Step 1.4: Detect document boundaries
    print("📌 Step 1.4: Detect Document Boundaries")
    print("-" * 80)
    try:
        boundaries = analyzer.get_document_boundaries(page_analyses)
        print(f"✅ Detected {len(boundaries)} document segment(s):")
        for i, (start, end) in enumerate(boundaries, 1):
            pages_in_segment = end - start + 1
            print(f"   Segment {i}: Pages {start}-{end} ({pages_in_segment} page(s))")
    except Exception as e:
        print(f"❌ Boundary detection failed: {e}")
        return False
    print()
    
    print("✅ PHASE 1 COMPLETE")
    print()
    
    # ========================================================================
    # PHASE 2A: CLASSIFICATION
    # ========================================================================
    
    print("=" * 80)
    print("PHASE 2A: DOCUMENT CLASSIFICATION")
    print("=" * 80)
    print()
    
    # Step 2.1: Classify segments with fixed classifier
    print("📌 Step 2.1: Classify Document Segments")
    print("-" * 80)
    try:
        classifier = FixedClassifier()
        classifications = classifier.classify_all_segments(boundaries, page_analyses)
        print(f"✅ Classified {len(classifications)} segment(s)")
    except Exception as e:
        print(f"❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # ========================================================================
    # RESULTS
    # ========================================================================
    
    print("=" * 80)
    print("📊 CLASSIFICATION RESULTS")
    print("=" * 80)
    print()
    
    for result in classifications:
        print(f"🔖 Segment {result['segment_id']}")
        print(f"   Pages: {result['segment_pages'][0]}-{result['segment_pages'][-1]}")
        print(f"   Document Type: {result['document_type'].upper()}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Reasoning: {result['reasoning']}")
        
        if 'scores' in result:
            wo_score = result['scores']['work_order']
            turn_score = result['scores']['turnover']
            print(f"   Scores: Work Order={wo_score:.2f}, Turnover={turn_score:.2f}")
        
        # Confidence indicator
        if result['confidence'] >= 0.9:
            indicator = "✅ Excellent - High confidence"
            status = "PASS"
        elif result['confidence'] >= 0.7:
            indicator = "✓ Good - Acceptable confidence"
            status = "PASS"
        elif result['confidence'] >= 0.5:
            indicator = "⚠️  Fair - Review recommended"
            status = "WARN"
        else:
            indicator = "❌ Low - Manual review required"
            status = "FAIL"
        
        print(f"   Status: {indicator}")
        print()
    
    # ========================================================================
    # SAVE RESULTS
    # ========================================================================
    
    print("=" * 80)
    print("💾 SAVE RESULTS")
    print("=" * 80)
    print()
    
    # Create output directory
    output_dir = Path(pdf_path).parent / "analysis_results"
    output_dir.mkdir(exist_ok=True)
    
    # Save page analyses
    page_analyses_file = output_dir / "page_analyses.json"
    with open(page_analyses_file, 'w') as f:
        json.dump(page_analyses, f, indent=2)
    print(f"✅ Page analyses saved: {page_analyses_file}")
    
    # Save classifications
    classifications_file = output_dir / "classifications.json"
    with open(classifications_file, 'w') as f:
        json.dump(classifications, f, indent=2)
    print(f"✅ Classifications saved: {classifications_file}")
    
    # Save complete summary
    summary = {
        "pdf_name": Path(pdf_path).name,
        "processed_date": datetime.now().isoformat(),
        "total_pages": page_count,
        "pages_analyzed": len(page_analyses),
        "segments_detected": len(boundaries),
        "document_boundaries": [
            {
                "segment": i,
                "start_page": start,
                "end_page": end,
                "page_count": end - start + 1
            }
            for i, (start, end) in enumerate(boundaries, 1)
        ],
        "classifications": classifications
    }
    
    summary_file = output_dir / "end_to_end_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Complete summary saved: {summary_file}")
    print()
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    print("=" * 80)
    print("📈 PIPELINE SUMMARY")
    print("=" * 80)
    print()
    
    from collections import Counter
    
    # Count document types
    type_counts = Counter(r['document_type'] for r in classifications)
    print("📊 Documents Classified:")
    for doc_type, count in sorted(type_counts.items()):
        print(f"   {doc_type.upper()}: {count} document(s)")
    print()
    
    # Calculate average confidence
    avg_confidence = sum(r['confidence'] for r in classifications) / len(classifications)
    print(f"🎯 Average Confidence: {avg_confidence:.1%}")
    
    # Count by quality
    excellent = sum(1 for r in classifications if r['confidence'] >= 0.9)
    good = sum(1 for r in classifications if 0.7 <= r['confidence'] < 0.9)
    fair = sum(1 for r in classifications if 0.5 <= r['confidence'] < 0.7)
    low = sum(1 for r in classifications if r['confidence'] < 0.5)
    
    print(f"📊 Quality Distribution:")
    print(f"   ✅ Excellent (≥90%): {excellent}")
    print(f"   ✓  Good (70-89%): {good}")
    print(f"   ⚠️  Fair (50-69%): {fair}")
    print(f"   ❌ Low (<50%): {low}")
    print()
    
    # Overall assessment
    if avg_confidence >= 0.7 and low == 0:
        overall_status = "✅ PASS - Pipeline working well!"
        ready_for_phase2b = True
        print("🎉 " + overall_status)
        print("✅ Ready to proceed to Phase 2B (Field Extraction)")
    elif avg_confidence >= 0.5:
        overall_status = "⚠️  WARN - Pipeline working but needs improvement"
        ready_for_phase2b = False
        print("⚠️  " + overall_status)
        print("💡 Some documents need better classification")
        print("💡 Consider using VLM-based classifier for low-confidence segments")
    else:
        overall_status = "❌ FAIL - Pipeline not working reliably"
        ready_for_phase2b = False
        print("❌ " + overall_status)
        print("💡 Classification confidence too low")
        print("💡 Switch to VLM-based classifier or debug further")
    
    print()
    print("=" * 80)
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    return ready_for_phase2b


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="End-to-end test: Phase 1 + Phase 2A"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to PDF file to test"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to analyze (default: all)"
    )
    
    args = parser.parse_args()
    
    # Validate PDF exists
    if not Path(args.pdf_path).exists():
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        return 1
    
    try:
        ready = test_end_to_end(args.pdf_path, args.max_pages)
        return 0 if ready else 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())