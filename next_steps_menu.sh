#!/bin/bash

# Interactive menu for next steps

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

clear
echo -e "${BLUE}========================================"
echo "Hendrix Pipeline - Next Steps"
echo "========================================${NC}"
echo ""
echo "The basic test worked! What would you like to do next?"
echo ""
echo -e "${GREEN}Setup & Installation:${NC}"
echo "1) Install core dependencies (recommended)"
echo "2) Download AI models"
echo "3) Check GPU/CUDA status"
echo ""
echo -e "${GREEN}Testing & Development:${NC}"
echo "4) Run with actual video analysis (no AI needed)"
echo "5) Test audio transcription (Whisper)"
echo "6) Test with a real video file"
echo ""
echo -e "${GREEN}Advanced Features:${NC}"
echo "7) Set up API server"
echo "8) Create web interface"
echo "9) Batch process multiple videos"
echo ""
echo -e "${GREEN}Documentation & Learning:${NC}"
echo "10) View architecture documentation"
echo "11) Learn about model options"
echo "12) See example use cases"
echo ""
echo "0) Exit"
echo ""
read -p "Enter your choice [0-12]: " choice

case $choice in
    1)
        echo -e "\n${YELLOW}Installing core dependencies...${NC}"
        ./install_core.sh
        ;;
        
    2)
        echo -e "\n${YELLOW}Downloading AI models...${NC}"
        echo "This will download several GB of data. Continue? (y/n)"
        read -p "> " confirm
        if [ "$confirm" = "y" ]; then
            bash scripts/setup/download_models.sh
        fi
        ;;
        
    3)
        echo -e "\n${BLUE}Checking GPU/CUDA status...${NC}"
        source hendrix_venv/bin/activate
        python -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB')
"
        echo ""
        nvidia-smi 2>/dev/null || echo "nvidia-smi not available"
        ;;
        
    4)
        echo -e "\n${YELLOW}Running actual video analysis...${NC}"
        source hendrix_venv/bin/activate
        export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
        
        # Download test video if needed
        if [ ! -f "test_video.mp4" ]; then
            curl -L -o test_video.mp4 "https://test-videos.co.uk/vids/bigbuckbunny/mp4/h264/720/Big_Buck_Bunny_720_10s_1MB.mp4"
        fi
        
        # Run video analysis component
        cd components/video_analysis
        python src/main.py "../../test_video.mp4" --output "../../outputs/video_analysis_test"
        cd ../..
        ;;
        
    5)
        echo -e "\n${YELLOW}Testing audio transcription...${NC}"
        source hendrix_venv/bin/activate
        
        # Check if whisper is installed
        if python -c "import whisper" 2>/dev/null; then
            echo "Testing Whisper transcription..."
            python -c "
import whisper
model = whisper.load_model('tiny')
result = model.transcribe('test_video.mp4')
print('Transcription:', result['text'][:200], '...')
"
        else
            echo -e "${RED}Whisper not installed. Install with: pip install openai-whisper${NC}"
        fi
        ;;
        
    6)
        echo -e "\n${BLUE}Select a video file:${NC}"
        echo "Enter path to video file (or press Enter to use test video):"
        read -p "> " video_path
        
        if [ -z "$video_path" ]; then
            video_path="test_video.mp4"
        fi
        
        if [ -f "$video_path" ]; then
            ./test_video.sh "$video_path"
        else
            echo -e "${RED}File not found: $video_path${NC}"
        fi
        ;;
        
    7)
        echo -e "\n${YELLOW}Setting up API server...${NC}"
        echo "Creating FastAPI server template..."
        cat > api_server.py << 'EOF'
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
from pathlib import Path

app = FastAPI(title="Hendrix Video Analysis API")

@app.get("/")
def read_root():
    return {"message": "Hendrix Video Analysis API", "version": "1.0"}

