"""
Phase 2A Test Script: Document Classification
Tests the document classifier on sample documents
"""

import sys
from pathlib import Path
import json

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.pdf_processor import prepare_pdf_for_analysis
from segmentation.page_analyzer import PageAnalyzer
from segmentation.classifier import DocumentClassifier
from utils.vlm_provider import ModelManager


def test_phase2a(pdf_path: str, max_pages: int = None):
    """
    Test Phase 2A: Classification
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to analyze (None for all)
    """
    print("=" * 70)
    print("🚀 PHASE 2A: DOCUMENT CLASSIFICATION TEST")
    print("=" * 70)
    print()
    
    # Step 1: Run Phase 1 if needed
    print("📌 Step 1: PDF Processing & Page Analysis (Phase 1)")
    print("-" * 70)
    
    # Initialize VLM
    model_manager = ModelManager(
        primary_model="openrouter_gemini",
        fallback_model="groq_llama_scout"
    )
    
    # Prepare PDF
    image_paths, page_count, metadata = prepare_pdf_for_analysis(pdf_path)
    
    # Limit pages if requested
    if max_pages and max_pages < len(image_paths):
        print(f"⚠️  Limiting analysis to first {max_pages} pages\n")
        image_paths = image_paths[:max_pages]
    
    # Analyze pages
    analyzer = PageAnalyzer(model_manager)
    analyses = analyzer.analyze_all_pages(image_paths)
    
    # Detect boundaries
    boundaries = analyzer.get_document_boundaries(analyses)
    
    print(f"\n✅ Phase 1 complete: {len(boundaries)} segment(s) detected")
    print()
    
    # Step 2: Classify segments
    print("📌 Step 2: Document Classification (Phase 2A)")
    print("-" * 70)
    
    classifier = DocumentClassifier()
    classifications = classifier.classify_all_segments(boundaries, analyses)
    
    # Step 3: Display detailed results
    print("\n" + "=" * 70)
    print("📊 CLASSIFICATION RESULTS")
    print("=" * 70)
    
    for result in classifications:
        print(f"\n🔖 Segment {result['segment_id']}")
        print(f"   Pages: {result['segment_pages'][0]}-{result['segment_pages'][-1]}")
        print(f"   Type: {result['document_type']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Reasoning: {result['reasoning']}")
        
        # Show scores if available
        if 'scores' in result:
            wo_score = result['scores']['work_order']
            turn_score = result['scores']['turnover']
            print(f"   Scores: Work Order={wo_score:.2f}, Turnover={turn_score:.2f}")
        else:
            print(f"   ⚠️  Scores not available")
        
        # Confidence indicator
        if result['confidence'] >= 0.9:
            indicator = "✅ High confidence"
        elif result['confidence'] >= 0.7:
            indicator = "✓ Medium confidence"
        else:
            indicator = "⚠️  Low confidence - needs review"
        print(f"   {indicator}")
    
    # Step 4: Save results
    print("\n📌 Step 3: Save Results")
    print("-" * 70)
    
    output_dir = Path(pdf_path).parent / "analysis_results"
    output_dir.mkdir(exist_ok=True)
    
    # Save classifications
    classifications_file = output_dir / "phase2a_classifications.json"
    with open(classifications_file, 'w') as f:
        json.dump(classifications, f, indent=2)
    print(f"💾 Classifications saved: {classifications_file}")
    
    # Save complete Phase 2A results
    phase2a_results = {
        "pdf_name": Path(pdf_path).name,
        "total_pages": page_count,
        "pages_analyzed": len(analyses),
        "segments_detected": len(boundaries),
        "document_boundaries": [
            {"segment": i, "start_page": start, "end_page": end}
            for i, (start, end) in enumerate(boundaries, 1)
        ],
        "classifications": classifications
    }
    
    results_file = output_dir / "phase2a_complete_results.json"
    with open(results_file, 'w') as f:
        json.dump(phase2a_results, f, indent=2)
    print(f"💾 Complete results saved: {results_file}")
    
    print()
    print("=" * 70)
    print("✅ PHASE 2A COMPLETE!")
    print("=" * 70)
    print()
    
    # Summary
    type_counts = {}
    for result in classifications:
        doc_type = result['document_type']
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    
    print("📈 Summary:")
    for doc_type, count in type_counts.items():
        print(f"   {doc_type}: {count} document(s)")
    
    avg_confidence = sum(r['confidence'] for r in classifications) / len(classifications)
    print(f"   Average Confidence: {avg_confidence:.1%}")
    
    needs_review = sum(1 for r in classifications if r['confidence'] < 0.7)
    if needs_review > 0:
        print(f"   ⚠️  {needs_review} document(s) need human review")
    
    print()
    print("🎯 Next Step: Phase 2B - Field Extraction")
    print()
    
    return classifications


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Phase 2A: Test document classification"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to PDF file"
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
        test_phase2a(args.pdf_path, args.max_pages)
        return 0
    except Exception as e:
        print(f"\n❌ Error during Phase 2A testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Default test with samples
    import os
    
    if len(sys.argv) == 1:
        # Test with both sample documents
        samples = [
            ("/mnt/user-data/uploads/WOs_sample.pdf", 5),  # First 5 pages
            ("/mnt/user-data/uploads/turnover__2_.pdf", None)  # All pages
        ]
        
        for pdf_path, max_pages in samples:
            if Path(pdf_path).exists():
                print(f"\n{'='*70}")
                print(f"Testing with: {Path(pdf_path).name}")
                print(f"{'='*70}\n")
                test_phase2a(pdf_path, max_pages)
                print("\n\n")
        
        sys.exit(0)
    else:
        sys.exit(main())