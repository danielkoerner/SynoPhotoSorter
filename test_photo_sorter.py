import os
import pytest
from photo_sorter import get_date_taken, MEDIA_EXTS

def test_media_extensions():
    """Test that media extensions are properly defined"""
    assert isinstance(MEDIA_EXTS, set)
    assert 'jpg' in MEDIA_EXTS
    assert 'jpeg' in MEDIA_EXTS
    assert 'png' in MEDIA_EXTS

def test_get_date_taken_with_invalid_file():
    """Test handling of invalid files in get_date_taken"""
    result = get_date_taken("nonexistent_file.jpg")
    assert result is None 