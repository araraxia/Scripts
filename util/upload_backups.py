
from pathlib import Path
from dotenv import load_dotenv
from flask import jsonify
import os, sys
from datetime import datetime

ROOT_PATH = Path(__file__).resolve().parent.parent.parent
if str(ROOT_PATH) not in sys.path:
    sys.path.append(str(ROOT_PATH))

from extras.gcloud_helper import GCloudBucket    

load_dotenv(ROOT_PATH / ".env")
backup_path = os.getenv("CALDERA_BACKUP_PATH", None)
backup_bucket = os.getenv("CALDERA_BACKUP_BUCKET", None)

def upload_backups(log):
    log.info("Starting backup upload process...")
    if not backup_path or not backup_bucket:
        log.error("CALDERA_BACKUP_PATH or CALDERA_BACKUP_BUCKET not set in environment.")
        return jsonify({"status": "error", "message": "Backup path or bucket not configured."}), 500

    bucket = GCloudBucket(bucket_name=backup_bucket, log=log)

    for backup_file in Path(backup_path).glob("*.tar.gz"):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination_blob = f"{now}/{backup_file.name}" or f"{now}/caldera_backup.tar.gz"
        try:
            log.info(f"Uploading {destination_blob} to bucket {backup_bucket}...")
            bucket.upload_to_bucket(
                source_file=str(backup_file),
                destination_blob=destination_blob,
            )
            log.info(f"Uploaded {backup_file} to {destination_blob} in bucket {backup_bucket}.")
            os.remove(backup_file)
            log.info(f"Removed local backup file {backup_file}.")
        except Exception as e:
            log.error(f"Failed to upload {backup_file}: {e}", exc_info=True)
            continue
    log.info("Backup upload process completed.")
    return jsonify({"status": "success", "message": "Backup upload process completed."}), 200