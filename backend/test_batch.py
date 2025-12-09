#!/usr/bin/env python3
"""
Test script for batch video analysis
"""
import requests
import time
import sys
from pathlib import Path
import mimetypes

BASE_URL = "http://localhost:8000/api/v1/batch"

def test_batch_analysis(video_files: list, context: str = None):
    """
    Test batch analysis with multiple video chunks
    
    Args:
        video_files: List of video file paths
        context: Optional context for all chunks
    """
    print("="*80)
    print("🚀 BATCH VIDEO ANALYSIS TEST")
    print("="*80)
    
    # Validate files
    for video_file in video_files:
        if not Path(video_file).exists():
            print(f"❌ File not found: {video_file}")
            return
    
    print(f"\n📦 Batch Upload:")
    print(f"   Total chunks: {len(video_files)}")
    for i, vf in enumerate(video_files, 1):
        print(f"   {i}. {Path(vf).name}")
    
    if context:
        print(f"\n📝 Context: {context}")
    
    # Prepare files for upload
    files = []
    for video_file in video_files:
        mime_type, _ = mimetypes.guess_type(video_file)
        if not mime_type:
            mime_type = 'video/mp4'
        
        f = open(video_file, 'rb')
        files.append(('files', (Path(video_file).name, f, mime_type)))
    
    # Prepare data
    data = {}
    if context:
        data['context'] = context
    
    print(f"\n⏳ Uploading and analyzing...")
    print(f"   Expected parallel processing with 4 workers")
    print(f"   This will be MUCH faster than sequential!")
    
    start_time = time.time()
    
    try:
        # Make request
        response = requests.post(
            f"{BASE_URL}/analyze-batch",
            files=files,
            data=data
        )
        
        # Close files
        for _, (_, f, _) in files:
            f.close()
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Batch analysis completed in {elapsed:.1f}s!")
            print_batch_results(result, elapsed)
        else:
            print(f"\n❌ Batch analysis failed: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        for _, (_, f, _) in files:
            try:
                f.close()
            except:
                pass

def print_batch_results(data: dict, wall_time: float):
    """Pretty print batch results"""
    print("\n" + "="*80)
    print("📊 BATCH ANALYSIS RESULTS")
    print("="*80)
    
    # Summary
    print(f"\n📦 Batch ID: {data['batch_id']}")
    print(f"   Status: {data['status'].upper()}")
    print(f"   Total Chunks: {data['total_chunks']}")
    print(f"   Successful: {data['successful_chunks']}")
    print(f"   Failed: {data['failed_chunks']}")
    
    # Performance
    print(f"\n⚡ Performance:")
    print(f"   Wall Clock Time: {wall_time:.2f}s")
    print(f"   Total Processing Time: {data['total_processing_time']:.2f}s")
    print(f"   Average per Chunk: {data['average_chunk_time']:.2f}s")
    
    # Calculate speedup
    total_sequential = sum(r['processing_time'] for r in data['results'])
    speedup = total_sequential / wall_time if wall_time > 0 else 1
    print(f"   Speedup: {speedup:.1f}x 🚀")
    print(f"   (Sequential would take: {total_sequential:.1f}s)")
    
    # Individual chunk results
    print(f"\n📹 Individual Chunk Results:")
    print("-"*80)
    
    for result in data['results']:
        print(f"\n  {result['chunk_id']}: {result['filename']}")
        print(f"     Status: {result['status']}")
        
        if result['status'] == 'success':
            print(f"     Duration: {result['duration']:.1f}s")
            print(f"     Processing Time: {result['processing_time']:.1f}s")
            print(f"     Overall Score: {result['overall_score']:.1f}/100")
            
            print(f"\n     📊 Scores:")
            print(f"        Communication: {result['communication']['score']:.1f}/100")
            print(f"        Engagement: {result['engagement']['score']:.1f}/100")
            print(f"        Clarity: {result['clarity']['score']:.1f}/100")
            print(f"        Interaction: {result['interaction']['score']:.1f}/100")
            
            # Transcript preview
            transcript = result['transcript']
            preview = transcript[:100] + "..." if len(transcript) > 100 else transcript
            print(f"\n     📝 Transcript: {preview}")
        else:
            print(f"     ❌ Error: {result.get('error_message', 'Unknown error')}")
    
    print("\n" + "="*80)

def main():
    """Main test"""
    if len(sys.argv) < 2:
        print("Usage: python test_batch.py <video1> <video2> ... [context]")
        print("\nExamples:")
        print("  python test_batch.py chunk1.mp4 chunk2.mp4 chunk3.mp4")
        print('  python test_batch.py *.mp4 "Mathematics lecture on calculus"')
        sys.exit(1)
    
    # Parse arguments
    args = sys.argv[1:]
    
    # Check if last arg is context (not a file)
    if args and not Path(args[-1]).suffix:
        context = args[-1]
        video_files = args[:-1]
    else:
        context = None
        video_files = args
    
    # Filter out non-existent files
    video_files = [f for f in video_files if Path(f).exists()]
    
    if not video_files:
        print("❌ No valid video files provided")
        sys.exit(1)
    
    # Health check
    print("🏥 Checking API health...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API is healthy!\n")
        else:
            print("❌ API is not responding")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        sys.exit(1)
    
    # Run test
    test_batch_analysis(video_files, context)

if __name__ == "__main__":
    main()