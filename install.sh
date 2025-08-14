#!/bin/bash

# Hendrix Video Analysis Pipeline - One-Click Installer
# This script installs Hendrix with all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "🎬 Hendrix Video Analysis Pipeline"
echo "One-Click Installer"
echo "====================================="
echo -e "${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"

echo -e "🔍 Detecting system..."
echo -e "  OS: $OS"
echo -e "  Architecture: $ARCH"

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Error: Python 3 is not installed${NC}"
    echo -e "Please install Python 3.8+ and try again"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "  Python: $PYTHON_VERSION"

if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo -e "${GREEN}  ✓ Python version OK${NC}"
else
    echo -e "${RED}❌ Error: Python 3.8+ required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Check/Install FFmpeg
echo -e "\n📹 Checking FFmpeg..."
if command_exists ffmpeg; then
    echo -e "${GREEN}  ✓ FFmpeg found${NC}"
else
    echo -e "${YELLOW}  ⚠ FFmpeg not found. Installing...${NC}"
    
    if [[ "$OS" == "Linux" ]]; then
        if command_exists apt-get; then
            sudo apt-get update && sudo apt-get install -y ffmpeg
        elif command_exists yum; then
            sudo yum install -y ffmpeg
        elif command_exists pacman; then
            sudo pacman -S ffmpeg
        else
            echo -e "${RED}❌ Could not install FFmpeg automatically. Please install it manually.${NC}"
            exit 1
        fi
    elif [[ "$OS" == "Darwin" ]]; then
        if command_exists brew; then
            brew install ffmpeg
        else
            echo -e "${RED}❌ Please install Homebrew first, then run: brew install ffmpeg${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Unsupported OS for automatic FFmpeg installation${NC}"
        exit 1
    fi
fi

# Install method selection
echo -e "\n📦 Choose installation method:"
echo -e "  1) 🐍 pip install (recommended)"
echo -e "  2) 🔧 Development install (editable)"
echo -e "  3) 🐳 Docker setup"
echo -e ""

read -p "Select option [1-3]: " INSTALL_METHOD

case $INSTALL_METHOD in
    1)
        echo -e "\n${BLUE}Installing via pip...${NC}"
        pip install --upgrade pip
        
        # For now, install in development mode since we're not on PyPI yet
        pip install -e .
        ;;
    2)
        echo -e "\n${BLUE}Setting up development environment...${NC}"
        pip install --upgrade pip
        pip install -e ".[dev]"
        
        # Install pre-commit hooks if in a git repo
        if [ -d ".git" ]; then
            echo -e "Setting up pre-commit hooks..."
            pre-commit install || echo "Note: pre-commit hooks setup failed"
        fi
        ;;
    3)
        echo -e "\n${BLUE}Setting up Docker...${NC}"
        
        if ! command_exists docker; then
            echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
            exit 1
        fi
        
        # Build Docker image
        docker build -t hendrix-video .
        
        echo -e "${GREEN}✅ Docker image 'hendrix-video' built successfully!${NC}"
        echo -e "\nUsage:"
        echo -e "  docker run -v \$(pwd):/data hendrix-video analyze /data/video.mp4"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid selection${NC}"
        exit 1
        ;;
esac

# Verify installation
echo -e "\n🔍 Verifying installation..."
if python -c "import hendrix; print('✓ Hendrix imported successfully')" 2>/dev/null; then
    echo -e "${GREEN}✅ Package installation successful!${NC}"
else
    echo -e "${RED}❌ Package installation failed${NC}"
    exit 1
fi

# Run verification
echo -e "\n🔧 Running system verification..."
if hendrix verify; then
    echo -e "\n${GREEN}🎉 Installation completed successfully!${NC}"
else
    echo -e "\n${YELLOW}⚠ Installation completed with warnings${NC}"
    echo -e "Some optional dependencies may be missing"
fi

# Show next steps
echo -e "\n📚 Next steps:"
echo -e "  1. Test with a video:    ${BLUE}hendrix analyze video.mp4${NC}"
echo -e "  2. See all options:      ${BLUE}hendrix --help${NC}"
echo -e "  3. Check configuration:  ${BLUE}hendrix config${NC}"
echo -e "  4. List available models: ${BLUE}hendrix list-models${NC}"

echo -e "\n📖 Documentation: https://github.com/material-lab-io/HendrixVideo"
echo -e "🐛 Issues: https://github.com/material-lab-io/HendrixVideo/issues"

echo -e "\n${GREEN}Happy video analyzing! 🎬✨${NC}"