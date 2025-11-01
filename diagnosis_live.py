#!/usr/bin/env python3
"""
Live Classification Diagnostic
Run this to see EXACTLY why classification is failing on your documents
"""

import sys
import json
from pathlib import Path
from collections import Counter

def find_phase1_results():
    """Find Phase 1 results in common locations"""
    search_paths = [
        Path.cwd() / "analysis_results",
        Path("/mnt/user-data/uploads/analysis_results"),
        Path("/workspaces/Financial-Document-Processing/analysis_results"),
        Path.home() / "analysis_results"
    ]
    
    for path in search_paths:
        if path.exists():
            page_analyses = path / "page_analyses.json"
            summary = path / "analysis_summary.json"
            if page_analyses.exists() or summary.exists():
                return path
    
    return None

def analyze_phase1_output(results_dir):
    """Deep dive into Phase 1 results"""
    
    print("=" * 80)
    print("🔬 CLASSIFICATION DIAGNOSTIC - DEEP DIVE")
    print("=" * 80)
    print()
    
    # Load page analyses
    page_analyses_file = results_dir / "page_analyses.json"
    if not page_analyses_file.exists():
        print(f"❌ No page_analyses.json found in {results_dir}")
        return False
    
    with open(page_analyses_file) as f:
        page_analyses = json.load(f)
    
    print(f"📁 Results Directory: {results_dir}")
    print(f"📄 Total Pages Analyzed: {len(page_analyses)}")
    print()
    
    # Load summary if available
    summary_file = results_dir / "analysis_summary.json"
    boundaries = []
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
        boundaries = summary.get('document_boundaries', [])
        print(f"📊 Document Segments: {len(boundaries)}")
        for b in boundaries:
            print(f"   Segment {b.get('segment', '?')}: Pages {b['start_page']}-{b['end_page']}")
    print()
    
    # Analyze each page in detail
    print("=" * 80)
    print("PAGE-BY-PAGE ANALYSIS")
    print("=" * 80)
    print()
    
    issues_found = []
    
    for i, analysis in enumerate(page_analyses, 1):
        print(f"📄 PAGE {i}")
        print("-" * 80)
        
        # Check success
        if not analysis.get('success'):
            print("   ❌ ANALYSIS FAILED")
            if 'error' in analysis:
                print(f"   Error: {analysis['error']}")
            issues_found.append(f"Page {i}: Analysis failed")
            print()
            continue
        
        data = analysis.get('data', {})
        
        # 1. Check document_type_hints (CRITICAL for classifier)
        hints = data.get('document_type_hints', [])
        print(f"   🏷️  document_type_hints: ", end="")
        if hints:
            print(f"✅ {hints}")
        else:
            print("❌ MISSING/EMPTY (classifier needs this!)")
            issues_found.append(f"Page {i}: No document_type_hints")
        
        # 2. Check key_text_snippets (CRITICAL for classifier)
        snippets = data.get('key_text_snippets', [])
        print(f"   📝 key_text_snippets: ", end="")
        if snippets and len(snippets) > 0:
            print(f"✅ {len(snippets)} snippets")
            # Show first few
            for j, snippet in enumerate(snippets[:3], 1):
                print(f"      {j}. {snippet[:70]}...")
        else:
            print("❌ MISSING/EMPTY (classifier needs this!)")
            issues_found.append(f"Page {i}: No key_text_snippets")
        
        # 3. Check page_type
        page_type = data.get('page_type', 'MISSING')
        print(f"   📋 page_type: {page_type}")
        
        # 4. Check data_assessment
        assessment = data.get('data_assessment', {})
        if assessment:
            print(f"   📊 data_assessment:")
            print(f"      - has_tables: {assessment.get('has_tables', False)}")
            print(f"      - has_forms: {assessment.get('has_forms', False)}")
            print(f"      - data_density: {assessment.get('data_density', 'UNKNOWN')}")
        else:
            print(f"   📊 data_assessment: ⚠️  MISSING")
        
        # 5. Check VLM confidence
        confidence = data.get('confidence', 0.0)
        print(f"   🎯 VLM confidence: {confidence:.2f}")
        
        print()
    
    # Simulate classifier scoring
    print("=" * 80)
    print("CLASSIFIER SIMULATION")
    print("=" * 80)
    print()
    
    if not boundaries:
        print("⚠️  No boundaries found - cannot simulate classification")
        print()
    else:
        for boundary in boundaries:
            segment_id = boundary.get('segment', 1)
            start = boundary['start_page']
            end = boundary['end_page']
            
            print(f"🔖 SEGMENT {segment_id}: Pages {start}-{end}")
            print("-" * 80)
            
            # Get pages for this segment
            segment_pages = list(range(start, end + 1))
            segment_analyses = []
            
            for page_num in segment_pages:
                for analysis in page_analyses:
                    if analysis.get('page_number') == page_num and analysis.get('success'):
                        segment_analyses.append(analysis['data'])
                        break
            
            if not segment_analyses:
                print("   ❌ NO VALID ANALYSES - Classifier will return 0.0 confidence")
                print()
                continue
            
            print(f"   Pages with valid analyses: {len(segment_analyses)}/{len(segment_pages)}")
            
            # Simulate scoring
            # Factor 1: Type hints (40%)
            wo_hints = 0
            turnover_hints = 0
            for data in segment_analyses:
                hints = data.get('document_type_hints', [])
                if 'WORK_ORDER' in hints:
                    wo_hints += 1
                if 'TURNOVER' in hints:
                    turnover_hints += 1
            
            print(f"   Type hints: WO={wo_hints}, Turnover={turnover_hints}")
            
            if wo_hints == 0 and turnover_hints == 0:
                print("   ❌ NO TYPE HINTS - Classifier scores 0 for Factor 1 (40% weight)")
                issues_found.append(f"Segment {segment_id}: No type hints in any page")
            
            # Factor 2: Keyword matching (30%)
            all_snippets = []
            for data in segment_analyses:
                all_snippets.extend(data.get('key_text_snippets', []))
            
            if not all_snippets:
                print("   ❌ NO TEXT SNIPPETS - Classifier scores 0 for Factor 2 (30% weight)")
                issues_found.append(f"Segment {segment_id}: No text snippets")
            else:
                combined_text = ' '.join(all_snippets).lower()
                
                # Count keyword matches
                wo_keywords = ["work order", "purchase order", "po#", "wo#", "order no", 
                              "invoice", "vendor", "supplier", "gstin", "gst"]
                turnover_keywords = ["turnover", "revenue", "profit and loss", "p&l", 
                                    "balance sheet", "financial", "shareholders"]
                
                wo_matches = sum(1 for kw in wo_keywords if kw in combined_text)
                turn_matches = sum(1 for kw in turnover_keywords if kw in combined_text)
                
                print(f"   Keyword matches: WO={wo_matches}, Turnover={turn_matches}")
                
                if wo_matches == 0 and turn_matches == 0:
                    print("   ⚠️  NO KEYWORD MATCHES - May indicate generic text extraction")
            
            # Estimate final score
            hint_score = (wo_hints / len(segment_analyses) * 40) if wo_hints > 0 else (turnover_hints / len(segment_analyses) * 40)
            
            if not all_snippets:
                keyword_score = 0
            else:
                keyword_score = 30 if (wo_matches > 0 or turn_matches > 0) else 0
            
            estimated_score = hint_score + keyword_score
            
            print(f"   📊 Estimated Score: ~{estimated_score:.0f}/100")
            
            if estimated_score < 50:
                print(f"   ❌ LOW SCORE - Will result in low confidence classification")
            
            print()
    
    # Summary of issues
    print("=" * 80)
    print("🚨 ISSUES SUMMARY")
    print("=" * 80)
    print()
    
    if not issues_found:
        print("✅ No critical issues found!")
        print("   Data structure looks good for classification.")
    else:
        print(f"Found {len(issues_found)} issue(s):")
        for i, issue in enumerate(issues_found, 1):
            print(f"   {i}. {issue}")
    
    print()
    
    # Root cause analysis
    print("=" * 80)
    print("💡 ROOT CAUSE ANALYSIS")
    print("=" * 80)
    print()
    
    pages_without_hints = sum(1 for a in page_analyses 
                             if a.get('success') and not a.get('data', {}).get('document_type_hints'))
    pages_without_snippets = sum(1 for a in page_analyses 
                                 if a.get('success') and not a.get('data', {}).get('key_text_snippets'))
    
    if pages_without_hints > 0:
        print(f"🔴 CRITICAL: {pages_without_hints}/{len(page_analyses)} pages have NO document_type_hints")
        print("   This means:")
        print("   - Phase 1 VLM is not providing type hints")
        print("   - Classifier loses 40% of its scoring ability")
        print("   - Classification confidence will be very low")
        print()
    
    if pages_without_snippets > 0:
        print(f"🔴 CRITICAL: {pages_without_snippets}/{len(page_analyses)} pages have NO key_text_snippets")
        print("   This means:")
        print("   - Phase 1 VLM is not extracting text")
        print("   - Classifier loses 30% of its scoring ability (keyword matching)")
        print("   - Classification confidence will be very low")
        print()
    
    if pages_without_hints > 0 or pages_without_snippets > 0:
        print("=" * 80)
        print("🔧 RECOMMENDED FIXES")
        print("=" * 80)
        print()
        print("Option 1: Fix Phase 1 VLM Prompt")
        print("   - Ensure VLM response includes document_type_hints")
        print("   - Ensure VLM response includes key_text_snippets")
        print("   - Check VLM response parsing logic")
        print()
        print("Option 2: Use Improved VLM-Based Classifier")
        print("   - Bypass Phase 1 intermediate data")
        print("   - Ask VLM directly to classify segments")
        print("   - More robust and reliable")
        print("   - Run: python test_improved_classifier.py /path/to/pdf")
        print()
        print("Option 3: Hybrid Approach")
        print("   - Try keyword-based first")
        print("   - If confidence < 70%, use VLM classification")
        print("   - Run: python test_improved_classifier.py /path/to/pdf --hybrid")
        print()
        
        return False
    else:
        print("✅ Data structure is good!")
        print("   The classifier should work correctly.")
        print("   If still getting 0.0 confidence, check:")
        print("   - Classifier logic bugs")
        print("   - Page number indexing issues")
        print()
        return True


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnose classification issues")
    parser.add_argument(
        "results_dir",
        nargs='?',
        help="Path to Phase 1 results directory (optional, will auto-detect)"
    )
    
    args = parser.parse_args()
    
    if args.results_dir:
        results_dir = Path(args.results_dir)
    else:
        print("🔍 Auto-detecting Phase 1 results...")
        results_dir = find_phase1_results()
        if not results_dir:
            print("❌ Could not find Phase 1 results!")
            print()
            print("Please specify the directory:")
            print("   python diagnose_live.py /path/to/analysis_results")
            print()
            print("Or run Phase 1 first:")
            print("   python test_phase1.py /path/to/pdf")
            return 1
        print(f"✅ Found results at: {results_dir}")
        print()
    
    if not results_dir.exists():
        print(f"❌ Directory not found: {results_dir}")
        return 1
    
    success = analyze_phase1_output(results_dir)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())