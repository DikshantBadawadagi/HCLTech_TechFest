#!/usr/bin/env python3
"""
Interactive test script with context support
"""
import requests
import time
import sys
from pathlib import Path
import mimetypes

BASE_URL = "http://localhost:8000/api/v1"

CONTEXT_EXAMPLES = {
    'dsa': "Data Structures and Algorithms lecture covering advanced topics with examples and complexity analysis",
    'business': "Business strategy presentation on market expansion, customer engagement, and competitive positioning",
    'finance': "Financial analysis covering investment strategies, risk management, and portfolio optimization",
    'math': "Mathematics tutorial covering theory, formulas, and practical problem-solving techniques",
    'science': "Science lecture covering fundamental concepts, experiments, and real-world applications",
}

def upload_and_analyze(video_path: str, context: str = None):
    """Upload video and start analysis"""
    print("="*70)
    print("🎬 TEACHER VIDEO ANALYSIS - WITH GEMINI AI")
    print("="*70)
    
    # Health check
    print("\n🏥 Checking API health...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code != 200:
            print("❌ API is not responding")
            return
        print("✅ API is healthy!")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Upload
    print(f"\n📤 Uploading: {Path(video_path).name}")
    
    if not Path(video_path).exists():
        print(f"❌ File not found: {video_path}")
        return
    
    with open(video_path, 'rb') as f:
        mime_type, _ = mimetypes.guess_type(video_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        files = {'file': (Path(video_path).name, f, mime_type)}
        response = requests.post(f"{BASE_URL}/videos/upload", files=files)
    
    if response.status_code != 200:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return
    
    data = response.json()
    video_id = data['video_id']
    print(f"✅ Video uploaded!")
    print(f"   ID: {video_id}")
    print(f"   Duration: {data['duration']:.1f}s")
    print(f"   Size: {data['size'] / (1024*1024):.2f} MB")
    
    # Start analysis
    print(f"\n🔍 Starting AI-powered analysis...")
    
    payload = {"video_id": video_id}
    if context:
        payload["context"] = context
        print(f"📝 Context: {context}")
    else:
        print("⚠️  No context provided - using auto-detection")
    
    response = requests.post(f"{BASE_URL}/analyze", json=payload)
    
    if response.status_code != 200:
        print(f"❌ Analysis failed: {response.status_code}")
        return
    
    data = response.json()
    analysis_id = data['analysis_id']
    print(f"✅ Analysis started! ID: {analysis_id}")
    
    # Wait for results
    print(f"\n⏳ Processing (parallel + Gemini AI)...")
    
    start_time = time.time()
    max_attempts = 60
    attempt = 0
    
    while attempt < max_attempts:
        response = requests.get(f"{BASE_URL}/analysis/{analysis_id}")
        
        if response.status_code == 200:
            data = response.json()
            status = data['status']
            
            if status == 'completed':
                elapsed = time.time() - start_time
                print(f"\n✅ Analysis completed in {elapsed:.1f} seconds!")
                print_results(data)
                return
            elif status == 'failed':
                print(f"\n❌ Analysis failed: {data.get('error_message', 'Unknown error')}")
                return
            elif status == 'processing':
                dots = "." * (attempt % 4)
                print(f"\r   Analyzing{dots:<4}", end="", flush=True)
                time.sleep(3)
                attempt += 1
        else:
            print(f"\n❌ Failed to fetch results: {response.status_code}")
            return
    
    print("\n⏰ Timeout waiting for analysis")

def print_results(data: dict):
    """Print beautiful results"""
    print("\n" + "="*70)
    print("📊 ANALYSIS RESULTS")
    print("="*70)
    
    # Overall Score
    if data.get('overall_score'):
        score = data['overall_score']
        bar_length = int(score / 2)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"\n🎯 OVERALL SCORE: {score:.1f}/100")
        print(f"   [{bar}] {score:.1f}%")
    
    # Processing time
    if data.get('processing_time'):
        print(f"\n⚡ Processing Time: {data['processing_time']:.1f} seconds")
    
    # Communication
    if data.get('communication'):
        comm = data['communication']
        print(f"\n💬 COMMUNICATION: {comm['score']:.1f}/100")
        print(f"   • Speaking Rate: {comm['speaking_rate']:.1f} WPM")
        print(f"   • Pauses: {comm['pause_count']}")
        print(f"   • Clarity: {'Excellent' if comm['stuttering_count'] == 0 else 'Good'}")
    
    # Engagement
    if data.get('engagement'):
        eng = data['engagement']
        print(f"\n🎤 ENGAGEMENT: {eng['score']:.1f}/100")
        print(f"   • Q&A Pairs: {eng['qna_pairs']}")
        print(f"   • Questions: {eng['question_count']}")
        print(f"   • Interactions: {eng['interaction_moments']}")
        if eng.get('rhetorical_questions'):
            print(f"   • Rhetorical Questions: {eng['rhetorical_questions']}")
    
    # Technical Depth (THE STAR OF THE SHOW!)
    if data.get('technical_depth'):
        tech = data['technical_depth']
        print(f"\n🧠 TECHNICAL DEPTH: {tech['score']:.1f}/100")
        print(f"   • Domain: {tech.get('domain', 'general').upper()}")
        print(f"   • Concepts Covered: {tech['concept_count']}")
        
        if tech.get('technical_terms'):
            terms_str = ', '.join(tech['technical_terms'][:6])
            print(f"   • Key Terms: {terms_str}")
        
        print(f"   • Correctness: {tech['concept_correctness_score']:.2f}")
        
        if tech.get('context_provided'):
            print(f"   ✅ User context was used")
        
        if tech.get('llm_analysis'):
            print(f"\n   🤖 AI ANALYSIS:")
            analysis = tech['llm_analysis']
            # Try to extract summary if JSON response
            try:
                import json
                # Try parsing as JSON first
                if isinstance(analysis, str) and ('{' in analysis):
                    # Clean up markdown
                    clean_analysis = analysis.strip()
                    if clean_analysis.startswith('```'):
                        clean_analysis = clean_analysis.split('```')[1]
                        if clean_analysis.startswith('json'):
                            clean_analysis = clean_analysis[4:]
                    
                    parsed = json.loads(clean_analysis)
                    if 'analysis_summary' in parsed:
                        print(f"   {parsed['analysis_summary']}")
                    else:
                        print(f"   {str(parsed)[:250]}...")
                else:
                    print(f"   {str(analysis)[:250]}...")
            except:
                print(f"   {str(analysis)[:250]}...")
        else:
            print(f"   ⚠️  No AI analysis available (check Gemini API key)")
    
    # Clarity
    if data.get('clarity'):
        clarity = data['clarity']
        print(f"\n🎥 CLARITY: {clarity['score']:.1f}/100")
        print(f"   • Video Quality: {clarity['video_quality_score']:.2f}")
        print(f"   • Audio Quality: {clarity['audio_quality_score']:.2f}")
        print(f"   • Eye Contact: {clarity['eye_contact_percentage']:.1f}%")
    
    # Interaction
    if data.get('interaction'):
        interact = data['interaction']
        print(f"\n👋 INTERACTION: {interact['score']:.1f}/100")
        print(f"   • Eye Contact: {interact['eye_contact_duration']:.1f}%")
        print(f"   • Gestures/min: {interact['gesture_frequency']:.1f}")
        print(f"   • Pose Stability: {interact['pose_stability']:.2f}")
    
    # Transcript preview
    if data.get('transcript'):
        transcript = data['transcript']
        preview = transcript[:150] + "..." if len(transcript) > 150 else transcript
        print(f"\n📝 TRANSCRIPT:")
        print(f"   {preview}")
    
    print("\n" + "="*70)

def main():
    print("🎓 Teacher Video Analysis - Interactive Tester")
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_with_context.py <video_path> [context]")
        print()
        print("Examples:")
        print('  python test_with_context.py lecture.mp4')
        print('  python test_with_context.py lecture.mp4 "DSA lecture on Binary Search"')
        print()
        print("Quick contexts:")
        for key, desc in CONTEXT_EXAMPLES.items():
            print(f"  --{key:<10} {desc}")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # Check for quick context flags
    if len(sys.argv) > 2:
        context_arg = sys.argv[2]
        if context_arg.startswith('--'):
            context_key = context_arg[2:]
            context = CONTEXT_EXAMPLES.get(context_key)
            if not context:
                print(f"❌ Unknown context flag: {context_arg}")
                print(f"Available: {', '.join('--' + k for k in CONTEXT_EXAMPLES.keys())}")
                sys.exit(1)
        else:
            context = context_arg
    else:
        context = None
    
    upload_and_analyze(video_path, context)

if __name__ == "__main__":
    main()