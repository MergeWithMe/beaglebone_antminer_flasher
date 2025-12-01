#!/bin/sh

# FPGA Manager v2.0 Installation Script
# Run this script to install the FPGA Bitstream Manager

echo "=========================================="
echo "FPGA Bitstream Manager v2.0 - Installation"
echo "=========================================="
echo ""
echo "New in v2.0:"
echo "  ✓ Multiple bitstream file support"
echo "  ✓ Individual flash buttons per file"
echo "  ✓ Real-time loadfpga output display"
echo "  ✓ Currently flashed file indicator"
echo ""

# Configuration - EDIT THESE PATHS AS NEEDED
WEB_ROOT="/var/www/htdocs"
CGI_DIR="$WEB_ROOT"
WEB_USER="www-data"  # Change to 'lighttpd' or 'http' if needed

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root"
    echo "Please run: sudo $0"
    exit 1
fi

echo "Step 1: Creating required directories..."
mkdir -p /fpgabit
mkdir -p /var/lib
chmod 755 /fpgabit
touch /var/lib/fpga_flash_state
chmod 644 /var/lib/fpga_flash_state
echo "✓ Directories created"
echo ""

echo "Step 2: Installing web application files..."
if [ ! -d "$WEB_ROOT" ]; then
    echo "WARNING: Web root directory $WEB_ROOT does not exist"
    echo "Please edit this script and set the correct WEB_ROOT path"
    exit 1
fi

# Copy files
cp -r fpga-manager "$WEB_ROOT/"
chmod +x "$WEB_ROOT/fpga-manager/fpga-manager.cgi"
echo "✓ Files copied to $WEB_ROOT/fpga-manager/"
echo ""

echo "Step 3: Setting permissions..."
# Try to set ownership (may fail if user doesn't exist)
if id "$WEB_USER" >/dev/null 2>&1; then
    chown -R "$WEB_USER:$WEB_USER" /fpgabit
    chown "$WEB_USER:$WEB_USER" /var/lib/fpga_flash_state
    echo "✓ Permissions set for user: $WEB_USER"
else
    echo "WARNING: User '$WEB_USER' not found"
    echo "Please manually set ownership of:"
    echo "  - /fpgabit"
    echo "  - /var/lib/fpga_flash_state"
fi
echo ""

echo "Step 4: Verifying installation..."
if [ -f "$WEB_ROOT/fpga-manager/fpga-manager.cgi" ]; then
    echo "✓ CGI script installed"
fi
if [ -f "$WEB_ROOT/fpga-manager/static/css/bootstrap.min.css" ]; then
    echo "✓ Bootstrap CSS found"
fi
if [ -f "$WEB_ROOT/fpga-manager/static/fonts/bootstrap-icons.woff2" ]; then
    echo "✓ Bootstrap Icons found"
fi
echo ""

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Ensure lighttpd is configured with:"
echo "   cgi.assign = ( \".cgi\" => \"/bin/sh\" )"
echo ""
echo "2. For large files or long flash times, consider:"
echo "   server.max-request-size = 52428800  # 50MB"
echo "   server.max-write-idle = 360         # 6 min timeout"
echo ""
echo "3. Restart lighttpd:"
echo "   systemctl restart lighttpd"
echo ""
echo "4. Access the application at:"
echo "   http://your-server-ip/fpga-manager/fpga-manager.cgi"
echo ""
echo "5. Verify 'loadfpga' command is available and executable"
echo ""
echo "What's new in v2.0:"
echo "  • Upload multiple .bit files (no auto-delete)"
echo "  • Each file has its own flash button"
echo "  • See real-time output from loadfpga"
echo "  • Clear indication of currently flashed file"
echo ""
echo "For troubleshooting, see README.md"
echo ""
