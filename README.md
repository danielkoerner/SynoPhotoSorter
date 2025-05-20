# SynoPhotoSorter

A Python utility that automatically organizes photos and videos into a date-based directory structure. Works on Synology NAS and other systems.

## Features

- Sorts photos/videos based on EXIF date (falls back to file modification date)
- Handles RAW files (CR2, CR3, NEF, etc.) and regular media (JPG, PNG, HEIC, MP4, etc.)
- Creates year/month/day directory structure
- Handles file naming conflicts
- Skips Synology @eaDir folders
- Logs all operations

## Quick Start

1. Install dependency: `python3 -m pip install --user exifread`
2. Run: `python3 photo_sorter.py`

## Automation

- On Synology: Set up as a scheduled task in DSM Control Panel
- On other systems: Add to crontab, e.g.:
  ```bash
  0 2 * * * python3 /path/to/photo_sorter.py  # Runs daily at 2 AM
  ```

## Configuration

Edit these variables in the script if needed:
- `SOURCE_FOLDER`: Default `~/Photos/MobileBackup`
- `RAW_BASE`: Default `~/Photos_RAW`
- `REGULAR_BASE`: Default `~/Photos`

## License

GNU General Public License v3.0 