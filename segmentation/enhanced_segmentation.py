"""
Enhanced Document Segmentation
Splits documents into homogeneous segments based on sub-types
Each segment contains only ONE sub-type
"""

from typing import List, Dict, Any, Tuple
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.document_types_enhanced import MainDocumentType


def create_homogeneous_segments(
    page_analyses: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Create homogeneous segments where each segment has only ONE sub-type
    
    Args:
        page_analyses: List of page analyses with sub-type information
        
    Returns:
        List of segment definitions
    """
    print("\n📊 Creating Homogeneous Segments (by sub-type)...")
    print("-" * 80)
    
    if not page_analyses:
        return []
    
    segments = []
    current_segment = None
    
    for i, analysis in enumerate(page_analyses, 1):
        if not analysis.get('success'):
            continue
        
        data = analysis.get('data', {})
        main_type = data.get('main_type')
        sub_type = data.get('sub_type')
        confidence = data.get('sub_type_confidence', 0.0)
        
        # Start new segment if:
        # 1. First page
        # 2. Sub-type changed
        # 3. Low confidence on previous (might be boundary)
        
        if current_segment is None:
            # First segment
            current_segment = {
                'start_page': i,
                'end_page': i,
                'main_type': main_type,
                'sub_type': sub_type,
                'pages': [i],
                'confidence': confidence
            }
        elif (sub_type != current_segment['sub_type'] or 
              main_type != current_segment['main_type']):
            # Sub-type changed - close current segment and start new one
            segments.append(current_segment)
            
            print(f"   Segment {len(segments)}: Pages {current_segment['start_page']}-{current_segment['end_page']}")
            print(f"      Type: {current_segment['main_type']} → {current_segment['sub_type']}")
            print(f"      Confidence: {current_segment['confidence']:.2f}")
            
            current_segment = {
                'start_page': i,
                'end_page': i,
                'main_type': main_type,
                'sub_type': sub_type,
                'pages': [i],
                'confidence': confidence
            }
        else:
            # Same sub-type - continue current segment
            current_segment['end_page'] = i
            current_segment['pages'].append(i)
            # Update confidence (average)
            current_segment['confidence'] = (
                current_segment['confidence'] + confidence
            ) / 2
    
    # Add last segment
    if current_segment:
        segments.append(current_segment)
        print(f"   Segment {len(segments)}: Pages {current_segment['start_page']}-{current_segment['end_page']}")
        print(f"      Type: {current_segment['main_type']} → {current_segment['sub_type']}")
        print(f"      Confidence: {current_segment['confidence']:.2f}")
    
    print(f"\n✅ Created {len(segments)} homogeneous segment(s)")
    
    return segments


def merge_single_page_segments(
    segments: List[Dict[str, Any]],
    min_confidence: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Optionally merge single-page segments with low confidence
    into adjacent segments
    
    Args:
        segments: List of segment definitions
        min_confidence: Minimum confidence to keep as separate segment
        
    Returns:
        Merged segment list
    """
    if len(segments) <= 1:
        return segments
    
    merged = []
    i = 0
    
    while i < len(segments):
        current = segments[i]
        
        # Check if current segment is single page with low confidence
        is_single_page = (current['end_page'] - current['start_page']) == 0
        is_low_conf = current['confidence'] < min_confidence
        
        if is_single_page and is_low_conf and i > 0:
            # Try to merge with previous segment
            prev = merged[-1]
            
            # Only merge if main types match
            if prev['main_type'] == current['main_type']:
                prev['end_page'] = current['end_page']
                prev['pages'].extend(current['pages'])
                prev['sub_type'] = f"{prev['sub_type']} + {current['sub_type']}"
                print(f"   ⚠️  Merged low-confidence page {current['start_page']} into previous segment")
                i += 1
                continue
        
        merged.append(current)
        i += 1
    
    return merged


def get_segment_boundaries(
    page_analyses: List[Dict[str, Any]],
    merge_low_confidence: bool = True
) -> List[Tuple[int, int]]:
    """
    Get document boundaries as (start, end) tuples
    Compatible with existing classifier interface
    
    Args:
        page_analyses: List of page analyses with sub-type info
        merge_low_confidence: Whether to merge single low-confidence pages
        
    Returns:
        List of (start_page, end_page) tuples
    """
    segments = create_homogeneous_segments(page_analyses)
    
    if merge_low_confidence:
        segments = merge_single_page_segments(segments)
    
    boundaries = [(s['start_page'], s['end_page']) for s in segments]
    return boundaries


def get_detailed_segments(
    page_analyses: List[Dict[str, Any]],
    merge_low_confidence: bool = True
) -> List[Dict[str, Any]]:
    """
    Get detailed segment information including sub-types
    
    Args:
        page_analyses: List of page analyses with sub-type info
        merge_low_confidence: Whether to merge single low-confidence pages
        
    Returns:
        List of detailed segment definitions with sub-type info
    """
    segments = create_homogeneous_segments(page_analyses)
    
    if merge_low_confidence:
        segments = merge_single_page_segments(segments)
    
    # Add segment IDs
    for i, segment in enumerate(segments, 1):
        segment['segment_id'] = i
    
    return segments