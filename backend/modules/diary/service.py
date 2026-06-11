"""Service boundary for the local diary module."""

import uuid
from datetime import date
from pathlib import Path
from typing import List, Optional

from fastapi import HTTPException, UploadFile

from core.config import settings
from modules.diary.repository import diary_repository
from modules.diary.schemas import (
    DiaryAttachment,
    DiaryEntryCreateRequest,
    DiaryEntryDetail,
    DiaryEntryListItem,
    DiaryEntryUpdateRequest,
)
from services.avatar_service import ALLOWED_EXTENSIONS


class DiaryService:
    def list_entries(
        self,
        *,
        user_id: int,
        keyword: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        mood: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[DiaryEntryListItem]:
        return diary_repository.list_entries(
            user_id=user_id,
            keyword=self._clean_optional(keyword),
            date_from=date_from,
            date_to=date_to,
            mood=self._clean_optional(mood),
            tag=self._clean_optional(tag),
            limit=limit,
            offset=offset,
        )

    def create_entry(self, *, user_id: int, request: DiaryEntryCreateRequest) -> DiaryEntryDetail:
        return diary_repository.create_entry(
            user_id=user_id,
            title=self._clean_text(request.title, max_length=120),
            content_markdown=self._clean_text(request.content_markdown, max_length=20000),
            entry_date=request.entry_date or date.today(),
            mood=self._clean_text(request.mood, max_length=40),
            tags=self._clean_tags(request.tags),
        )

    def get_entry(self, *, user_id: int, entry_id: int) -> DiaryEntryDetail:
        return diary_repository.get_entry(user_id=user_id, entry_id=entry_id)

    def update_entry(
        self,
        *,
        user_id: int,
        entry_id: int,
        request: DiaryEntryUpdateRequest,
    ) -> DiaryEntryDetail:
        return diary_repository.update_entry(
            user_id=user_id,
            entry_id=entry_id,
            title=self._clean_text(request.title, max_length=120),
            content_markdown=self._clean_text(request.content_markdown, max_length=20000),
            entry_date=request.entry_date or date.today(),
            mood=self._clean_text(request.mood, max_length=40),
            tags=self._clean_tags(request.tags),
        )

    def delete_entry(self, *, user_id: int, entry_id: int) -> int:
        return diary_repository.soft_delete_entry(user_id=user_id, entry_id=entry_id)

    async def save_image(self, *, user_id: int, entry_id: int, file: UploadFile) -> DiaryAttachment:
        self.get_entry(user_id=user_id, entry_id=entry_id)
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
                detail=f"图片不能超过 {settings.avatar_max_size_mb}MB",
            )
        if not data:
            raise HTTPException(status_code=400, detail="上传文件为空")

        filename = f"diary_{user_id}_{entry_id}_{uuid.uuid4().hex}{extension}"
        relative_dir = Path("diary") / "images"
        target_dir = settings.upload_dir / relative_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        try:
            target_path.write_bytes(data)
        except OSError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save diary image to {target_path}: {exc}",
            ) from exc

        public_url = f"/uploads/{(relative_dir / filename).as_posix()}"
        return diary_repository.create_attachment(
            user_id=user_id,
            entry_id=entry_id,
            filename=filename,
            original_filename=file.filename or "",
            content_type=file.content_type or "",
            file_size=len(data),
            storage_path=str(target_path),
            public_url=public_url,
        )

    def delete_image(self, *, user_id: int, image_id: int) -> int:
        return diary_repository.soft_delete_attachment(user_id=user_id, image_id=image_id)

    def _clean_text(self, value: str, *, max_length: int) -> str:
        cleaned = str(value or "").strip()
        if len(cleaned) > max_length:
            raise HTTPException(status_code=400, detail=f"字段长度不能超过 {max_length}")
        return cleaned

    def _clean_optional(self, value: Optional[str]) -> Optional[str]:
        cleaned = str(value or "").strip()
        return cleaned or None

    def _clean_tags(self, tags: List[str]) -> List[str]:
        result: List[str] = []
        for tag in tags:
            value = str(tag or "").strip()
            if not value or value in result:
                continue
            if len(value) > 30:
                raise HTTPException(status_code=400, detail="标签长度不能超过 30")
            result.append(value)
            if len(result) >= 20:
                break
        return result


diary_service = DiaryService()
