import os
import time
import logging
from dotenv import load_dotenv
from config_modules.config import StorageConfig # Import config *after* load_dotenv

# Load .env to get storage directory location
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DashboardCleanup")

# --- Configuration ---
DASHBOARD_DIR = StorageConfig.DASHBOARDS_DIR
RETENTION_DAYS = 15
SECONDS_IN_DAY = 86400
# ---------------------

def cleanup():
    if not os.path.exists(DASHBOARD_DIR):
        logger.warning(f"Directory not found, skipping: {DASHBOARD_DIR}")
        return

    logger.info("--- Starting Dashboard Cleanup Task ---")

    now = time.time()
    cutoff = now - (RETENTION_DAYS * SECONDS_IN_DAY)

    files_deleted = 0
    files_kept = 0

    try:
        for filename in os.listdir(DASHBOARD_DIR):
            file_path = os.path.join(DASHBOARD_DIR, filename)

            if not filename.endswith(".html"):
                continue # Skip non-html files

            if os.path.isfile(file_path):
                try:
                    file_mod_time = os.path.getmtime(file_path)

                    if file_mod_time < cutoff:
                        os.remove(file_path)
                        logger.info(f"DELETED: {filename} (older than {RETENTION_DAYS} days)")
                        files_deleted += 1
                    else:
                        files_kept += 1

                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

    except Exception as e:
        logger.error(f"Error reading dashboard directory {DASHBOARD_DIR}: {e}")

    logger.info("--- Cleanup Task Complete ---")
    logger.info(f"Files Deleted: {files_deleted}")
    logger.info(f"Files Kept: {files_kept}")

if __name__ == "__main__":
    cleanup()