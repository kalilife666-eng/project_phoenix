# Copyright project_phoenix
"""
Metadata Stripper Module
Anonymizes images, videos, and audio by removing EXIF, XMP, and other tags.
Uses Pillow for images and Mutagen for audio/video basic tags.
For thorough video stripping, ffmpeg is recommended.
"""

import os
from PIL import Image
from mutagen import File as MutagenFile

class MetadataStripper:
    """Handles stripping of metadata from various media formats."""

    def strip_image_metadata(self, input_path, output_path=None):
        """
        Removes all metadata (EXIF, IPTC, etc.) from an image.
        """
        if output_path is None:
            output_path = input_path
            
        try:
            with Image.open(input_path) as img:
                data = list(img.getdata())
                image_without_exif = Image.new(img.mode, img.size)
                image_without_exif.putdata(data)
                image_without_exif.save(output_path)
            return True, f"Metadata stripped from {input_path}"
        except Exception as e:
            return False, f"Failed to strip image metadata: {str(e)}"

    def strip_media_tags(self, input_path):
        """
        Removes metadata tags from audio and some video files using Mutagen.
        Works for MP3, FLAC, M4A, MP4, etc.
        """
        try:
            audio = MutagenFile(input_path)
            if audio is not None:
                audio.delete()
                audio.save()
                return True, f"Tags deleted from {input_path}"
            return False, "Unsupported media format for Mutagen"
        except Exception as e:
            return False, f"Failed to strip media tags: {str(e)}"

    def strip_file(self, file_path, output_path=None):
        """
        Generic entry point to strip metadata based on file extension.
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.tiff']:
            return self.strip_image_metadata(file_path, output_path)
        elif ext in ['.mp3', '.m4a', '.mp4', '.flac', '.ogg', '.wav']:
            # Note: mutagen strips tags but doesn't re-encode. 
            # Re-encoding with ffmpeg is safer for video.
            return self.strip_media_tags(file_path)
        else:
            return False, f"Unsupported file type: {ext}"

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python metadata_stripper.py <file_path>")
        sys.exit(1)
    
    stripper = MetadataStripper()
    success, msg = stripper.strip_file(sys.argv[1])
    print(msg)
