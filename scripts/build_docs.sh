#!/usr/bin/env bash
# Build autosubmit-scan documentation using Jupyter Book
#
# This script builds the documentation locally for testing and preview.
# It supports various build options and provides helpful error messages.
#
# Usage:
#   ./scripts/build_docs.sh [OPTIONS]
#
# Options:
#   --clean         Clean build artifacts before building
#   --clean-all     Clean build artifacts and cached notebook outputs
#   --execute       Force execute all notebooks
#   --skip-execute  Skip notebook execution
#   --verbose       Show verbose build output
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
BUILD_DIR="${DOCS_DIR}/_build"

# Default options
CLEAN=false
CLEAN_ALL=false
EXECUTE_NOTEBOOKS=""
VERBOSE=""
BUILDER=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN=true
            shift
            ;;
        --clean-all)
            CLEAN_ALL=true
            shift
            ;;
        --execute)
            # This forces notebooks to execute - handled by _config.yml
            shift
            ;;
        --skip-execute)
            # Skip notebook execution - handled by _config.yml
            shift
            ;;
        --verbose)
            VERBOSE="--verbose"
            shift
            ;;
        --help|-h)
            echo "Build autosubmit-scan documentation"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --clean         Clean build artifacts before building"
            echo "  --clean-all     Clean build artifacts and cached notebook outputs"
            echo "  --execute       Force execute all notebooks"
            echo "  --skip-execute  Skip notebook execution"
            echo "  --verbose       Show verbose build output"
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
echo -e "${BLUE}Building autosubmit-scan Documentation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if jupyter-book is installed
if ! command -v jupyter-book &> /dev/null; then
    echo -e "${RED}Error: jupyter-book is not installed${NC}"
    echo ""
    echo "Install with:"
    echo "  pip install -r ${DOCS_DIR}/requirements.txt"
    echo ""
    echo "Or using pixi:"
    echo "  pixi install"
    echo "  pixi run python -m pip install -r docs/requirements.txt"
    exit 1
fi

# Clean if requested
if [ "$CLEAN_ALL" = true ]; then
    echo -e "${YELLOW}Cleaning all build artifacts and cached outputs...${NC}"
    cd "${DOCS_DIR}"
    jupyter-book clean . --all
    echo -e "${GREEN}✓ Cleaned${NC}"
    echo ""
elif [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning build artifacts...${NC}"
    cd "${DOCS_DIR}"
    jupyter-book clean .
    echo -e "${GREEN}✓ Cleaned${NC}"
    echo ""
fi

# Check if source package is installed
if ! python -c "import src" 2>/dev/null; then
    echo -e "${YELLOW}Warning: 'src' module not found in Python path${NC}"
    echo "This may cause autodoc to fail. Install with:"
    echo "  pip install -e ."
    echo ""
fi

# Build the documentation
echo -e "${BLUE}Building documentation...${NC}"
echo "Docs directory: ${DOCS_DIR}"
echo "Build directory: ${BUILD_DIR}/html"
echo ""

cd "${DOCS_DIR}"

# Build command
BUILD_CMD="jupyter-book build . ${VERBOSE}"
echo "Running: ${BUILD_CMD}"
echo ""

if eval ${BUILD_CMD}; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Documentation built successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Output location: ${BUILD_DIR}/html/index.html"
    echo ""
    echo "To view the documentation:"
    echo "  ./scripts/preview_docs.sh"
    echo ""
    echo "Or open directly:"
    echo "  open ${BUILD_DIR}/html/index.html  # macOS"
    echo "  xdg-open ${BUILD_DIR}/html/index.html  # Linux"
    echo "  start ${BUILD_DIR}/html/index.html  # Windows"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Documentation build failed${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "Common issues:"
    echo ""
    echo "1. Module import errors:"
    echo "   pip install -e ."
    echo ""
    echo "2. Missing dependencies:"
    echo "   pip install -r docs/requirements.txt"
    echo ""
    echo "3. Notebook execution errors:"
    echo "   ./scripts/build_docs.sh --skip-execute"
    echo ""
    echo "4. For more details:"
    echo "   ./scripts/build_docs.sh --verbose"
    exit 1
fi
