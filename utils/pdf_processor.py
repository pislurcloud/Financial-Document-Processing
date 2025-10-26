"""
PDF Processing Utilities
Handles multi-page PDF splitting and conversion to images
"""

from pdf2image import convert_from_path
from pypdf import PdfReader, PdfWriter
from pathlib import Path
from typing import List, Tuple
import tempfile
import os


class PDFProcessor:
    """Process multi-page PDFs"""
    
    def __init__(self, dpi: int = 300):
        """
        Initialize PDF processor
        
        Args:
            dpi: Resolution for PDF to image conversion
        """
        self.dpi = dpi
    
    def pdf_to_images(self, pdf_path: str) -> List[str]:
        """
        Convert each PDF page to high-quality image
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of image paths (one per page)
        """
        print(f"📄 Converting PDF to images: {pdf_path}")
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=self.dpi, fmt='png')
        
        # Save images to temp directory
        image_paths = []
        base_name = Path(pdf_path).stem
        output_dir = Path(pdf_path).parent / f"{base_name}_pages"
        output_dir.mkdir(exist_ok=True)
        
        for i, img in enumerate(images, start=1):
            image_path = output_dir / f"page_{i:03d}.png"
            img.save(image_path, 'PNG', quality=95)
            image_paths.append(str(image_path))
            print(f"   ✓ Page {i} → {image_path.name}")
        
        print(f"✅ Converted {len(image_paths)} pages\n")
        return image_paths
    
    def get_page_count(self, pdf_path: str) -> int:
        """Get total pages in PDF"""
        reader = PdfReader(pdf_path)
        return len(reader.pages)
    
    def extract_page_range(
        self,
        pdf_path: str,
        start_page: int,
        end_page: int,
        output_path: str = None
    ) -> str:
        """
        Extract specific pages into new PDF
        
        Args:
            pdf_path: Source PDF
            start_page: Start page (1-indexed)
            end_page: End page (1-indexed, inclusive)
            output_path: Output PDF path (optional)
            
        Returns:
            Path to extracted PDF
        """
        reader = PdfReader(pdf_path)
        writer = PdfWriter()
        
        # Convert to 0-indexed
        for page_num in range(start_page - 1, end_page):
            if page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])
        
        if output_path is None:
            base = Path(pdf_path).stem
            output_path = Path(pdf_path).parent / f"{base}_pages_{start_page}-{end_page}.pdf"
        
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        return str(output_path)
    
    def split_pdf(
        self,
        pdf_path: str,
        page_ranges: List[Tuple[int, int]],
        output_dir: str = None
    ) -> List[str]:
        """
        Split PDF into multiple PDFs based on page ranges
        
        Args:
            pdf_path: Source PDF
            page_ranges: List of (start_page, end_page) tuples (1-indexed)
            output_dir: Directory for output files
            
        Returns:
            List of output PDF paths
        """
        if output_dir is None:
            output_dir = Path(pdf_path).parent / "split_documents"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(exist_ok=True)
        
        output_files = []
        base_name = Path(pdf_path).stem
        
        for i, (start, end) in enumerate(page_ranges, start=1):
            output_path = output_dir / f"{base_name}_segment_{i:02d}.pdf"
            self.extract_page_range(pdf_path, start, end, str(output_path))
            output_files.append(str(output_path))
            print(f"   ✓ Segment {i}: Pages {start}-{end} → {output_path.name}")
        
        return output_files
    
    def get_pdf_metadata(self, pdf_path: str) -> dict:
        """Extract PDF metadata"""
        reader = PdfReader(pdf_path)
        meta = reader.metadata
        
        return {
            "title": meta.title if meta and meta.title else None,
            "author": meta.author if meta and meta.author else None,
            "subject": meta.subject if meta and meta.subject else None,
            "creator": meta.creator if meta and meta.creator else None,
            "producer": meta.producer if meta and meta.producer else None,
            "creation_date": str(meta.creation_date) if meta and meta.creation_date else None,
            "page_count": len(reader.pages)
        }


def prepare_pdf_for_analysis(pdf_path: str) -> Tuple[List[str], int, dict]:
    """
    Complete PDF preparation workflow
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Tuple of (image_paths, page_count, metadata)
    """
    processor = PDFProcessor()
    
    # Get metadata
    metadata = processor.get_pdf_metadata(pdf_path)
    page_count = metadata["page_count"]
    
    print(f"\n📋 PDF Info:")
    print(f"   Pages: {page_count}")
    if metadata["title"]:
        print(f"   Title: {metadata['title']}")
    print()
    
    # Convert to images
    image_paths = processor.pdf_to_images(pdf_path)
    
    return image_paths, page_count, metadata


# Quick test
if __name__ == "__main__":
    # Test with sample PDF
    test_pdf = "/mnt/user-data/uploads/WOs_sample.pdf"
    
    if os.path.exists(test_pdf):
        image_paths, page_count, metadata = prepare_pdf_for_analysis(test_pdf)
        print(f"✅ Prepared {page_count} pages for analysis")
        print(f"   Images: {len(image_paths)}")
    else:
        print("Test PDF not found")
