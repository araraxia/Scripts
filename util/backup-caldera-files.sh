#!/usr/bin/bash

echo "Starting backup of Caldera files."

DEVICE_NAME="RIP_CALDERA"
OUTPUT_DIR="/mnt/..."
OUTPUT_FILE="$OUTPUT_DIR/${DEVICE_NAME}_backup_$(date +'%Y%m%d').tar.gz"
HOME_DIR="$HOME"

UPLOAD_ENDPOINT=""

INPUT_DIRS=(
    "/opt/caldera"
    "/etc"
    "$HOME_DIR"
    "/var/log"
)
EXCLUDE_DIRS=(
    "/opt/caldera/var/tmp/*"
    "/opt/caldera/var/jobs/*"
)

echo "Mounting all filesystemds in fstab."
mount -a

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Output directory missing after mounting, aborting."
    exit 1
fi

EXCLUDE_ARGS=()
for EXCLUDE_DIR in "${EXCLUDE_DIRS[@]}"; do
    EXCLUDE_ARGS+=("--exclude=$EXCLUDE_DIR")
done

INPUT_ARGS=()
for DIR in "${INPUT_DIRS[@]}"; do
    if [ -d "$DIR" ]; then
        INPUT_ARGS+=("$DIR")
    else
        echo "Warning: Input directory $DIR does not exist, skipping."
    fi
done


echo "Running backup command: tar ${EXCLUDE_ARGS[@]} -cvzf \"${OUTPUT_FILE}\" ${INPUT_ARGS[@]}"
tar "${EXCLUDE_ARGS[@]}" -cvzf "$OUTPUT_FILE" "${INPUT_ARGS[@]}"
if [ $? -eq 0 ]; then
    echo "Backup completed successfully: $OUTPUT_FILE"
    curl -X POST -H "Content-Type: application/json" -d "{\"status\":\"success\"}" $UPLOAD_ENDPOINT
else
    echo "Backup failed."
    exit 1
fi

echo "Backup script completed."
