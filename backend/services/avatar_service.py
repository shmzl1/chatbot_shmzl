import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from core.config import settings


ALLOWED_EXTENSIONS = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}


class AvatarService:
    async def save_avatar(self, *, file: UploadFile, owner_id: str, category: str) -> str:
        extension = Path(file.filename or "").suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="只允许上传 png、jpg、jpeg、webp 图片")
        if file.content_type not in set(ALLOWED_EXTENSIONS.values()):
            raise HTTPException(status_code=400, detail="文件类型不是受支持的图片")

        data = await file.read()
        max_bytes = settings.avatar_max_size_mb * 1024 * 1024
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"头像不能超过 {settings.avatar_max_size_mb}MB",
            )
        if not data:
            raise HTTPException(status_code=400, detail="上传文件为空")

        safe_owner = "".join(ch for ch in owner_id if ch.isalnum() or ch in ("-", "_")) or "avatar"
        filename = f"{safe_owner}_{uuid.uuid4().hex}{extension}"
        relative_dir = Path("avatars") / category
        target_dir = settings.upload_dir / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        target_path.write_bytes(data)
        public_path = (relative_dir / filename).as_posix()
        return f"/uploads/{public_path}"


avatar_service = AvatarService()
