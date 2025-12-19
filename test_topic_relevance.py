#!/usr/bin/env python3
"""
Test the topic relevance analysis endpoint
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_topic_relevance():
    """Test topic relevance endpoint with a video"""
    
    # Use one of your test videos
    video_path = "mentorTest2.mp4"  # Change to your video
    
    print("🎬 Testing Topic Relevance Analysis")
    print(f"Video: {video_path}\n")
    
    with open(video_path, 'rb') as f:
        files = {'file': f}
        
        print("📤 Uploading and analyzing...")
        response = requests.post(
            f"{BASE_URL}/analyze-topic-relevance",
            files=files
        )
    
    if response.status_code == 200:
        data = response.json()
        
        print("\n✅ Analysis Complete!\n")
        print("=" * 70)
        
        # Show transcript
        print("\n📝 TRANSCRIPT:")
        print(data['transcript'][:500] + "...\n" if len(data['transcript']) > 500 else data['transcript'])
        
        # Show topics
        print("\n🎯 TOPICS FOUND:")
        for topic in data['topics_found']:
            print(f"  • {topic['topic']} (at {topic['timestamp']}s)")
        
        # Show frame analysis
        print(f"\n🖼️  FRAME ANALYSIS ({data['total_frames_analyzed']} frames):")
        print("-" * 70)
        
        for frame in data['frame_analysis']:
            print(f"\n⏱️  Timestamp: {frame['timestamp_seconds']}s")
            print(f"📌 Topic: {frame['topic']}")
            analysis = frame['analysis']
            print(f"✓ Relevant: {analysis.get('relevant', 'N/A')}")
            print(f"📷 Description: {analysis.get('description', 'N/A')}")
            print(f"💡 Explanation: {analysis.get('explanation', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("\n✅ Test successful!")
        
        # Save full JSON
        with open('topic_analysis_result.json', 'w') as f:
            json.dump(data, f, indent=2)
        print("\n💾 Full result saved to: topic_analysis_result.json")
    
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_topic_relevance()
