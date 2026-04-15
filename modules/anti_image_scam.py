import imagehash
from PIL import Image
import io
import aiohttp
import easyocr
import numpy as np

# Initialize OCR
reader = easyocr.Reader(['en'])

SCAM_KEYWORDS = ["voxwin", "mr beast", "mrbeast", "usdt", "crypto", "bonus", "withdrawal"]

async def is_scam_image(attachment):
    if not attachment.content_type or not attachment.content_type.startswith('image'):
        return False, None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status == 200:
                    img_data = await resp.read()
                    img_pil = Image.open(io.BytesIO(img_data))
                    
                    # OCR Check
                    img_np = np.array(img_pil)
                    results = reader.readtext(img_np)
                    detected_text = " ".join([res[1].lower() for res in results])
                    
                    for keyword in SCAM_KEYWORDS:
                        if keyword in detected_text:
                            return True, f"Detected: {keyword}"

                    current_hash = str(imagehash.dhash(img_pil))
                    return False, f"Hash: {current_hash}"
    except Exception as e:
        return False, f"ERROR: {e}"
    return False, None
