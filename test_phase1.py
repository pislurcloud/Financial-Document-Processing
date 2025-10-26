"""
Phase 1 Test Script: PDF Processing & Page Analysis
Tests PDF conversion and VLM-based page analysis
"""

import sys
from pathlib import Path
import json
import argparse

# Add current project to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.pdf_processor import prepare_pdf_for_analysis, PDFProcessor
from segmentation.page_analyzer import PageAnalyzer, save_analysis_results
from utils.vlm_provider import ModelManager


def test_phase1(pdf_path: str, max_pages: int = None):
    """
    Test Phase 1: PDF Processing & Page Analysis
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to analyze (None for all)
    """
    print("=" * 70)
    print("🚀 PHASE 1: PDF PROCESSING & PAGE ANALYSIS")
    print("=" * 70)
    print()
    
    # Step 1: Initialize VLM
    print("📌 Step 1: Initialize VLM Model Manager")
    print("-" * 70)
    model_manager = ModelManager(
        primary_model="openrouter_gemini",
        fallback_model="groq_llama_scout"
    )
    print()
    
    # Step 2: Prepare PDF
    print("📌 Step 2: Process PDF and Convert to Images")
    print("-" * 70)
    image_paths, page_count, metadata = prepare_pdf_for_analysis(pdf_path)
    
    # Limit pages if requested
    if max_pages and max_pages < len(image_paths):
        print(f"⚠️  Limiting analysis to first {max_pages} pages\n")
        image_paths = image_paths[:max_pages]
    
    print()
    
    # Step 3: Analyze pages
    print("📌 Step 3: VLM Page-by-Page Analysis")
    print("-" * 70)
    analyzer = PageAnalyzer(model_manager)
    analyses = analyzer.analyze_all_pages(image_paths)
    
    # Step 4: Detect boundaries
    print("📌 Step 4: Detect Document Boundaries")
    print("-" * 70)
    boundaries = analyzer.get_document_boundaries(analyses)
    
    print("\n🎯 Detected Document Segments:")
    for i, (start, end) in enumerate(boundaries, start=1):
        page_range = f"Page {start}" if start == end else f"Pages {start}-{end}"
        print(f"   Segment {i}: {page_range}")
    
    print()
    
    # Step 5: Summarize findings
    print("📌 Step 5: Analysis Summary")
    print("-" * 70)
    
    successful_analyses = [a for a in analyses if a.get('success')]
    
    # Count page types
    page_types = {}
    doc_type_hints = {}
    
    for analysis in successful_analyses:
        data = analysis['data']
        page_type = data.get('page_type', 'UNKNOWN')
        page_types[page_type] = page_types.get(page_type, 0) + 1
        
        for hint in data.get('document_type_hints', []):
            doc_type_hints[hint] = doc_type_hints.get(hint, 0) + 1
    
    print(f"\n📊 Page Type Distribution:")
    for ptype, count in sorted(page_types.items(), key=lambda x: x[1], reverse=True):
        print(f"   {ptype}: {count} pages")
    
    print(f"\n📋 Document Type Hints:")
    for dtype, count in sorted(doc_type_hints.items(), key=lambda x: x[1], reverse=True):
        print(f"   {dtype}: detected in {count} pages")
    
    # Step 6: Save results
    print("\n📌 Step 6: Save Analysis Results")
    print("-" * 70)
    
    output_dir = Path(pdf_path).parent / "analysis_results"
    output_dir.mkdir(exist_ok=True)
    
    # Save full analysis
    analysis_file = output_dir / "page_analyses.json"
    save_analysis_results(analyses, str(analysis_file))
    
    # Save summary
    summary = {
        "pdf_metadata": metadata,
        "total_pages_analyzed": len(analyses),
        "successful_analyses": len(successful_analyses),
        "detected_segments": len(boundaries),
        "document_boundaries": [
            {"segment": i, "start_page": start, "end_page": end, "page_count": end - start + 1}
            for i, (start, end) in enumerate(boundaries, start=1)
        ],
        "page_type_distribution": page_types,
        "document_type_hints": doc_type_hints
    }
    
    summary_file = output_dir / "analysis_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"💾 Summary saved to: {summary_file}")
    
    print()
    print("=" * 70)
    print("✅ PHASE 1 COMPLETE!")
    print("=" * 70)
    print()
    print(f"📁 Results saved in: {output_dir}")
    print(f"   - Full analysis: page_analyses.json")
    print(f"   - Summary: analysis_summary.json")
    print(f"   - Page images: {Path(pdf_path).parent / (Path(pdf_path).stem + '_pages')}")
    print()
    
    return analyses, boundaries, summary


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Phase 1: Test PDF processing and page analysis"
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
        test_phase1(args.pdf_path, args.max_pages)
        return 0
    except Exception as e:
        print(f"\n❌ Error during Phase 1 testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Default test with WO sample
    default_pdf = "/mnt/user-data/uploads/WOs_sample.pdf"
    
    if len(sys.argv) == 1 and Path(default_pdf).exists():
        print(f"📄 Using default test PDF: {default_pdf}\n")
        sys.exit(test_phase1(default_pdf, max_pages=5))  # Test first 5 pages
    else:
        sys.exit(main())
