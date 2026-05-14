import io
import os
import uuid
from PIL import Image, UnidentifiedImageError
from flask import current_app

from errors import MyCamError

_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}
_MAX_DIM = 1024


class ImageService:
    @staticmethod
    def validate(file_storage):
        if not file_storage or not file_storage.filename:
            raise MyCamError("NO_FILE", "Missing image", 400)
        mime = (file_storage.mimetype or "").lower()
        if mime not in _ALLOWED_MIME:
            raise MyCamError("BAD_MIME", f"Unsupported format: {mime}", 400)

    @staticmethod
    def save_and_preprocess(user_id: int, file_storage) -> tuple[str, bytes, str]:
        """Save the source image (compressed to JPEG); returns (relative_path, image_bytes, mime)."""
        ImageService.validate(file_storage)
        upload_root = current_app.config["UPLOAD_FOLDER"]
        user_dir = os.path.join(upload_root, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        try:
            img = Image.open(file_storage.stream)
            img.load()
        except (UnidentifiedImageError, OSError) as e:
            raise MyCamError("BAD_IMAGE", f"Failed to read image: {e}", 400)

        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        # Resize
        img.thumbnail((_MAX_DIM, _MAX_DIM))

        filename = f"{uuid.uuid4().hex}.jpg"
        abs_path = os.path.join(user_dir, filename)
        img.save(abs_path, format="JPEG", quality=85, optimize=True)

        # bytes for AI
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        image_bytes = buf.getvalue()

        rel_path = f"/static/uploads/{user_id}/{filename}"
        return rel_path, image_bytes, "image/jpeg"
