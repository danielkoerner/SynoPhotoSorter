import os
import shutil
from datetime import datetime
import logging
import sys
from typing import Optional

try:
    import exifread
except ImportError:
    print("Please install exifread: python3 -m pip install --user exifread")
    sys.exit(1)

# Dynamically determine current home directory
HOME_DIR = os.path.expanduser("~")

# Construct paths dynamically
SOURCE_FOLDER = os.path.join(HOME_DIR, 'Photos', 'MobileBackup')
RAW_BASE = os.path.join(HOME_DIR, 'Photos_RAW')
REGULAR_BASE = os.path.join(HOME_DIR, 'Photos')

# File extensions for different types of images/videos
RAW_EXTS = {'cr2', 'cr3', 'nef', 'arw', 'dng', 'raf', 'rw2'}
REGULAR_EXTS = {'jpg', 'jpeg', 'png', 'heic', 'mov', 'mp4', 'gif', 'avi', 'mpg', 'mpeg'}

# Synology specific directories to exclude
EXCLUDE_DIRS = {'@eaDir'}

logging.basicConfig(
    filename='photo_sorter.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

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
        logging.warning(f"Failed to read EXIF data for {path}: {e}")

    try:
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime)
    except Exception as e:
        logging.error(f"Failed to read file modification date for {path}: {e}")
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
    logging.info(f"Moved: {src} -> {dest_path}")

def main() -> None:
    """
    Main function that walks through the source folder and organizes photos/videos
    into date-based directory structure.
    """
    for root, dirs, files in os.walk(SOURCE_FOLDER):
        # Remove Synology @eaDir folders from the search list
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = file.lower().split('.')[-1]
            path = os.path.join(root, file)

            if ext in RAW_EXTS | REGULAR_EXTS:  # Using set union for faster lookup
                date_taken = get_date_taken(path)
                if not date_taken:
                    logging.warning(f"No date found, file skipped: {path}")
                    continue

                if ext in RAW_EXTS:
                    dest_folder = os.path.join(RAW_BASE,
                                             date_taken.strftime('%Y'),
                                             date_taken.strftime('%m'),
                                             date_taken.strftime('%d'))
                else:
                    dest_folder = os.path.join(REGULAR_BASE,
                                             date_taken.strftime('%Y'),
                                             date_taken.strftime('%Y-%m'),
                                             date_taken.strftime('%Y-%m-%d'))

                move_file(path, dest_folder)
            else:
                logging.info(f"Skipped file with unknown extension: {path}")

if __name__ == "__main__":
    main()
