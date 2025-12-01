# FPGA Bitstream Manager v2.0 - Installation Guide

## Overview
A web-based application for managing multiple FPGA bitstream files with offline Bootstrap support and real-time flash output display.

## What's New in v2.0
- ✨ **Multiple bitstream files** - Store and manage multiple .bit files simultaneously
- ✨ **Individual flash buttons** - Each file has its own flash button
- ✨ **Currently flashed display** - Clear indication of which file is currently active
- ✨ **Real-time output** - See the actual output from the loadfpga command
- ✨ **Better status tracking** - Visual indicators for active bitstream

## Files Included
```
fpga-manager/
├── fpga-manager.cgi          # Main CGI script
└── static/
    ├── css/
    │   ├── bootstrap.min.css
    │   └── bootstrap-icons.min.css
    └── fonts/
        ├── bootstrap-icons.woff
        └── bootstrap-icons.woff2
```

## Installation Steps

### 1. Create Required Directories
```bash
# Create FPGA bitstream directory
mkdir -p /fpgabit
chmod 755 /fpgabit

# Create state file directory (if needed)
mkdir -p /var/lib
touch /var/lib/fpga_flash_state
chmod 644 /var/lib/fpga_flash_state
```

### 2. Install Web Application Files

Option A - If your CGI directory is in your web root:
```bash
# Copy the entire fpga-manager directory to your web root
cp -r fpga-manager /var/www/htdocs/
chmod +x /var/www/htdocs/fpga-manager/fpga-manager.cgi
```

Option B - If CGI is in a separate directory:
```bash
# Copy CGI script to CGI directory
cp fpga-manager/fpga-manager.cgi /path/to/cgi-bin/
chmod +x /path/to/cgi-bin/fpga-manager.cgi

# Copy static files to web root
cp -r fpga-manager/static /var/www/htdocs/
```

### 3. Configure Lighttpd

Edit your lighttpd.conf to ensure:

```conf
# CGI configuration
cgi.assign = ( ".cgi" => "/bin/sh" )

# If using separate directories, ensure static files are accessible
# The CGI script expects static files at: ./static/css/ and ./static/fonts/
# relative to the CGI script location or accessible via the web server
```

### 4. Set Permissions

Ensure the web server can:
- Read the CGI script
- Execute the CGI script
- Read static files (CSS, fonts)
- Write to /fpgabit/
- Write to /var/lib/fpga_flash_state

```bash
# Example permissions
chown -R www-data:www-data /fpgabit
chmod 755 /fpgabit

chown www-data:www-data /var/lib/fpga_flash_state
chmod 644 /var/lib/fpga_flash_state
```

### 5. Verify Installation

Access the application:
```
http://your-server-ip/fpga-manager.cgi
```

## Features

- **Upload .bit files**: Drag and drop or click to select bitstream files
- **Multiple files**: Store as many .bit files as needed in /fpgabit/
- **File information**: Displays filename, size, and upload time for each file
- **Individual flash buttons**: Each bitstream has its own flash button
- **Delete buttons**: Remove unwanted files with a single click (with confirmation)
- **Currently flashed indicator**: Clear visual indication of which file is active
- **Real-time flash output**: See the complete output from loadfpga command
- **Flash history**: Tracks currently flashed file and timestamp
- **Offline ready**: All Bootstrap files included locally

## Usage Workflow

1. **Upload Files**: Upload one or more .bit files using the upload zone
2. **View Library**: All uploaded files are displayed in a list
3. **Flash FPGA**: Click the "Flash FPGA" button next to any file
4. **View Output**: See real-time output from the loadfpga command
5. **Track Status**: Currently flashed file is highlighted with a badge

## Flash Output Page

When you flash a file, you'll see:
- The filename being flashed
- The exact command being executed
- Real-time terminal output from loadfpga
- Success/failure status
- Exit code (if failed)
- Button to return to the main page

## State File Location

The application stores flash history in:
```
/var/lib/fpga_flash_state
```

This file persists across reboots (unlike /tmp) and contains:
- Currently flashed filename
- Timestamp of last flash operation

## File Management

This version:
- **KEEPS** all uploaded .bit files
- Does NOT delete files automatically on upload
- Allows you to maintain a library of bitstreams
- Each file can be flashed individually
- **Includes delete buttons** for easy file removal

To remove files:
- **Via web interface**: Click the red trash icon next to any file (confirmation required)
- **Via command line**: `rm /fpgabit/filename.bit`

## Troubleshooting

### Static files not loading
If CSS/icons don't load, verify the static files are in the correct location relative to the CGI script:
```bash
# From CGI script directory
ls -la static/css/
ls -la static/fonts/
```

### Upload fails
Check permissions on /fpgabit/:
```bash
ls -ld /fpgabit
# Should be writable by web server user
```

### Flash command not working
Verify `loadfpga` command is:
- In the system PATH
- Executable by the web server user
- Has proper permissions to access hardware

### Flash output not showing
- Ensure loadfpga outputs to stdout/stderr
- Check that the command completes (doesn't hang)
- Verify web server timeout settings

### State file issues
Check /var/lib/fpga_flash_state:
```bash
ls -la /var/lib/fpga_flash_state
# Should be writable by web server user
```

### Currently flashed indicator not showing
- Upload a file and flash it at least once
- Check that /var/lib/fpga_flash_state is writable
- Verify the state file contains valid data:
  ```bash
  cat /var/lib/fpga_flash_state
  ```

## Security Notes

- Only .bit files are accepted
- File uploads are restricted to /fpgabit/ directory
- The application runs with web server permissions
- Consider adding authentication if exposed to network
- Flash operations execute with web server user privileges

## Customization

To change storage locations, edit these variables in fpga-manager.cgi:
```bash
FPGA_DIR="/fpgabit"           # Bitstream storage
STATE_FILE="/var/lib/fpga_flash_state"  # Flash history
```

## Advanced Configuration

### Timeout Settings
If loadfpga takes a long time, you may need to increase CGI timeout in lighttpd.conf:
```conf
server.max-write-idle = 360
```

### File Size Limits
For large .bit files, ensure lighttpd is configured to accept them:
```conf
server.upload-dirs = ( "/tmp" )
server.max-request-size = 52428800  # 50MB
```

## Comparison with v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Multiple files | ❌ One at a time | ✅ Unlimited |
| Auto-delete old files | ✅ Yes | ❌ No (keeps all) |
| Flash output | ❌ No visibility | ✅ Real-time display |
| Currently flashed | ❌ Only last flash time | ✅ Full file info + highlight |
| Individual flash buttons | ❌ One global button | ✅ Per-file buttons |

## Example Use Cases

1. **Development**: Keep multiple bitstream versions and switch between them
2. **Testing**: Compare different FPGA configurations quickly
3. **Production**: Maintain stable releases and development builds
4. **Debugging**: Store known-good configurations alongside test versions
