import os
import shutil
from datetime import datetime
import logging
import sys
from typing import Optional, List
import logging.handlers
import glob

try:
    import exifread
except ImportError:
    print("Please install exifread: python3 -m pip install --user exifread")
    sys.exit(1)

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(SCRIPT_DIR, 'logs')

# Create logs directory if it doesn't exist
os.makedirs(LOGS_DIR, exist_ok=True)

# Dynamically determine current home directory
HOME_DIR = os.path.expanduser("~")

# Construct paths
SOURCE_FOLDERS = [
    os.path.join(HOME_DIR, 'Photos', 'MobileBackup'),
    os.path.join(HOME_DIR, 'Photos', 'PhotoLibrary')
]
PHOTOS_BASE = os.path.join(HOME_DIR, 'Photos')

# File extensions for different types of images/videos
MEDIA_EXTS = {'jpg', 'jpeg', 'png', 'heic', 'mov', 'mp4', 'gif', 'avi', 'mpg', 'mpeg',
              'cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'rw2'}

# Synology specific directories to exclude
EXCLUDE_DIRS = {'@eaDir'}

# System files to ignore when checking if directory is empty
IGNORE_FILES = {'Thumbs.db', '.DS_Store', '@eaDir'}

def cleanup_old_logs(max_logs: int = 30):
    """
    Clean up old log files, keeping only the most recent ones.
    
    Args:
        max_logs: Maximum number of log files to keep
    """
    log_files = glob.glob(os.path.join(LOGS_DIR, 'photo_sorter_*.log'))
    log_files.sort(reverse=True)  # Sort newest first
    
    # Remove old log files
    for old_log in log_files[max_logs:]:
        try:
            os.remove(old_log)
        except Exception as e:
            print(f"Failed to remove old log file {old_log}: {e}")

# Configure logging to output to both file and console
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a new log file with timestamp
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(LOGS_DIR, f'photo_sorter_{timestamp}.log')

# File handler
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(console_handler)

# Clean up old logs
cleanup_old_logs()

def get_date_taken(path: str) -> Optional[datetime]:
    """
    Extract the date when the photo/video was taken.
    First tries to read EXIF data, falls back to file modification time if EXIF is not available.

    Args:
        path: Path to the media file

    Returns:
        datetime object if date could be determined, None otherwise
    """
    try:
        with open(path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag='DateTimeOriginal', details=False)
            date_taken = tags.get('EXIF DateTimeOriginal')
            if date_taken:
                return datetime.strptime(str(date_taken), '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        logger.warning(f"Failed to read EXIF data for {path}: {e}")

    try:
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime)
    except Exception as e:
        logger.error(f"Failed to read file modification date for {path}: {e}")
        return None

def move_file(src: str, dest: str) -> None:
    """
    Move a file to destination, handling filename conflicts by adding a counter.

    Args:
        src: Source file path
        dest: Destination directory path
    """
    os.makedirs(dest, exist_ok=True)
    dest_path = os.path.join(dest, os.path.basename(src))

    if os.path.exists(dest_path):
        base, ext = os.path.splitext(os.path.basename(src))
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            new_dest_path = os.path.join(dest, new_name)
            if not os.path.exists(new_dest_path):
                dest_path = new_dest_path
                break
            counter += 1

    shutil.move(src, dest_path)
    logger.info(f"Moved: {src} -> {dest_path}")

def remove_empty_dirs(path: str) -> None:
    """
    Remove empty directories recursively from bottom up.
    Directories containing only system files (Thumbs.db, .DS_Store) or @eaDir
    are considered empty.
    
    Args:
        path: Starting path to check for empty directories
    """
    for root, dirs, files in os.walk(path, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                # Get directory contents, excluding system files
                contents = [f for f in os.listdir(dir_path) 
                          if f not in IGNORE_FILES and 
                          not any(f.startswith(ignore) for ignore in IGNORE_FILES)]
                
                if not contents:
                    try:
                        # Try to remove the directory and its contents
                        shutil.rmtree(dir_path)
                        logger.info(f"Removed directory with only system files: {dir_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove directory {dir_path}: {e}")
            except Exception as e:
                logger.warning(f"Failed to process directory {dir_path}: {e}")

def process_directory(source_dir: str) -> None:
    """
    Process a single source directory, organizing its photos/videos.

    Args:
        source_dir: Source directory to process
    """
    for root, dirs, files in os.walk(source_dir):
        # Remove Synology @eaDir folders from the search list
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = file.lower().split('.')[-1]
            path = os.path.join(root, file)

            if ext in MEDIA_EXTS:
                date_taken = get_date_taken(path)
                if not date_taken:
                    logger.warning(f"No date found, file skipped: {path}")
                    continue

                dest_folder = os.path.join(PHOTOS_BASE,
                                         date_taken.strftime('%Y'),
                                         date_taken.strftime('%m'))

                move_file(path, dest_folder)
            else:
                logger.info(f"Skipped file with unknown extension: {path}")
    
    # Clean up empty directories after processing
    remove_empty_dirs(source_dir)

def main() -> None:
    """
    Main function that walks through all source folders and organizes photos/videos
    into date-based directory structure.
    """
    for source_folder in SOURCE_FOLDERS:
        if os.path.exists(source_folder):
            logger.info(f"Processing directory: {source_folder}")
            process_directory(source_folder)
        else:
            logger.warning(f"Source folder does not exist: {source_folder}")

if __name__ == "__main__":
    main()
