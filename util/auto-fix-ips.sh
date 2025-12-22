
OLD_IP="192.168.0"
NEW_IP="172.16.1"

USER_HOME_DIR="$HOME"
SEARCH_DIR="$USER_HOME_DIR/.cas"
SEARCH_DIR2="$USER_HOME_DIR/.config"
SEARCH_DIR3="C:/Code/Automation"
#SEARCH_DIR4="C:/API"

echo "USER_HOME_DIR: $USER_HOME_DIR"
echo "Searching in $SEARCH_DIR and $SEARCH_DIR2"

preview_changes() {
    echo "Previewing changes in $1"
    echo "Lines that will be changed:"
    echo "BEFORE:"
    grep -n "$OLD_IP" "$1" 2>/dev/null | while read -r line; do
        echo "  $line"
    done
    echo "AFTER:"
    grep -n "$OLD_IP" "$1" 2>/dev/null | sed "s/$OLD_IP/$NEW_IP/g" | while read -r line; do
        echo "  $line"
    done
    echo
}

is_text_file() {
    local file="$1"
    # Use file command to check if it's text
    file_type=$(file -b --mime-type "$file" 2>/dev/null)
    [[ $file_type == text/* ]] || [[ $file_type == application/json ]] || [[ $file_type == application/xml ]]
}

find_changes() {
    local processed=0
    local errors=0
    local log_file="auto-fix-ips-$(date +%Y%m%d_%H%M%S).log"

    echo "Finding files in $1 that contain $OLD_IP"
    while IFS= read -r -d '' file; do
        if ! is_text_file "$file"; then
            continue
        fi

        if grep -q "$OLD_IP" "$file" 2>/dev/null; then
            echo "==============================================="
            preview_changes "$file"

            read -p "Apply changes to this $file? (y/n): " -r response </dev/tty

            echo
            case $response in
                [Yy]* ) 
                    cp "$file" "$file.bak"
                    if sed -i "s/$OLD_IP/$NEW_IP/g" "$file"; then
                        echo "Updated $file (backup at $file.bak)"
                        echo "$(date +%F_%T) - Updated: $file" >> "$log_file"
                        ((processed++))
                    else
                        echo "Error updating $file"
                        echo "$(date +%F_%T) - Error updating: $file" >> "$log_file"
                        ((errors++))
                    fi
                    ;;
                * ) 
                    echo "Skipped $file"
                    echo "$(date +%F_%T) - Skipped: $file" >> "$log_file"
                    ;;
            esac
            echo "---"
            echo
        fi
    done < <(find "$1" -type f \
        ! -name "*.pyc" \
        ! -name "*pyo" \
        ! -name "*.so" \
        ! -name "__pycache__" \
        ! -path "*/.git/*" \
        ! -path "*/__pycache__/*" \
        ! -path "*/node_modules/*" \
        -print0 2>/dev/null)
}

revert_backups() {
    local reverted=0
    local errors=0
    local log_file="auto-fix-ips-revert-$(date +%Y%m%d_%H%M%S).log"
    
    echo "Finding .bak files in $1 to revert..."
    
    while IFS= read -r -d '' bakfile; do
        # Get the original filename by removing .bak extension
        original_file="${bakfile%.bak}"
        
        if [[ -f "$original_file" ]]; then
            echo "Found backup: $bakfile"
            echo "  -> Will restore to: $original_file"
            
            read -p "Revert $original_file from backup? (y/n): " -r response </dev/tty
            
            case $response in
                [Yy]* ) 
                    if mv "$bakfile" "$original_file"; then
                        echo "✓ Reverted: $original_file"
                        echo "$(date +%F_%T) - Reverted: $original_file" >> "$log_file"
                        ((reverted++))
                    else
                        echo "✗ Error reverting: $original_file"
                        echo "$(date +%F_%T) - Error reverting: $original_file" >> "$log_file"
                        ((errors++))
                    fi
                    ;;
                * ) 
                    echo "✗ Skipped: $original_file"
                    echo "$(date +%F_%T) - Skipped: $original_file" >> "$log_file"
                    ;;
            esac
            echo "---"
        else
            echo "Warning: Backup file $bakfile found but original $original_file doesn't exist"
            echo "$(date +%F_%T) - Warning: Orphaned backup: $bakfile" >> "$log_file"
        fi
    done < <(find "$1" -name "*.bak" -type f -print0 2>/dev/null)
    
    echo
    echo "Revert Summary:"
    echo "  Reverted: $reverted files"
    echo "  Errors: $errors files"
    echo "  Log file: $log_file"
    echo
}

package_backups() {
    local backup_count=0
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local tarball_name="ip-change-backups-$timestamp.tar.gz"
    local temp_dir="/tmp/backup_collection_$$"
    local log_file="auto-fix-ips-package-$timestamp.log"
    
    echo "Collecting .bak files from $1..."
    
    # Create temporary directory for organizing backups
    mkdir -p "$temp_dir"
    
    # Find and copy all .bak files
    while IFS= read -r -d '' bakfile; do
        # Create relative path structure in temp directory
        relative_path=$(realpath --relative-to="$1" "$bakfile" 2>/dev/null || echo "${bakfile#$1/}")
        target_dir="$temp_dir/$(dirname "$relative_path")"
        
        mkdir -p "$target_dir"
        
        if cp "$bakfile" "$target_dir/"; then
            echo "  Added: $bakfile"
            echo "$(date +%F_%T) - Added to archive: $bakfile" >> "$log_file"
            ((backup_count++))
        else
            echo "  Error copying: $bakfile"
            echo "$(date +%F_%T) - Error copying: $bakfile" >> "$log_file"
        fi
    done < <(find "$1" -name "*.bak" -type f -print0 2>/dev/null)
    
    if [[ $backup_count -gt 0 ]]; then
        echo
        echo "Creating compressed archive: $tarball_name"
        
        # Create tarball from temp directory
        if tar -czf "$tarball_name" -C "$temp_dir" . 2>/dev/null; then
            echo "✓ Successfully created: $tarball_name"
            echo "✓ Archive contains $backup_count backup files"
            
            # Show archive contents
            echo
            echo "Archive contents:"
            tar -tzf "$tarball_name" | head -10
            if [[ $(tar -tzf "$tarball_name" | wc -l) -gt 10 ]]; then
                echo "  ... and $(($(tar -tzf "$tarball_name" | wc -l) - 10)) more files"
            fi
            
            # Show file size
            archive_size=$(ls -lh "$tarball_name" | awk '{print $5}')
            echo "✓ Archive size: $archive_size"
            echo "$(date +%F_%T) - Created archive: $tarball_name ($backup_count files, $archive_size)" >> "$log_file"
        else
            echo "✗ Error creating archive"
            echo "$(date +%F_%T) - Error creating archive: $tarball_name" >> "$log_file"
        fi
    else
        echo "No .bak files found in $1"
        echo "$(date +%F_%T) - No .bak files found in: $1" >> "$log_file"
    fi
    
    # Cleanup temp directory
    rm -rf "$temp_dir"
    
    echo
    echo "Package Summary:"
    echo "  Files packaged: $backup_count"
    echo "  Archive: $tarball_name"
    echo "  Log file: $log_file"
    echo
}

# Update IP addresses in .cas files
echo "Directory update script started."
echo "Select directories:"
echo "1) $SEARCH_DIR"
echo "   $SEARCH_DIR2"
echo "2) $SEARCH_DIR3"
echo "3) Revert .bak files (undo changes)"
echo "4) Package .bak files into tarball"
#echo "2) $SEARCH_DIR4"
read -p "Update set 1, 2, revert (3), or package (4)? (1/2/3/4): " dir_choice
if [[ $dir_choice == "1" ]]; then
    find_changes "$SEARCH_DIR"
    find_changes "$SEARCH_DIR2"
elif [[ $dir_choice == "2" ]]; then
    find_changes "$SEARCH_DIR3"
    #find_changes "$SEARCH_DIR4"
elif [[ $dir_choice == "3" ]]; then
    echo "Revert mode selected."
    echo "Select directory to revert:"
    echo "1) $SEARCH_DIR and $SEARCH_DIR2"
    echo "2) $SEARCH_DIR3"
    read -p "Revert set 1 or 2? (1/2): " revert_choice
    if [[ $revert_choice == "1" ]]; then
        revert_backups "$SEARCH_DIR"
        revert_backups "$SEARCH_DIR2"
    elif [[ $revert_choice == "2" ]]; then
        revert_backups "$SEARCH_DIR3"
    else
        echo "Invalid choice, exiting."
        exit 1
    fi
elif [[ $dir_choice == "4" ]]; then
    echo "Package mode selected."
    echo "Select directory to package backups from:"
    echo "1) $SEARCH_DIR and $SEARCH_DIR2"
    echo "2) $SEARCH_DIR3"
    read -p "Package set 1 or 2? (1/2): " package_choice
    if [[ $package_choice == "1" ]]; then
        package_backups "$SEARCH_DIR"
        package_backups "$SEARCH_DIR2"
    elif [[ $package_choice == "2" ]]; then
        package_backups "$SEARCH_DIR3"
    else
        echo "Invalid choice, exiting."
        exit 1
    fi
else
    echo "Invalid choice, exiting."
    exit 1
fi

echo "Script completed."