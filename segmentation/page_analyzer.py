"""
VLM-based Page Analyzer
Analyzes individual pages to detect document boundaries
"""

import json
from typing import Dict, Any, List
from pathlib import Path
import sys

# Add current project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.vlm_provider import ModelManager, extract_json_from_response
from config.document_types import get_page_analysis_prompt


class PageAnalyzer:
    """Analyzes individual pages with VLM"""
    
    def __init__(self, model_manager: ModelManager):
        """
        Initialize page analyzer
        
        Args:
            model_manager: VLM model manager instance
        """
        self.model_manager = model_manager
    
    def analyze_page(
        self,
        image_path: str,
        page_number: int,
        total_pages: int
    ) -> Dict[str, Any]:
        """
        Analyze a single page using VLM
        
        Args:
            image_path: Path to page image
            page_number: Current page number (1-indexed)
            total_pages: Total number of pages
            
        Returns:
            Page analysis results
        """
        print(f"🔍 Analyzing page {page_number}/{total_pages}...")
        
        # Get prompt
        prompt = get_page_analysis_prompt(page_number, total_pages)
        
        # Analyze with VLM
        result = self.model_manager.analyze_image_with_fallback(image_path, prompt)
        
        if not result['success']:
            return {
                "success": False,
                "error": result['error'],
                "page_number": page_number
            }
        
        try:
            # Parse VLM response
            analysis = extract_json_from_response(result['response'])
            
            # Add metadata
            analysis['page_number'] = page_number
            analysis['total_pages'] = total_pages
            analysis['image_path'] = image_path
            analysis['model_used'] = result['model_used']
            analysis['processing_time'] = result['processing_time']
            
            # Log key findings
            print(f"   ✓ Page Type: {analysis.get('page_type', 'UNKNOWN')}")
            if analysis.get('document_type_hints'):
                print(f"   ✓ Document Hints: {', '.join(analysis['document_type_hints'])}")
            if analysis.get('is_document_start'):
                print(f"   🆕 NEW DOCUMENT START")
            if analysis.get('is_document_end'):
                print(f"   🏁 DOCUMENT END")
            
            return {
                "success": True,
                "data": analysis
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Failed to parse VLM response: {str(e)}",
                "raw_response": result['response'][:500],
                "page_number": page_number
            }
    
    def analyze_all_pages(
        self,
        image_paths: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyze all pages in sequence
        
        Args:
            image_paths: List of page image paths
            
        Returns:
            List of page analysis results
        """
        total_pages = len(image_paths)
        analyses = []
        
        print(f"\n📊 Starting page-by-page analysis...")
        print(f"   Total pages: {total_pages}\n")
        
        for i, image_path in enumerate(image_paths, start=1):
            analysis_result = self.analyze_page(image_path, i, total_pages)
            analyses.append(analysis_result)
            print()  # Blank line between pages
        
        # Summary
        successful = sum(1 for a in analyses if a.get('success'))
        print(f"✅ Analysis complete: {successful}/{total_pages} pages analyzed successfully\n")
        
        return analyses
    
    def get_document_boundaries(self, analyses: List[Dict[str, Any]]) -> List[Tuple[int, int]]:
        """
        Determine document boundaries from page analyses
        
        Args:
            analyses: List of page analysis results
            
        Returns:
            List of (start_page, end_page) tuples
        """
        boundaries = []
        current_start = 1
        
        for i, analysis in enumerate(analyses, start=1):
            if not analysis.get('success'):
                continue
            
            data = analysis['data']
            
            # Check if this page starts a new document
            if i > 1 and data.get('is_document_start'):
                # Previous document ends at page i-1
                boundaries.append((current_start, i - 1))
                current_start = i
        
        # Add final document
        if current_start <= len(analyses):
            boundaries.append((current_start, len(analyses)))
        
        return boundaries


def save_analysis_results(analyses: List[Dict[str, Any]], output_path: str):
    """Save page analyses to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(analyses, f, indent=2)
    print(f"💾 Analysis results saved to: {output_path}")


# Quick test
if __name__ == "__main__":
    from utils.vlm_provider import ModelManager
    from utils.pdf_processor import prepare_pdf_for_analysis
    
    # Test with sample PDF
    test_pdf = "/mnt/user-data/uploads/WOs_sample.pdf"
    
    # Initialize VLM
    print("🤖 Initializing VLM...")
    model_manager = ModelManager(
        primary_model="openrouter_gemini",
        fallback_model="groq_llama_scout"
    )
    
    # Prepare PDF
    image_paths, page_count, metadata = prepare_pdf_for_analysis(test_pdf)
    
    # Analyze pages
    analyzer = PageAnalyzer(model_manager)
    analyses = analyzer.analyze_all_pages(image_paths[:3])  # Test first 3 pages
    
    # Get boundaries
    boundaries = analyzer.get_document_boundaries(analyses)
    print(f"\n📍 Detected document boundaries: {boundaries}")
    
    # Save results
    save_analysis_results(analyses, "/home/claude/page_analysis_results.json")
