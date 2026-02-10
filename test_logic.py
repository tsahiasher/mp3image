import os
import shutil
import logging
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1

# Mock audio_handler import locally
import audio_handler

# Create a dummy MP3 file (valid header)
DUMMY_MP3 = "test_audio.mp3"
with open(DUMMY_MP3, "wb") as f:
    # 10 frames of silence (MPEG 1 Layer 3)
    f.write(b'\xFF\xFB\x90\x00' * 10)

def test_metadata():
    print("Testing Metadata...")
    # 1. Test set_metadata
    audio_handler.set_metadata(DUMMY_MP3, "Test Title", "Test Artist")
    
    # Verify directly
    audio = MP3(DUMMY_MP3, ID3=ID3)
    print(f"Direct Read: Title={audio.tags['TIT2']}, Artist={audio.tags['TPE1']}")
    assert str(audio.tags['TIT2']) == "Test Title"
    assert str(audio.tags['TPE1']) == "Test Artist"

    # 2. Test get_metadata
    meta = audio_handler.get_metadata(DUMMY_MP3)
    print(f"get_metadata: {meta}")
    assert meta['title'] == "Test Title"
    assert meta['artist'] == "Test Artist"
    
    # 3. Test Hebrew
    hebrew_title = "כותרת בדיקה"
    hebrew_artist = "אמן בדיקה"
    audio_handler.set_metadata(DUMMY_MP3, hebrew_title, hebrew_artist)
    meta = audio_handler.get_metadata(DUMMY_MP3)
    print(f"Hebrew Test: {meta}")
    assert meta['title'] == hebrew_title
    assert meta['artist'] == hebrew_artist
    
    print("Metadata tests passed!")

try:
    test_metadata()
except Exception as e:
    print(f"Test Failed: {e}")
finally:
    if os.path.exists(DUMMY_MP3):
        os.remove(DUMMY_MP3)
