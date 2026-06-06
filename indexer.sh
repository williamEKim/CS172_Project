# Usage: ./indexer.sh <output-dir>
# Example: ./indexer.sh processed
export PATH="$PATH:/Applications/Docker.app/Contents/Resources/bin"

OUTPUT_DIR=${1:-"processed"}

if ! command -v docker &> /dev/null; then
    echo "Docker is not installed or not in PATH."
    echo "WARNMING: Install Docker Desktop before running this script."
    exit 1
fi

docker info &> /dev/null
if [ $? -ne 0 ]; then
    echo "Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Directory '$OUTPUT_DIR' not found. Run main.py first to collect posts."
    exit 1
fi

if [ -z "$(ls -A "$OUTPUT_DIR"/*.jsonl 2>/dev/null)" ]; then
    echo "No .jsonl files found in '$OUTPUT_DIR'. Run main.py first."
    exit 1
fi

echo "Building Docker image..."
docker compose build

if [ $? -ne 0 ]; then
    echo "Docker build failed. Check your Dockerfile."
    exit 1
fi

echo ""
echo "Starting indexer with data from '$OUTPUT_DIR'..."
echo "Index will be saved to bluesky_index/"

docker compose run --rm \
    -e DATA_DIR="$OUTPUT_DIR" \
    app python3 pylucene.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Done. Index saved to bluesky_index/"
    echo "Executing the Web UI for searcher..."
    docker compose up
else
    echo ""
    echo "Indexer failed. Check the error above."
    exit 1
fi