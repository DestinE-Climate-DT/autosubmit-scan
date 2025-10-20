#!/usr/bin/env bash
# Preview autosubmit-scan documentation in a web browser
#
# This script starts a local web server to preview the built documentation.
# It will automatically open your browser to view the documentation.
#
# Usage:
#   ./scripts/preview_docs.sh [OPTIONS]
#
# Options:
#   --port PORT     Port to serve on (default: 8000)
#   --no-browser    Don't automatically open browser
#   --help          Show this help message

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DOCS_DIR="${PROJECT_ROOT}/docs"
BUILD_DIR="${DOCS_DIR}/_build/html"

# Default options
PORT=8000
OPEN_BROWSER=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --no-browser)
            OPEN_BROWSER=false
            shift
            ;;
        --help|-h)
            echo "Preview autosubmit-scan documentation"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --port PORT     Port to serve on (default: 8000)"
            echo "  --no-browser    Don't automatically open browser"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Previewing Documentation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if documentation is built
if [ ! -d "${BUILD_DIR}" ]; then
    echo -e "${RED}Error: Documentation not built${NC}"
    echo ""
    echo "Build the documentation first:"
    echo "  ./scripts/build_docs.sh"
    exit 1
fi

if [ ! -f "${BUILD_DIR}/index.html" ]; then
    echo -e "${RED}Error: index.html not found${NC}"
    echo ""
    echo "Build the documentation first:"
    echo "  ./scripts/build_docs.sh"
    exit 1
fi

# Check if port is available
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Port ${PORT} is already in use${NC}"
    echo "Try using a different port:"
    echo "  $0 --port 8001"
    exit 1
fi

# Start the server
echo "Serving documentation from: ${BUILD_DIR}"
echo "URL: http://localhost:${PORT}"
echo ""
echo -e "${GREEN}Press Ctrl+C to stop the server${NC}"
echo ""

# Open browser if requested
if [ "$OPEN_BROWSER" = true ]; then
    # Detect OS and open browser
    sleep 1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "http://localhost:${PORT}" &
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open "http://localhost:${PORT}" &
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        # Windows
        start "http://localhost:${PORT}" &
    else
        echo -e "${YELLOW}Could not detect OS to open browser${NC}"
        echo "Open manually: http://localhost:${PORT}"
    fi
fi

# Start the HTTP server
cd "${BUILD_DIR}"
python -m http.server ${PORT}
