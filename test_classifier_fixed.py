"""
Test Fixed Classifier
Tests the bug-fixed classifier on actual Phase 1 results
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from segmentation.classifier_fixed import FixedClassifier


def test_fixed_classifier(results_dir: str):
    """
    Test fixed classifier on Phase 1 results
    
    Args:
        results_dir: Path to Phase 1 analysis results directory
    """
    results_path = Path(results_dir)
    
    print("=" * 70)
    print("🚀 TESTING FIXED CLASSIFIER")
    print("=" * 70)
    print()
    
    # Load Phase 1 page analyses
    page_analyses_file = results_path / "page_analyses.json"
    if not page_analyses_file.exists():
        print(f"❌ Page analyses not found: {page_analyses_file}")
        return False
    
    with open(page_analyses_file) as f:
        page_analyses = json.load(f)
    
    print(f"📁 Results Directory: {results_path}")
    print(f"📄 Loaded {len(page_analyses)} page analyses")
    print()
    
    # Load boundaries
    summary_file = results_path / "analysis_summary.json"
    if not summary_file.exists():
        print(f"❌ Summary not found: {summary_file}")
        return False
    
    with open(summary_file) as f:
        summary = json.load(f)
    
    boundaries = [(b['start_page'], b['end_page']) 
                  for b in summary.get('document_boundaries', [])]
    
    print(f"📊 Found {len(boundaries)} segment(s):")
    for i, (start, end) in enumerate(boundaries, 1):
        print(f"   Segment {i}: Pages {start}-{end}")
    print()
    
    # Classify with fixed classifier
    print("📌 Classification with Fixed Classifier")
    print("-" * 70)
    
    classifier = FixedClassifier()
    classifications = classifier.classify_all_segments(boundaries, page_analyses)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 CLASSIFICATION RESULTS")
    print("=" * 70)
    
    for result in classifications:
        print(f"\n🔖 Segment {result['segment_id']}")
        print(f"   Pages: {result['segment_pages'][0]}-{result['segment_pages'][-1]}")
        print(f"   Type: {result['document_type']}")
        print(f"   Confidence: {result['confidence']:.1%}")
        print(f"   Reasoning: {result['reasoning']}")
        
        if 'scores' in result:
            wo = result['scores']['work_order']
            turn = result['scores']['turnover']
            print(f"   Scores: WO={wo:.2f}, Turnover={turn:.2f}")
        
        # Confidence indicator
        if result['confidence'] >= 0.9:
            indicator = "✅ Excellent"
        elif result['confidence'] >= 0.7:
            indicator = "✓ Good"
        elif result['confidence'] >= 0.5:
            indicator = "⚠️  Fair"
        else:
            indicator = "❌ Low - needs review"
        print(f"   {indicator}")
    
    # Save results
    output_file = results_path / "classifications_fixed.json"
    with open(output_file, 'w') as f:
        json.dump(classifications, f, indent=2)
    print(f"\n💾 Results saved: {output_file}")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ FIXED CLASSIFIER TEST COMPLETE")
    print("=" * 70)
    print()
    
    from collections import Counter
    type_counts = Counter(r['document_type'] for r in classifications)
    
    print("📈 Summary:")
    for doc_type, count in type_counts.items():
        print(f"   {doc_type}: {count} document(s)")
    
    avg_conf = sum(r['confidence'] for r in classifications) / len(classifications)
    print(f"   Average Confidence: {avg_conf:.1%}")
    
    high_conf = sum(1 for r in classifications if r['confidence'] >= 0.7)
    print(f"   High Confidence: {high_conf}/{len(classifications)}")
    
    if avg_conf >= 0.7:
        print("\n✅ Classification working well! Ready for Phase 2B")
        return True
    else:
        print("\n⚠️  Confidence still low - may need VLM-based approach")
        return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test fixed classifier"
    )
    parser.add_argument(
        "results_dir",
        nargs='?',
        default="uploads/analysis_results",
        help="Path to Phase 1 results directory"
    )
    
    args = parser.parse_args()
    
    results_path = Path(args.results_dir)
    if not results_path.exists():
        print(f"❌ Results directory not found: {results_path}")
        print()
        print("Trying common locations...")
        
        search_paths = [
            Path("uploads/analysis_results"),
            Path("/mnt/user-data/uploads/analysis_results"),
            Path("/workspaces/Financial-Document-Processing/uploads/analysis_results"),
            Path.cwd() / "analysis_results"
        ]
        
        for path in search_paths:
            if path.exists():
                print(f"✅ Found results at: {path}")
                results_path = path
                break
        else:
            print("❌ Could not find Phase 1 results")
            return 1
    
    success = test_fixed_classifier(str(results_path))
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())