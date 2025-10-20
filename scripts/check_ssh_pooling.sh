#!/usr/bin/env bash
#
# check_ssh_pooling.sh - Verify SSH connection pooling configuration
#
# This script checks if SSH ControlMaster is configured correctly for
# efficient connection pooling when scanning remote files.
#
# Usage:
#   ./scripts/check_ssh_pooling.sh [hostname]
#
# Examples:
#   ./scripts/check_ssh_pooling.sh climatedt-wf
#   ./scripts/check_ssh_pooling.sh mn5

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Get hostname from argument or use default
HOSTNAME="${1:-climatedt-wf}"

echo "=========================================="
echo "SSH Connection Pooling Configuration Check"
echo "=========================================="
echo ""
info "Checking SSH configuration for host: $HOSTNAME"
echo ""

# Check 1: SSH config file exists
echo "[1/6] Checking SSH config file..."
if [[ -f ~/.ssh/config ]]; then
    success "SSH config file exists: ~/.ssh/config"
else
    warning "SSH config file not found: ~/.ssh/config"
    info "Creating minimal SSH config with ControlMaster settings..."
    mkdir -p ~/.ssh
    chmod 700 ~/.ssh
    cat > ~/.ssh/config << 'EOF'
# Connection multiplexing for autosubmit-scan
Host *
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 10m
EOF
    chmod 600 ~/.ssh/config
    success "Created ~/.ssh/config with ControlMaster settings"
fi
echo ""

# Check 2: ControlMaster setting
echo "[2/6] Checking ControlMaster setting..."
CONTROL_MASTER=$(ssh -G "$HOSTNAME" 2>/dev/null | grep -i '^controlmaster' | awk '{print $2}')
if [[ "$CONTROL_MASTER" == "auto" || "$CONTROL_MASTER" == "yes" ]]; then
    success "ControlMaster is enabled: $CONTROL_MASTER"
else
    error "ControlMaster is not enabled (current: ${CONTROL_MASTER:-none})"
    warning "Add to ~/.ssh/config:"
    echo "    Host *"
    echo "        ControlMaster auto"
fi
echo ""

# Check 3: ControlPath setting
echo "[3/6] Checking ControlPath setting..."
CONTROL_PATH=$(ssh -G "$HOSTNAME" 2>/dev/null | grep -i '^controlpath' | awk '{print $2}')
if [[ -n "$CONTROL_PATH" ]]; then
    success "ControlPath is set: $CONTROL_PATH"

    # Expand %C token if present
    if [[ "$CONTROL_PATH" == *"%C"* ]]; then
        info "ControlPath uses %C (hash of connection params) for unique sockets"
    fi
else
    error "ControlPath is not set"
    warning "Add to ~/.ssh/config:"
    echo "    Host *"
    echo "        ControlPath ~/.ssh/control-%C"
fi
echo ""

# Check 4: ControlPersist setting
echo "[4/6] Checking ControlPersist setting..."
CONTROL_PERSIST=$(ssh -G "$HOSTNAME" 2>/dev/null | grep -i '^controlpersist' | awk '{print $2}')
if [[ -n "$CONTROL_PERSIST" && "$CONTROL_PERSIST" != "no" ]]; then
    success "ControlPersist is enabled: $CONTROL_PERSIST"

    # Parse the duration
    if [[ "$CONTROL_PERSIST" =~ ^([0-9]+)([smhd]?)$ ]]; then
        DURATION="${BASH_REMATCH[1]}"
        UNIT="${BASH_REMATCH[2]:-s}"

        # Convert to seconds
        case "$UNIT" in
            s) SECONDS=$DURATION ;;
            m) SECONDS=$((DURATION * 60)) ;;
            h) SECONDS=$((DURATION * 3600)) ;;
            d) SECONDS=$((DURATION * 86400)) ;;
        esac

        # Recommend at least 10 minutes (600 seconds)
        if [[ $SECONDS -lt 600 ]]; then
            warning "ControlPersist is short ($CONTROL_PERSIST). Recommend ≥ 10m for typical scans."
        fi
    fi
else
    warning "ControlPersist is not enabled (connections will close immediately)"
    info "Add to ~/.ssh/config:"
    echo "    Host *"
    echo "        ControlPersist 10m"
fi
echo ""

# Check 5: SSH directory permissions
echo "[5/6] Checking SSH directory permissions..."
SSH_DIR_PERMS=$(stat -f "%Lp" ~/.ssh 2>/dev/null || stat -c "%a" ~/.ssh 2>/dev/null || echo "unknown")
if [[ "$SSH_DIR_PERMS" == "700" ]]; then
    success "SSH directory has correct permissions: 700"
else
    warning "SSH directory has unexpected permissions: $SSH_DIR_PERMS (expected 700)"
    info "Fix with: chmod 700 ~/.ssh"
fi
echo ""

# Check 6: Test actual connection (if hostname is reachable)
echo "[6/6] Testing SSH connection to $HOSTNAME..."
if ssh -O check "$HOSTNAME" 2>/dev/null; then
    success "Existing control master found for $HOSTNAME"
    info "Connection is already established and can be reused"

    # Show control socket info
    SOCKET=$(ssh -G "$HOSTNAME" 2>/dev/null | grep '^controlpath' | awk '{print $2}')
    if [[ -S "$SOCKET" ]]; then
        info "Control socket: $SOCKET"
        info "Socket age: $(find "$SOCKET" -printf '%Cr\n' 2>/dev/null || stat -f '%Sm' "$SOCKET" 2>/dev/null)"
    fi
else
    info "No existing control master for $HOSTNAME"

    # Try to connect
    if timeout 10 ssh -o BatchMode=yes -o ConnectTimeout=5 "$HOSTNAME" echo "test" &>/dev/null; then
        success "Successfully connected to $HOSTNAME"
        info "A control socket should now exist"

        # Check for control socket
        sleep 1
        if ssh -O check "$HOSTNAME" 2>/dev/null; then
            success "Control master is now active"
        else
            warning "Connection succeeded but control master not detected"
        fi
    else
        warning "Could not connect to $HOSTNAME (timeout or authentication failure)"
        info "This is okay if you're not currently able to reach the host"
        info "The configuration will work when the host is reachable"
    fi
fi
echo ""

# Summary
echo "=========================================="
echo "Summary"
echo "=========================================="

# Count issues
ISSUES=0

if [[ "$CONTROL_MASTER" != "auto" && "$CONTROL_MASTER" != "yes" ]]; then
    ((ISSUES++))
fi

if [[ -z "$CONTROL_PATH" ]]; then
    ((ISSUES++))
fi

if [[ -z "$CONTROL_PERSIST" || "$CONTROL_PERSIST" == "no" ]]; then
    ((ISSUES++))
fi

if [[ $ISSUES -eq 0 ]]; then
    echo ""
    success "SSH connection pooling is properly configured!"
    echo ""
    info "Your scans will benefit from:"
    echo "  • Shared connections across Snakemake processes"
    echo "  • Reduced connection overhead (44+ → 1-2 connections)"
    echo "  • Faster scan execution"
    echo "  • Lower risk of connection timeouts"
    echo ""
else
    echo ""
    warning "Found $ISSUES configuration issue(s)"
    echo ""
    info "Recommended ~/.ssh/config settings:"
    echo ""
    cat << 'EOF'
    Host *
        ControlMaster auto
        ControlPath ~/.ssh/control-%C
        ControlPersist 10m
EOF
    echo ""
    info "Add these settings to ~/.ssh/config and run this script again"
    echo ""
fi

echo "For more information, see: docs/SSH_CONNECTION_POOLING.md"
echo ""
