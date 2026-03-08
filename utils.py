from PIL import Image
import os

def resize_image(input_path, max_size=(1024, 1024)):
    """Resize image to fit Telegram's limits while preserving aspect ratio"""
    try:
        with Image.open(input_path) as img:
            # Create output filename
            filename, ext = os.path.splitext(input_path)
            output_path = f"{filename}_resized{ext}"

            # Resize image
            img.thumbnail(max_size)
            img.save(output_path, quality=85, optimize=True)

            return output_path
    except Exception as e:
        print(f"Error resizing image: {e}")
        return None
