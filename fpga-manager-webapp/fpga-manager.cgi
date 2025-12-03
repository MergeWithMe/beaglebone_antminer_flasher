#!/bin/sh

# FPGA Bitstream Manager CGI Script - Multiple Files Version
# Content type header
echo "Content-Type: text/html"
echo ""

# Configuration
FPGA_DIR="/fpgabit"
STATE_FILE="/fpgabit/fpga_flash_state"

# Function to get all .bit files
get_all_files() {
    ls "$FPGA_DIR"/*.bit 2>/dev/null
}

# Function to get file info
get_file_info() {
    local file="$1"
    if [ -f "$file" ]; then
        echo "$(basename "$file")|$(stat -c %s "$file" 2>/dev/null || stat -f %z "$file" 2>/dev/null)|$(stat -c %y "$file" 2>/dev/null | cut -d. -f1 || stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$file" 2>/dev/null)"
    fi
}

# Function to format bytes
format_bytes() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes} B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$((bytes / 1024)) KB"
    else
        echo "$((bytes / 1048576)) MB"
    fi
}

# Parse request method and handle POST
if [ "$REQUEST_METHOD" = "POST" ]; then
    echo "Handling POST request" > /fpgabit/upload_log.txt
    # Read content length
    CONTENT_LENGTH=${CONTENT_LENGTH:-0}

    echo "Content Length: $CONTENT_LENGTH" >> /fpgabit/upload_log.txt
    echo "Content Type: $CONTENT_TYPE" >> /fpgabit/upload_log.txt
    
    # Read POST data
    if [ $CONTENT_LENGTH -gt 0 ]; then
        # Check if this is a multipart upload or form data
        case "$CONTENT_TYPE" in
            *multipart/form-data*)
                # Handle file upload
                # Extract boundary
                BOUNDARY=$(echo "$CONTENT_TYPE" | sed 's/.*boundary=\(.*\)/\1/')
                echo "received multipart/form-data with boundary: $BOUNDARY" >> /fpgabit/upload_log.txt
                if [ -n "$BOUNDARY" ]; then
                    # Create temporary file for upload data
                    TEMP_FILE="/$FPGA_DIR/upload_$$"
                    dd bs=$CONTENT_LENGTH count=1 of="$TEMP_FILE" 2>/dev/null

                    # Extract filename from content
                    FILENAME=$(grep -aoP 'filename="\K[^"]+' "$TEMP_FILE" 2>/dev/null || \
                              grep -a "filename=" "$TEMP_FILE" | head -n 1 | \
                              sed 's/.*filename="\([^"]*\)".*/\1/' | \
                              sed 's/.*\\\([^\\]*\)$/\1/')

                    echo "extracted filename: $FILENAME" >> /fpgabit/upload_log.txt

                    mv "$TEMP_FILE" "$FPGA_DIR/$FILENAME"

                    # Strip multipart headers and boundaries to extract raw file data
                    # Find the boundary string
                    BOUNDARY_LINE="--$BOUNDARY"
                    # Find the start and end of the file data using grep and sed
                    START=$(grep -n "$BOUNDARY_LINE" "$TEMP_FILE" | head -n 1 | cut -d: -f1)
                    # Find the header end (empty line after boundary)
                    HEADER_END=$(tail -n +$((START+1)) "$TEMP_FILE" | grep -n '^$' | head -n 1 | cut -d: -f1)
                    DATA_START=$((START + HEADER_END))
                    # Find the next boundary (end of file data)
                    DATA_END=$(tail -n +$((DATA_START+1)) "$TEMP_FILE" | grep -n "$BOUNDARY_LINE" | head -n 1 | cut -d: -f1)
                    if [ -n "$DATA_START" ] && [ -n "$DATA_END" ]; then
                        sed -n "$((DATA_START+1)),$((DATA_START+DATA_END-1))p" "$TEMP_FILE" > "$FPGA_DIR/$FILENAME"
                        echo "extracted bitstream data to $FPGA_DIR/$FILENAME" >> /fpgabit/upload_log.txt
                    else
                        echo "Failed to extract file data from multipart upload" >> /fpgabit/upload_log.txt
                    fi
                  
                    echo "cleaning up temporary file" >> /fpgabit/upload_log.txt
                fi
                ;;
            *)
                # Regular form POST data
                POST_DATA=$(dd bs=1 count=$CONTENT_LENGTH 2>/dev/null)
                
                # Check if this is a delete request
                if echo "$POST_DATA" | grep -q "action=delete"; then
                    # Extract filename from POST data
                    DELETE_FILE=$(echo "$POST_DATA" | sed 's/.*filename=\([^&]*\).*/\1/' | sed 's/%2F/\//g' | sed 's/+/ /g')
                    
                    if [ -f "$DELETE_FILE" ]; then
                        rm -f "$DELETE_FILE"
                    fi
                fi
                
                # Check if this is a flash request
                if echo "$POST_DATA" | grep -q "action=flash"; then
                    # Extract filename from POST data
                    FLASH_FILE=$(echo "$POST_DATA" | sed 's/.*filename=\([^&]*\).*/\1/' | sed 's/%2F/\//g' | sed 's/+/ /g')
                    
                    if [ -f "$FLASH_FILE" ]; then
                        # Display header for flash output
                        cat << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flashing FPGA...</title>
    <link href="static/css/bootstrap.min.css" rel="stylesheet">
    <link href="static/css/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        @font-face {
            font-family: 'bootstrap-icons';
            src: url('static/fonts/bootstrap-icons.woff2') format('woff2'),
                 url('static/fonts/bootstrap-icons.woff') format('woff');
        }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        .main-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 2rem;
        }
        .output-box {
            background: #1e1e1e;
            color: #00ff00;
            padding: 1.5rem;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 400px;
            overflow-y: auto;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .success-msg {
            color: #28a745;
            font-weight: bold;
        }
        .error-msg {
            color: #dc3545;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="main-card">
                    <h2 class="mb-4"><i class="bi bi-lightning-charge"></i> Flashing FPGA</h2>
EOF
                        
                        echo "                    <p><strong>File:</strong> $(basename "$FLASH_FILE")</p>"
                        echo "                    <p class=\"mb-3\"><strong>Command:</strong> loadfpga $FLASH_FILE</p>"
                        echo "                    <h5 class=\"mt-4 mb-3\">Output:</h5>"
                        echo "                    <div class=\"output-box\">"
                        
                        # Execute flash command and capture output
                        FLASH_OUTPUT=$(loadfpga "$(basename "$FLASH_FILE")" 2>&1)
                        FLASH_RESULT=$?
                        
                        # Display output
                        echo "$FLASH_OUTPUT" | sed 's/</\&lt;/g' | sed 's/>/\&gt;/g'
                        
                        echo "                    </div>"
                        
                        if [ $FLASH_RESULT -eq 0 ]; then
                            echo "                    <div class=\"alert alert-success mt-3 success-msg\">"
                            echo "                        <i class=\"bi bi-check-circle\"></i> Flash completed successfully!"
                            echo "                    </div>"
                            # Save flash state
                            echo "$(basename "$FLASH_FILE")|$(date '+%Y-%m-%d %H:%M:%S')" > "$STATE_FILE"
                        else
                            echo "                    <div class=\"alert alert-danger mt-3 error-msg\">"
                            echo "                        <i class=\"bi bi-x-circle\"></i> Flash failed with exit code: $FLASH_RESULT"
                            echo "                    </div>"
                        fi
                        
                        cat << 'EOF'
                    <div class="text-center mt-4">
                        <a href="?" class="btn btn-primary btn-lg">
                            <i class="bi bi-arrow-left"></i> Back to Manager
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
EOF
                        exit 0
                    fi
                fi
                ;;
        esac
    fi
fi

# Get currently flashed info
CURRENT_FLASHED=""
CURRENT_FLASHED_TIME=""
if [ -f "$STATE_FILE" ]; then
    FLASH_INFO=$(cat "$STATE_FILE")
    CURRENT_FLASHED=$(echo "$FLASH_INFO" | cut -d'|' -f1)
    CURRENT_FLASHED_TIME=$(echo "$FLASH_INFO" | cut -d'|' -f2)
fi

# HTML Output
cat << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FPGA Bitstream Manager</title>
    <link href="static/css/bootstrap.min.css" rel="stylesheet">
    <link href="static/css/bootstrap-icons.min.css" rel="stylesheet">
    <style>
        @font-face {
            font-family: 'bootstrap-icons';
            src: url('static/fonts/bootstrap-icons.woff2') format('woff2'),
                 url('static/fonts/bootstrap-icons.woff') format('woff');
        }
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem 0;
        }
        .main-card {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .header-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px 15px 0 0;
            padding: 2rem;
        }
        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s;
            cursor: pointer;
        }
        .upload-zone:hover {
            border-color: #764ba2;
            background: #f8f9fa;
        }
        .upload-zone.uploading {
            border-color: #28a745;
            background: #f0fff4;
        }
        .bitstream-card {
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            transition: all 0.3s;
            background: white;
        }
        .bitstream-card:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .bitstream-card.active {
            border-left: 4px solid #28a745;
            background: #f0fff4;
        }
        .current-badge {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 0.4rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .btn-flash {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            font-weight: 600;
        }
        .btn-flash:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            color: white;
        }
        .btn-delete {
            background: #dc3545;
            border: none;
            color: white;
            font-weight: 600;
            margin-left: 0.5rem;
        }
        .btn-delete:hover {
            background: #c82333;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
            color: white;
        }
        .info-card {
            border-left: 4px solid #17a2b8;
            background: #e7f7f9;
            padding: 1rem;
            border-radius: 8px;
        }
        .no-files-msg {
            text-align: center;
            padding: 2rem;
            color: #6c757d;
        }
        .progress-container {
            display: none;
            margin-top: 1rem;
        }
        .progress {
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
        }
        .progress-bar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            font-weight: 600;
        }
        .upload-status {
            text-align: center;
            margin-top: 0.5rem;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <div class="main-card">
                    <div class="header-section">
                        <h1 class="mb-0"><i class="bi bi-cpu"></i> FPGA Bitstream Manager</h1>
                        <p class="mb-0 mt-2 opacity-75">Upload and manage multiple FPGA bitstream files</p>
                    </div>
                    
                    <div class="p-4">
                        <!-- Currently Flashed Section -->
EOF

if [ -n "$CURRENT_FLASHED" ]; then
    cat << EOF
                        <div class="mb-4">
                            <h4 class="mb-3"><i class="bi bi-check-circle-fill text-success"></i> Currently Flashed</h4>
                            <div class="info-card">
                                <div class="row align-items-center">
                                    <div class="col-md-8">
                                        <h5 class="mb-1"><i class="bi bi-file-binary-fill"></i> $CURRENT_FLASHED</h5>
                                        <p class="mb-0 text-muted"><small>Flashed: $CURRENT_FLASHED_TIME</small></p>
                                    </div>
                                    <div class="col-md-4 text-md-end mt-2 mt-md-0">
                                        <span class="current-badge">
                                            <i class="bi bi-lightning-charge-fill"></i> ACTIVE
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <hr class="my-4">
EOF
fi

cat << 'EOF'
                        <!-- Upload Section -->
                        <div class="mb-4">
                            <h4 class="mb-3"><i class="bi bi-cloud-upload"></i> Upload New Bitstream</h4>
                            <form method="POST" enctype="multipart/form-data" id="uploadForm">
                                <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
                                    <i class="bi bi-file-earmark-arrow-up" style="font-size: 3rem; color: #667eea;" id="uploadIcon"></i>
                                    <p class="mt-3 mb-2 fw-bold" id="uploadText">Click to select a .bit file</p>
                                    <p class="text-muted small" id="uploadSubtext">Multiple .bit files can be stored</p>
                                    <input type="file" id="fileInput" name="bitfile" accept=".bit" style="display: none;">
                                </div>
                                <div class="progress-container" id="progressContainer">
                                    <div class="progress">
                                        <div class="progress-bar" id="progressBar" role="progressbar" style="width: 0%">0%</div>
                                    </div>
                                    <div class="upload-status" id="uploadStatus">Uploading...</div>
                                </div>
                            </form>
                        </div>

                        <hr class="my-4">

                        <!-- Available Bitstreams -->
                        <div class="mb-3">
                            <h4 class="mb-3"><i class="bi bi-list-ul"></i> Available Bitstreams</h4>
EOF

# List all .bit files
BIT_FILES=$(get_all_files)
FILE_COUNT=0

if [ -n "$BIT_FILES" ]; then
    for file in $BIT_FILES; do
        FILE_COUNT=$((FILE_COUNT + 1))
        FILE_INFO=$(get_file_info "$file")
        FILE_NAME=$(echo "$FILE_INFO" | cut -d'|' -f1)
        FILE_SIZE=$(echo "$FILE_INFO" | cut -d'|' -f2)
        FILE_DATE=$(echo "$FILE_INFO" | cut -d'|' -f3)
        FILE_SIZE_FORMATTED=$(format_bytes $FILE_SIZE)
        
        # Check if this is the currently flashed file
        IS_CURRENT=""
        if [ "$FILE_NAME" = "$CURRENT_FLASHED" ]; then
            IS_CURRENT="active"
        fi
        
        cat << EOF
                            <div class="bitstream-card $IS_CURRENT">
                                <div class="row align-items-center">
                                    <div class="col-md-7">
                                        <h5 class="mb-1">
                                            <i class="bi bi-file-earmark-binary"></i> $FILE_NAME
EOF
        
        if [ "$FILE_NAME" = "$CURRENT_FLASHED" ]; then
            echo "                                            <span class=\"badge bg-success ms-2\"><i class=\"bi bi-check\"></i> Current</span>"
        fi
        
        cat << EOF
                                        </h5>
                                        <p class="mb-0 text-muted">
                                            <small><strong>Size:</strong> $FILE_SIZE_FORMATTED | <strong>Uploaded:</strong> $FILE_DATE</small>
                                        </p>
                                    </div>
                                    <div class="col-md-5 text-md-end mt-2 mt-md-0">
                                        <form method="POST" style="display: inline;">
                                            <input type="hidden" name="action" value="flash">
                                            <input type="hidden" name="filename" value="$file">
                                            <button type="submit" class="btn btn-flash">
                                                <i class="bi bi-lightning-charge"></i> Flash FPGA
                                            </button>
                                        </form>
                                        <form method="POST" style="display: inline;" onsubmit="return confirm('Delete $FILE_NAME?');">
                                            <input type="hidden" name="action" value="delete">
                                            <input type="hidden" name="filename" value="$file">
                                            <button type="submit" class="btn btn-delete btn-sm">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </form>
                                    </div>
                                </div>
                            </div>
EOF
    done
else
    cat << 'EOF'
                            <div class="no-files-msg">
                                <i class="bi bi-inbox" style="font-size: 3rem; color: #dee2e6;"></i>
                                <p class="mt-3 mb-0">No bitstream files available</p>
                                <p class="text-muted small">Upload a .bit file to get started</p>
                            </div>
EOF
fi

cat << EOF
                        </div>
                    </div>
                </div>
                
                <div class="text-center mt-3">
                    <p class="text-white small opacity-75">FPGA Bitstream Manager v2.0 | $FILE_COUNT file(s) available</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // File upload handling with progress indication
        document.getElementById('fileInput').addEventListener('change', function(e) {
            if (this.files.length > 0) {
                const file = this.files[0];
                const uploadZone = document.getElementById('uploadZone');
                const uploadIcon = document.getElementById('uploadIcon');
                const uploadText = document.getElementById('uploadText');
                const uploadSubtext = document.getElementById('uploadSubtext');
                const progressContainer = document.getElementById('progressContainer');
                const progressBar = document.getElementById('progressBar');
                const uploadStatus = document.getElementById('uploadStatus');
                const form = document.getElementById('uploadForm');
                
                // Show uploading state
                uploadZone.classList.add('uploading');
                uploadIcon.className = 'bi bi-hourglass-split';
                uploadText.textContent = 'Uploading: ' + file.name;
                uploadSubtext.textContent = 'Please wait, get a coffee! Saving to slow NAND flash.';
                progressContainer.style.display = 'block';
                
                // Create FormData and XMLHttpRequest for upload with progress
                const formData = new FormData(form);
                const xhr = new XMLHttpRequest();
                
                // Progress event
                xhr.upload.addEventListener('progress', function(e) {
                    if (e.lengthComputable) {
                        const percentComplete = Math.round((e.loaded / e.total) * 100);
                        progressBar.style.width = percentComplete + '%';
                        progressBar.textContent = percentComplete + '%';
                        uploadStatus.textContent = 'Uploading: ' + percentComplete + '%';
                    }
                });
                
                // Load event (upload complete)
                xhr.addEventListener('load', function() {
                    if (xhr.status === 200) {
                        progressBar.style.width = '100%';
                        progressBar.textContent = '100%';
                        uploadStatus.textContent = 'Upload complete! Refreshing...';
                        uploadStatus.style.color = '#28a745';
                        
                        // Redirect after a short delay
                        setTimeout(function() {
                            window.location.reload();
                        }, 1000);
                    } else {
                        uploadStatus.textContent = 'Upload failed!';
                        uploadStatus.style.color = '#dc3545';
                    }
                });
                
                // Error event
                xhr.addEventListener('error', function() {
                    uploadStatus.textContent = 'Upload failed!';
                    uploadStatus.style.color = '#dc3545';
                });
                
                // Send the request
                xhr.open('POST', window.location.href, true);
                xhr.send(formData);
                
                // Prevent default form submission
                e.preventDefault();
                return false;
            }
        });
    </script>
</body>
</html>
EOF
