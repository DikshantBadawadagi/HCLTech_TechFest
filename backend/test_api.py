#!/usr/bin/env python3
"""
Test script for Teacher Video Analysis API
"""
import requests
import time
import sys
from pathlib import Path
import mimetypes

BASE_URL = "http://localhost:8000/api/v1"

def upload_video(video_path: str):
    """Upload a video file"""
    print(f"📤 Uploading video: {video_path}")
    
    if not Path(video_path).exists():
        print(f"❌ File not found: {video_path}")
        return None
    
    with open(video_path, 'rb') as f:
        # include filename and a guessed mime type so FastAPI's UploadFile.content_type is set
        mime_type, _ = mimetypes.guess_type(video_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        files = {'file': (Path(video_path).name, f, mime_type)}
        response = requests.post(f"{BASE_URL}/videos/upload", files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Video uploaded successfully!")
        print(f"   Video ID: {data['video_id']}")
        print(f"   Duration: {data['duration']} seconds")
        print(f"   Size: {data['size'] / (1024*1024):.2f} MB")
        return data['video_id']
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None

def start_analysis(video_id: str, context: str = None):
    """Start video analysis"""
    print(f"\n🔍 Starting analysis for video: {video_id}")
    
    payload = {"video_id": video_id}
    if context:
        payload["context"] = context
        print(f"   📝 Context provided: {context[:100]}...")
    
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Analysis started!")
        print(f"   Analysis ID: {data['analysis_id']}")
        return data['analysis_id']
    else:
        print(f"❌ Analysis failed: {response.status_code}")
        print(response.text)
        return None

def get_analysis_result(analysis_id: str, wait: bool = True):
    """Get analysis results"""
    print(f"\n📊 Fetching analysis results: {analysis_id}")
    
    max_attempts = 60  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f"{BASE_URL}/analysis/{analysis_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            
            if status == 'completed':
                print("\n✅ Analysis completed!")
                print_results(data)
                return data
            elif status == 'failed':
                print(f"\n❌ Analysis failed: {data.get('error_message', 'Unknown error')}")
                return None
            elif status == 'processing':
                if wait:
                    print(f"⏳ Processing... (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(5)
                    attempt += 1
                else:
                    print("⏳ Analysis still processing")
                    return None
            else:
                print(f"❓ Unknown status: {status}")
                return None
        else:
            print(f"❌ Failed to fetch results: {response.status_code}")
            return None
    
    print("⏰ Timeout waiting for analysis")
    return None

def print_results(data: dict):
    """Pretty print analysis results"""
    print("\n" + "="*60)
    print("📈 ANALYSIS RESULTS")
    print("="*60)
    
    if data.get('overall_score'):
        print(f"\n🎯 OVERALL SCORE: {data['overall_score']}/100")
    
    # Communication
    if data.get('communication'):
        comm = data['communication']
        print(f"\n💬 COMMUNICATION (Score: {comm['score']}/100)")
        print(f"   Speaking Rate: {comm['speaking_rate']} WPM")
        print(f"   Pauses: {comm['pause_count']}")
        print(f"   Stuttering: {comm['stuttering_count']}")
        print(f"   Pitch Mean: {comm['pitch_mean']} Hz")
    
    # Engagement
    if data.get('engagement'):
        eng = data['engagement']
        print(f"\n🎤 ENGAGEMENT (Score: {eng['score']}/100)")
        print(f"   Q&A Pairs: {eng['qna_pairs']}")
        print(f"   Questions: {eng['question_count']}")
        print(f"   Interactions: {eng['interaction_moments']}")
        print(f"   Rhetorical Questions: {eng.get('rhetorical_questions', 0)}")
        print(f"   Direct Address: {eng.get('direct_address_count', 0)}")
    
    # Technical Depth
    if data.get('technical_depth'):
        tech = data['technical_depth']
        print(f"\n🧠 TECHNICAL DEPTH (Score: {tech['score']}/100)")
        print(f"   Domain: {tech.get('domain', 'general').upper()}")
        print(f"   Concepts: {tech['concept_count']}")
        if tech.get('technical_terms'):
            print(f"   Terms: {', '.join(tech['technical_terms'][:5])}")
        print(f"   Correctness: {tech['concept_correctness_score']}")
        if tech.get('context_provided'):
            print(f"   ✅ User context was used in analysis")
        if tech.get('llm_analysis'):
            print(f"   🤖 AI Analysis: {tech['llm_analysis'][:150]}...")
    
    # Clarity
    if data.get('clarity'):
        clarity = data['clarity']
        print(f"\n🎥 CLARITY (Score: {clarity['score']}/100)")
        print(f"   Video Quality: {clarity['video_quality_score']:.2f}")
        print(f"   Audio Quality: {clarity['audio_quality_score']:.2f}")
        print(f"   Eye Contact: {clarity['eye_contact_percentage']:.1f}%")
    
    # Interaction
    if data.get('interaction'):
        interact = data['interaction']
        print(f"\n👋 INTERACTION (Score: {interact['score']}/100)")
        print(f"   Eye Contact: {interact['eye_contact_duration']:.1f}%")
        print(f"   Gestures/min: {interact['gesture_frequency']:.1f}")
        print(f"   Pose Stability: {interact['pose_stability']:.2f}")
    
    # Transcript preview
    if data.get('transcript'):
        transcript = data['transcript']
        preview = transcript[:200] + "..." if len(transcript) > 200 else transcript
        print(f"\n📝 TRANSCRIPT PREVIEW:")
        print(f"   {preview}")
        print(f"   Confidence: {data.get('transcript_confidence', 0):.2f}")
    
    print(f"\n⏱️  Processing Time: {data.get('processing_time', 0):.2f} seconds")
    print("="*60 + "\n")

def main():
    """Main test flow"""
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <video_path> [context]")
        print("Example: python test_api.py lecture.mp4")
        print('Example with context: python test_api.py lecture.mp4 "DSA lecture on Binary Search"')
        sys.exit(1)
    
    video_path = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Test health endpoint
    print("🏥 Testing API health...")
    response = requests.get("http://localhost:8000/health")
    if response.status_code == 200:
        print("✅ API is healthy!\n")
    else:
        print("❌ API is not responding")
        sys.exit(1)
    
    # Upload video
    video_id = upload_video(video_path)
    if not video_id:
        sys.exit(1)
    
    # Start analysis
    analysis_id = start_analysis(video_id, context)
    if not analysis_id:
        sys.exit(1)
    
    # Wait for results
    get_analysis_result(analysis_id, wait=True)

if __name__ == "__main__":
    main()