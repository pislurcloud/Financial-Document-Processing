"""
Enhanced End-to-End Test
Tests hierarchical classification with sub-types and granular segmentation
"""

import sys
from pathlib import Path
import json
from datetime import datetime
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))

from utils.pdf_processor import prepare_pdf_for_analysis
from segmentation.page_analyzer import PageAnalyzer
from segmentation.subtype_detector import enhance_page_analysis_with_subtype
from segmentation.enhanced_segmentation import get_detailed_segments
from utils.vlm_provider import ModelManager
from config.document_types_enhanced import (
    requires_extraction, 
    get_subtype_priority,
    MainDocumentType
)


def test_enhanced_pipeline(pdf_path: str, max_pages: int = None):
    """
    Test enhanced pipeline with hierarchical classification
    
    Args:
        pdf_path: Path to PDF file
        max_pages: Maximum pages to analyze
    """
    print("=" * 80)
    print("🚀 ENHANCED END-TO-END TEST")
    print("   Phase 1: Segmentation")
    print("   Phase 2A: Hierarchical Classification (Main Type + Sub-Type)")
    print("=" * 80)
    print(f"📄 Document: {Path(pdf_path).name}")
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    # ========================================================================
    # PHASE 1: INITIAL ANALYSIS
    # ========================================================================
    
    print("=" * 80)
    print("PHASE 1: PDF PROCESSING & PAGE ANALYSIS")
    print("=" * 80)
    print()
    
    # Initialize VLM
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
        return False
    print()
    
    # Convert PDF
    print("📌 Step 1.2: Convert PDF to Images")
    print("-" * 80)
    try:
        image_paths, page_count, metadata = prepare_pdf_for_analysis(pdf_path)
        print(f"✅ Converted {page_count} pages")
        
        if max_pages and max_pages < len(image_paths):
            print(f"⚠️  Limiting to first {max_pages} pages")
            image_paths = image_paths[:max_pages]
            page_count = max_pages
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        return False
    print()
    
    # Analyze pages
    print("📌 Step 1.3: Analyze Pages with VLM")
    print("-" * 80)
    try:
        analyzer = PageAnalyzer(model_manager)
        page_analyses = analyzer.analyze_all_pages(image_paths)
        
        successful = sum(1 for a in page_analyses if a.get('success'))
        print(f"✅ Analyzed {successful}/{len(page_analyses)} pages")
    except Exception as e:
        print(f"❌ Page analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # ========================================================================
    # PHASE 2A: SUB-TYPE DETECTION & ENHANCED SEGMENTATION
    # ========================================================================
    
    print("=" * 80)
    print("PHASE 2A: HIERARCHICAL CLASSIFICATION")
    print("=" * 80)
    print()
    
    # Step 2.1: Detect sub-types for each page
    print("📌 Step 2.1: Detect Document Sub-Types")
    print("-" * 80)
    try:
        enhanced_analyses = []
        for analysis in page_analyses:
            enhanced = enhance_page_analysis_with_subtype(analysis, use_vlm=False)
            enhanced_analyses.append(enhanced)
        
        print("✅ Sub-type detection complete")
        print()
        print("   Page-by-Page Classification:")
        for i, analysis in enumerate(enhanced_analyses, 1):
            if analysis.get('success'):
                data = analysis['data']
                main = data.get('main_type', 'Unknown')
                sub = data.get('sub_type', 'Unknown')
                conf = data.get('sub_type_confidence', 0.0)
                print(f"   Page {i}: {main} → {sub} (conf: {conf:.2f})")
    except Exception as e:
        print(f"❌ Sub-type detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # Step 2.2: Create homogeneous segments
    print("📌 Step 2.2: Create Homogeneous Segments")
    print("-" * 80)
    try:
        segments = get_detailed_segments(enhanced_analyses, merge_low_confidence=True)
        print(f"✅ Created {len(segments)} homogeneous segment(s)")
    except Exception as e:
        print(f"❌ Segmentation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    print()
    
    # ========================================================================
    # RESULTS
    # ========================================================================
    
    print("=" * 80)
    print("📊 HIERARCHICAL CLASSIFICATION RESULTS")
    print("=" * 80)
    print()
    
    for segment in segments:
        seg_id = segment['segment_id']
        start = segment['start_page']
        end = segment['end_page']
        main_type = segment['main_type']
        sub_type = segment['sub_type']
        confidence = segment['confidence']
        pages = segment['pages']
        
        print(f"🔖 Segment {seg_id}")
        print(f"   Pages: {start}-{end} ({len(pages)} page(s))")
        print(f"   Main Type: {main_type}")
        print(f"   Sub-Type: {sub_type}")
        print(f"   Confidence: {confidence:.1%}")
        
        # Check if requires extraction
        needs_extraction = requires_extraction(
            MainDocumentType(main_type) if main_type != 'UNKNOWN' else None,
            sub_type
        )
        
        if needs_extraction:
            priority = get_subtype_priority(
                MainDocumentType(main_type) if main_type != 'UNKNOWN' else None,
                sub_type
            )
            print(f"   ⭐ EXTRACTION REQUIRED (Priority {priority})")
        else:
            print(f"   ℹ️  No extraction needed")
        
        # Confidence indicator
        if confidence >= 0.8:
            indicator = "✅ High confidence"
        elif confidence >= 0.6:
            indicator = "✓ Good confidence"
        elif confidence >= 0.4:
            indicator = "⚠️  Fair confidence"
        else:
            indicator = "❌ Low confidence - review needed"
        
        print(f"   {indicator}")
        print()
    
    # ========================================================================
    # SAVE RESULTS
    # ========================================================================
    
    print("=" * 80)
    print("💾 SAVE RESULTS")
    print("=" * 80)
    print()
    
    output_dir = Path(pdf_path).parent / "analysis_results_enhanced"
    output_dir.mkdir(exist_ok=True)
    
    # Save enhanced page analyses
    page_analyses_file = output_dir / "page_analyses_enhanced.json"
    with open(page_analyses_file, 'w') as f:
        json.dump(enhanced_analyses, f, indent=2)
    print(f"✅ Enhanced page analyses: {page_analyses_file}")
    
    # Save segments
    segments_file = output_dir / "segments_hierarchical.json"
    with open(segments_file, 'w') as f:
        json.dump(segments, f, indent=2)
    print(f"✅ Hierarchical segments: {segments_file}")
    
    # Save complete summary
    summary = {
        "pdf_name": Path(pdf_path).name,
        "processed_date": datetime.now().isoformat(),
        "total_pages": page_count,
        "total_segments": len(segments),
        "segments": segments,
        "extraction_summary": {
            "segments_needing_extraction": sum(
                1 for s in segments 
                if requires_extraction(
                    MainDocumentType(s['main_type']) if s['main_type'] != 'UNKNOWN' else None,
                    s['sub_type']
                )
            ),
            "total_segments": len(segments)
        }
    }
    
    summary_file = output_dir / "enhanced_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Complete summary: {summary_file}")
    print()
    
    # ========================================================================
    # SUMMARY STATISTICS
    # ========================================================================
    
    print("=" * 80)
    print("📈 PIPELINE SUMMARY")
    print("=" * 80)
    print()
    
    # Count by main type
    main_type_counts = Counter(s['main_type'] for s in segments)
    print("📊 Main Types:")
    for main_type, count in sorted(main_type_counts.items()):
        print(f"   {main_type}: {count} segment(s)")
    print()
    
    # Count by sub-type
    subtype_counts = Counter(f"{s['main_type']} → {s['sub_type']}" for s in segments)
    print("📊 Sub-Types:")
    for subtype, count in sorted(subtype_counts.items()):
        print(f"   {subtype}: {count} segment(s)")
    print()
    
    # Average confidence
    avg_conf = sum(s['confidence'] for s in segments) / len(segments)
    print(f"🎯 Average Confidence: {avg_conf:.1%}")
    print()
    
    # Extraction needs
    extraction_segments = [
        s for s in segments 
        if requires_extraction(
            MainDocumentType(s['main_type']) if s['main_type'] != 'UNKNOWN' else None,
            s['sub_type']
        )
    ]
    
    print(f"⭐ Segments Requiring Extraction: {len(extraction_segments)}/{len(segments)}")
    if extraction_segments:
        print("   Extraction Targets:")
        for s in extraction_segments:
            priority = get_subtype_priority(
                MainDocumentType(s['main_type']) if s['main_type'] != 'UNKNOWN' else None,
                s['sub_type']
            )
            print(f"   - Segment {s['segment_id']}: {s['sub_type']} (Priority {priority})")
    print()
    
    # Quality distribution
    excellent = sum(1 for s in segments if s['confidence'] >= 0.8)
    good = sum(1 for s in segments if 0.6 <= s['confidence'] < 0.8)
    fair = sum(1 for s in segments if 0.4 <= s['confidence'] < 0.6)
    low = sum(1 for s in segments if s['confidence'] < 0.4)
    
    print("📊 Quality Distribution:")
    print(f"   ✅ Excellent (≥80%): {excellent}")
    print(f"   ✓  Good (60-79%): {good}")
    print(f"   ⚠️  Fair (40-59%): {fair}")
    print(f"   ❌ Low (<40%): {low}")
    print()
    
    # Overall assessment
    if avg_conf >= 0.6 and low == 0:
        status = "✅ PASS"
        ready = True
        print(f"🎉 {status} - Enhanced pipeline working well!")
        print("✅ Ready for Phase 2B (Field Extraction)")
    elif avg_conf >= 0.4:
        status = "⚠️  WARN"
        ready = False
        print(f"⚠️  {status} - Pipeline working but needs improvement")
        print("💡 Some segments need better classification")
    else:
        status = "❌ FAIL"
        ready = False
        print(f"❌ {status} - Classification confidence too low")
        print("💡 Review sub-type detection logic")
    
    print()
    print("=" * 80)
    print(f"⏰ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()
    
    return ready


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test enhanced hierarchical classification"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to PDF file"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to analyze"
    )
    
    args = parser.parse_args()
    
    if not Path(args.pdf_path).exists():
        print(f"❌ PDF not found: {args.pdf_path}")
        return 1
    
    try:
        ready = test_enhanced_pipeline(args.pdf_path, args.max_pages)
        return 0 if ready else 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())