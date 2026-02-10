import logging
import os
from typing import Optional

from mutagen.mp3 import MP3  # type: ignore
from mutagen.id3 import ID3, APIC, ID3NoHeaderError, TIT2, TPE1  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_cover_art(mp3_path: str) -> Optional[bytes]:
    """Extracts the cover art image data from an MP3 file's ID3 tags.

    Args:
        mp3_path: The absolute path to the MP3 file.

    Returns:
        The binary image data if found, otherwise None.

    Raises:
        FileNotFoundError: If the MP3 file does not exist.
    """
    if not os.path.exists(mp3_path):
        logger.error(f"File not found: {mp3_path}")
        raise FileNotFoundError(f"File not found: {mp3_path}")

    try:
        audio = MP3(mp3_path, ID3=ID3)
    except ID3NoHeaderError:
        logger.warning(f"No ID3 header found for {mp3_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading MP3 file {mp3_path}: {e}")
        return None

    # Check for existing ID3 tags
    if audio.tags:
        for tag in audio.tags.values():
            if isinstance(tag, APIC):
                logger.info(f"Found existing cover art in {mp3_path}")
                return tag.data
    
    logger.info(f"No cover art found in {mp3_path}")
    return None


def embed_cover_art(mp3_path: str, image_path: str) -> None:
    """Embeds an image as the cover art (APIC frame) into an MP3 file.

    Args:
        mp3_path: The absolute path to the MP3 file.
        image_path: The absolute path to the image file.

    Raises:
        FileNotFoundError: If either the MP3 or image file does not exist.
        ValueError: If the image format is not supported (only jpeg/png are typical).
    """
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"MP3 file not found: {mp3_path}")
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        audio = MP3(mp3_path, ID3=ID3)
        
        # Add ID3 tag if it doesn't exist
        try:
            audio.add_tags()
        except Exception:
            pass # Tags probably already exist

        with open(image_path, 'rb') as img:
            image_data = img.read()

        # Determine MIME type based on extension
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            mime = 'image/jpeg'
        elif ext == '.png':
            mime = 'image/png'
        else:
            logger.warning(f"Unknown image extension {ext}, defaulting to image/jpeg")
            mime = 'image/jpeg'

        # Create APIC frame
        # 3 is "Front Cover"
        apic = APIC(
            encoding=3, # 3 is UTF-8
            mime=mime,
            type=3, 
            desc='Cover',
            data=image_data
        )

        # Remove existing APIC frames (optional, but good practice to allow replacement)
        audio.tags.delall("APIC")
        
        audio.tags.add(apic)
        audio.save(v2_version=3)
        logger.info(f"Successfully embedded {image_path} into {mp3_path} (ID3v2.3)")

    except Exception as e:
        logger.error(f"Failed to embed cover art: {e}")
        raise

def get_metadata(mp3_path: str) -> dict[str, Optional[str]]:
    """Retrieves Title and Artist metadata from an MP3 file.
    
    Args:
        mp3_path: The absolute path to the MP3 file.
        
    Returns:
        A dictionary with keys 'title' and 'artist', containing the tag values or None.
    """
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"File not found: {mp3_path}")

    try:
        audio = MP3(mp3_path, ID3=ID3)
    except ID3NoHeaderError:
        return {'title': None, 'artist': None}
    except Exception as e:
        logger.error(f"Error reading metadata from {mp3_path}: {e}")
        return {'title': None, 'artist': None}

    title = None
    if audio.tags and 'TIT2' in audio.tags:
        title = audio.tags['TIT2'].text[0]

    artist = None
    if audio.tags and 'TPE1' in audio.tags:
        artist = audio.tags['TPE1'].text[0]
        
    return {'title': title, 'artist': artist}

def set_metadata(mp3_path: str, title: str, artist: str) -> None:
    """Sets the Title (TIT2) and Artist (TPE1) tags for an MP3 file.
    
    Args:
        mp3_path: The absolute path to the MP3 file.
        title: The title text.
        artist: The artist text.
    """
    if not os.path.exists(mp3_path):
        raise FileNotFoundError(f"File not found: {mp3_path}")

    try:
        audio = MP3(mp3_path, ID3=ID3)
        
        try:
            audio.add_tags()
        except Exception:
            pass 

        # encoding=3 is UTF-8
        audio.tags.add(TIT2(encoding=3, text=title))
        audio.tags.add(TPE1(encoding=3, text=artist))
        
        audio.save(v2_version=3)
        logger.info(f"Updated metadata for {mp3_path}: Title='{title}', Artist='{artist}'")
        
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        raise
