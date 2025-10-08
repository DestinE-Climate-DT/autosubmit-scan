#!/bin/bash
# Quickstart Script for autosubmit-scan
#
# This script demonstrates a complete workflow:
# 1. Create a sample catalog
# 2. Generate test log files
# 3. Validate the catalog
# 4. Run a scan
# 5. View results
# 6. Export to markdown
#
# Usage: bash examples/quickstart.sh

set -e  # Exit on error

echo "=================================================="
echo "  Autosubmit-Scan Quickstart Demo"
echo "=================================================="
echo ""

# Configuration
DEMO_DIR="./quickstart_demo"
CATALOG_FILE="${DEMO_DIR}/demo_catalog.yaml"
LOG_DIR="${DEMO_DIR}/logs"
OUTPUT_DIR="${DEMO_DIR}/output"

# Step 1: Setup demo directory
echo "[1/7] Setting up demo directory..."
rm -rf "${DEMO_DIR}"
mkdir -p "${DEMO_DIR}"
mkdir -p "${LOG_DIR}"

# Step 2: Create a simple catalog
echo "[2/7] Creating demo catalog..."
cat > "${CATALOG_FILE}" << 'EOF'
version: "1.0.0"
schema_version: "1.0.0"

metadata:
  name: "Quickstart Demo Catalog"
  description: "Simple catalog for demonstration"
  author: "Quickstart Script"
  created: "2024-01-01T00:00:00+00:00"
  updated: "2024-01-01T00:00:00+00:00"

errors:
  error_keyword:
    id: "error_keyword"
    pattern:
      type: "regex"
      pattern: "ERROR|CRITICAL|FATAL"
      flags:
        - "IGNORECASE"
    files:
      - "quickstart_demo/logs/**/*.log"
    meaning: "Critical error detected in logs"
    suggestion: "Review the log file for details and take corrective action"
    context_lines: 3
    next_errors:
      - error_id: "check_severity"
        when:
          type: "always"
    metadata:
      severity: "high"
      tags:
        - "errors"
        - "monitoring"

  check_severity:
    id: "check_severity"
    pattern:
      type: "regex"
      pattern: "CRITICAL|FATAL"
      flags:
        - "IGNORECASE"
    files:
      - "quickstart_demo/logs/**/*.log"
    meaning: "High-severity error requires immediate attention"
    suggestion: "Escalate to on-call engineer"
    context_lines: 5
    next_errors: []
    metadata:
      severity: "critical"
      tags:
        - "escalation"

  warning_keyword:
    id: "warning_keyword"
    pattern:
      type: "regex"
      pattern: "WARNING|WARN"
      flags:
        - "IGNORECASE"
    files:
      - "quickstart_demo/logs/**/*.log"
    meaning: "Warning detected - potential issue"
    suggestion: "Monitor for related errors"
    context_lines: 2
    next_errors: []
    metadata:
      severity: "medium"
      tags:
        - "warnings"
EOF

echo "   Catalog created: ${CATALOG_FILE}"

# Step 3: Generate sample log files
echo "[3/7] Generating sample log files..."

cat > "${LOG_DIR}/app.log" << 'EOF'
2024-01-01 10:00:00 INFO Application started
2024-01-01 10:00:01 INFO Loading configuration
2024-01-01 10:00:02 WARNING Configuration file not found, using defaults
2024-01-01 10:00:05 INFO Processing data batch 1
2024-01-01 10:00:10 ERROR Failed to connect to database
2024-01-01 10:00:11 ERROR Connection timeout after 5 seconds
2024-01-01 10:00:12 INFO Retrying connection
2024-01-01 10:00:15 INFO Connected successfully
2024-01-01 10:00:20 CRITICAL Out of memory condition detected
2024-01-01 10:00:21 FATAL Application crashed
EOF

cat > "${LOG_DIR}/system.log" << 'EOF'
2024-01-01 09:55:00 INFO System initialized
2024-01-01 09:55:05 INFO Services starting
2024-01-01 10:00:00 WARNING High CPU usage detected
2024-01-01 10:00:05 INFO CPU usage normalized
2024-01-01 10:05:00 ERROR Disk space low on /var/log
2024-01-01 10:05:01 WARNING Only 5% disk space remaining
2024-01-01 10:10:00 INFO Cleanup job started
2024-01-01 10:10:10 INFO Freed 10GB of disk space
EOF

cat > "${LOG_DIR}/network.log" << 'EOF'
2024-01-01 10:00:00 INFO Network monitor started
2024-01-01 10:01:00 INFO All connections healthy
2024-01-01 10:02:00 WARNING Latency spike detected
2024-01-01 10:02:05 INFO Latency back to normal
2024-01-01 10:03:00 ERROR Connection refused from 192.168.1.100
2024-01-01 10:03:01 ERROR Retry failed
2024-01-01 10:03:02 CRITICAL Network segment unreachable
EOF

echo "   Generated 3 log files in ${LOG_DIR}/"

# Step 4: Validate catalog
echo "[4/7] Validating catalog..."
python -m src.cli.main validate "${CATALOG_FILE}"
echo ""

# Step 5: Run scan
echo "[5/7] Running error scan..."
python -m src.cli.main scan \
    --catalog "${CATALOG_FILE}" \
    --output "${OUTPUT_DIR}" \
    --cores 2
echo ""

# Step 6: Show report summary
echo "[6/7] Report Summary"
echo "=================================================="

if [ -f "${OUTPUT_DIR}/report.json" ]; then
    echo "   Report generated: ${OUTPUT_DIR}/report.json"

    # Extract summary stats using Python
    python3 << EOF
import json
with open("${OUTPUT_DIR}/report.json", "r") as f:
    report = json.load(f)

summary = report.get("summary", {})
print(f"   Total matches: {summary.get('totalMatches', 0)}")
print(f"   Error types: {summary.get('errorTypes', 0)}")
print(f"   Files scanned: {summary.get('filesScanned', 0)}")
print()
print("   Matches by error type:")
for match in report.get("hasPart", []):
    error_id = match.get("errorDefinition", "unknown")
    file_uri = match.get("url", "unknown")
    line = match.get("position", "?")
    text = match.get("text", "")[:50]
    print(f"     - {error_id} @ line {line}: {text}...")
EOF
else
    echo "   ERROR: Report not generated!"
    exit 1
fi

echo ""
echo "=================================================="

# Step 7: Export to Markdown
echo "[7/7] Exporting report to Markdown..."
python -m src.cli.main export \
    "${OUTPUT_DIR}/report.json" \
    --template markdown \
    --output "${DEMO_DIR}/report.md"

echo "   Markdown report: ${DEMO_DIR}/report.md"
echo ""

# Completion message
echo "=================================================="
echo "  Quickstart Demo Complete!"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  1. View interactive TUI:"
echo "     python -m src.cli.main view ${OUTPUT_DIR}/report.json"
echo ""
echo "  2. View Markdown report:"
echo "     cat ${DEMO_DIR}/report.md"
echo ""
echo "  3. Explore sample catalog:"
echo "     cat examples/sample_catalog.yaml"
echo ""
echo "  4. Read documentation:"
echo "     cat docs/USER_GUIDE.md"
echo ""
echo "Demo files location: ${DEMO_DIR}/"
echo "=================================================="