@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...), profile: str = "fast"):
    # Save uploaded file
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process video (mock for now)
    result = {
        "filename": file.filename,
        "profile": profile,
        "status": "processing",
        "message": "Video analysis started"
    }
    
    # Clean up
    os.remove(temp_path)
    
    return JSONResponse(content=result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF
        echo -e "${GREEN}API server template created: api_server.py${NC}"
        echo "To run: pip install fastapi uvicorn && python api_server.py"
        ;;
        
    8)
        echo -e "\n${YELLOW}Creating web interface...${NC}"
        echo "Choose interface type:"
        echo "a) Gradio (simple, quick)"
        echo "b) Streamlit (more features)"
        read -p "> " ui_choice
        
        if [ "$ui_choice" = "a" ]; then
            cat > gradio_app.py << 'EOF'
import gradio as gr
import subprocess
import json

def process_video(video_file, profile):
    if video_file is None:
        return "Please upload a video", None
    
    # Run pipeline (mock for now)
    result = f"Processing {video_file.name} with {profile} profile..."
    
    # Return results
    return result, None  # text result, file output

iface = gr.Interface(
    fn=process_video,
    inputs=[
        gr.Video(label="Upload Video"),
        gr.Radio(["fast", "balanced", "quality"], label="Profile", value="fast")
    ],
    outputs=[
        gr.Textbox(label="Results"),
        gr.File(label="Download Output")
    ],
    title="Hendrix Video Analysis",
    description="AI-powered video analysis and captioning"
)

if __name__ == "__main__":
    iface.launch()
EOF
            echo -e "${GREEN}Gradio app created: gradio_app.py${NC}"
            echo "To run: pip install gradio && python gradio_app.py"
        fi
        ;;
        
    9)
        echo -e "\n${YELLOW}Creating batch processing script...${NC}"
        cat > batch_process.sh << 'EOF'
#!/bin/bash
# Batch process multiple videos

INPUT_DIR="${1:-./input_videos}"
OUTPUT_DIR="${2:-./batch_output}"
PROFILE="${3:-fast}"

mkdir -p "$OUTPUT_DIR"

for video in "$INPUT_DIR"/*.{mp4,avi,mov,mkv}; do
    if [ -f "$video" ]; then
        echo "Processing: $video"
        python hendrix_pipeline.py --video "$video" --profile "$PROFILE" --output-dir "$OUTPUT_DIR/$(basename "$video" .${video##*.})"
    fi
done

echo "Batch processing complete!"
EOF
        chmod +x batch_process.sh
        echo -e "${GREEN}Batch script created: batch_process.sh${NC}"
        echo "Usage: ./batch_process.sh [input_dir] [output_dir] [profile]"
        ;;
        
    10)
        echo -e "\n${BLUE}Opening architecture documentation...${NC}"
        cat docs/GETTING_STARTED.md | less
        ;;
        
    11)
        echo -e "\n${BLUE}Available Models:${NC}"
        source hendrix_venv/bin/activate
        python -m hendrix_pipeline --list-models 2>/dev/null || echo "Run option 1 first to install dependencies"
        ;;
        
    12)
        echo -e "\n${BLUE}Example Use Cases:${NC}"
        echo ""
        echo "1. ${GREEN}Accessibility:${NC} Generate subtitles for videos"
        echo "   python hendrix_pipeline.py --video lecture.mp4 --output-formats srt"
        echo ""
        echo "2. ${GREEN}Content Analysis:${NC} Extract key moments and summaries"
        echo "   python hendrix_pipeline.py --video movie.mp4 --profile quality"
        echo ""
        echo "3. ${GREEN}Video Search:${NC} Make videos searchable by content"
        echo "   python hendrix_pipeline.py --video archive.mp4 --output-formats json"
        echo ""
        echo "4. ${GREEN}Social Media:${NC} Auto-generate captions for clips"
        echo "   python hendrix_pipeline.py --video clip.mp4 --profile fast"
        ;;
        
    0)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        ;;
esac

echo ""
echo "Press Enter to continue..."
read
exec "$0"