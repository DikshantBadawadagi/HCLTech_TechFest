# Llama 3.2 Vision Local Setup

## What Changed
- ✅ Switched from Gemini Vision (rate-limited API) to **Llama 3.2 Vision (local model)**
- ✅ No more API rate limits - runs on your GPU
- ✅ Automatic GPU detection (CUDA) with CPU fallback
- ✅ Same interface, drop-in replacement

## Installation

### 1. Install PyTorch with GPU Support (NVIDIA CUDA)
```bash
# For CUDA 12.1 (recommended)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Or for CPU only (slower)
pip install torch torchvision torchaudio
```

### 2. Install other dependencies
```bash
pip install -r requirements.txt
```

### 3. First Run (Model Download)
The first time you run the endpoint, it will automatically download the Llama 3.2 Vision model (~15-20 GB).
- This happens once and is cached locally
- Requires ~30-40 GB free disk space temporarily
- Takes 5-10 minutes depending on internet speed

## Hardware Requirements
- **GPU (Recommended)**: NVIDIA GPU with 16+ GB VRAM (RTX 4090, A100, etc.)
- **CPU**: Will work but very slow (10-30 seconds per frame)

## Performance Estimates
- **With GPU**: ~1-2 seconds per frame
- **With CPU**: ~15-30 seconds per frame

## How It Works
1. Video → Audio extraction
2. Audio → Transcript (Groq Whisper API)
3. Transcript → Topics (Gemini - minimal API calls)
4. Topics → Frame sampling (OpenCV)
5. Frames → Analysis (Llama Vision - **local, no API limits**)

## Troubleshooting

### Out of Memory Error
If you get CUDA out of memory error:
- Reduce batch size in `llama_vision_service.py`
- Use CPU instead: `self.device = "cpu"`
- Close other applications to free GPU memory

### Model Won't Download
- Check internet connection
- Ensure HuggingFace token in environment (if needed)
- Clear `~/.cache/huggingface/` and retry

### Slow Performance
- Check GPU is being used: `nvidia-smi` should show process
- Ensure CUDA is properly installed with PyTorch
- GPU should show ~90%+ usage if working correctly
