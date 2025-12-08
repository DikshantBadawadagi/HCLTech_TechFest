#!/usr/bin/env python3
"""
Quick script to check if Gemini API is working
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.config import settings
import google.generativeai as genai

def check_gemini():
    print("🔍 Checking Gemini Configuration")
    print("=" * 60)
    
    # Check API key
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY not set in .env file")
        print("\nTo fix:")
        print("1. Get API key from: https://makersuite.google.com/app/apikey")
        print("2. Add to backend/.env:")
        print("   GEMINI_API_KEY=your_key_here")
        return False
    
    if settings.GEMINI_API_KEY == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY still has default value")
        print("\nYou need to replace it with your actual API key")
        return False
    
    print(f"✅ API Key found: {settings.GEMINI_API_KEY[:20]}...")
    print(f"✅ Model: {settings.GEMINI_MODEL}")
    
    # Try to initialize
    print("\n🔗 Testing connection to Gemini...")
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        # List available models to help debug
        print("📋 Checking available models...")
        try:
            models = genai.list_models()
            available = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            print(f"✅ Found {len(available)} available models")
            
            # Show Gemini 1.5 models
            gemini_15 = [m for m in available if 'gemini-1.5' in m.lower() or 'gemini-1.5' in m]
            if gemini_15:
                print("\n📱 Available Gemini 1.5 models:")
                for model_name in gemini_15[:5]:
                    print(f"   • {model_name}")
        except Exception as e:
            print(f"⚠️  Could not list models: {e}")
        
        # Try the configured model
        print(f"\n🧪 Testing model: {settings.GEMINI_MODEL}")
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Simple test
        print("📤 Sending test request...")
        response = model.generate_content("Say 'Hello, I am working!' in JSON format: {\"message\": \"...\"}")
        
        print("📥 Response received!")
        print(f"   {response.text[:200]}...")
        
        print("\n✅ GEMINI IS WORKING!")
        print("\nYour API is properly configured and responding.")
        return True
        
    except Exception as e:
        print(f"\n❌ Gemini test failed: {e}")
        print(f"\nError type: {type(e).__name__}")
        
        if "not found" in str(e).lower() or "404" in str(e):
            print("\n⚠️  Model not found error")
            print("\nTry these alternative model names in your .env:")
            print("   GEMINI_MODEL=gemini-1.5-flash-latest")
            print("   GEMINI_MODEL=gemini-1.5-pro-latest")
            print("   GEMINI_MODEL=gemini-pro")
        elif "API_KEY_INVALID" in str(e) or "invalid" in str(e).lower():
            print("\n⚠️  Your API key appears to be invalid")
            print("Get a new one from: https://makersuite.google.com/app/apikey")
        elif "quota" in str(e).lower():
            print("\n⚠️  You may have exceeded your API quota")
            print("Check your usage at: https://makersuite.google.com/")
        else:
            print("\n⚠️  Check your internet connection and API key")
        
        return False

if __name__ == "__main__":
    print("\n")
    success = check_gemini()
    print("\n" + "=" * 60)
    
    if success:
        print("✅ All checks passed! You can use Gemini in your analysis.")
        print("\nNext: Restart Docker and test your videos")
        print("docker-compose restart api")
    else:
        print("❌ Please fix the issues above before using Gemini")
        print("\nThe system will work but will use fallback analysis")
    
    print("=" * 60 + "\n")