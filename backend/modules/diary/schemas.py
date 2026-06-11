"""Schemas for the local diary module."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class DiaryEntryCreateRequest(BaseModel):
    title: str = Field(default="", max_length=120)
    content_markdown: str = Field(default="", max_length=20000)
    entry_date: Optional[date] = None
    mood: str = Field(default="", max_length=40)
    tags: List[str] = Field(default_factory=list)


class DiaryEntryUpdateRequest(BaseModel):
    title: str = Field(default="", max_length=120)
    content_markdown: str = Field(default="", max_length=20000)
    entry_date: Optional[date] = None
    mood: str = Field(default="", max_length=40)
    tags: List[str] = Field(default_factory=list)


class DiaryAttachment(BaseModel):
    id: int
    entry_id: int
    filename: str
    original_filename: str
    content_type: str
    file_size: int
    public_url: str
    created_at: str


class DiaryEntryListItem(BaseModel):
    id: int
    title: str
    content_excerpt: str = ""
    entry_date: str
    mood: str = ""
    tags: List[str] = Field(default_factory=list)
    image_count: int = 0
    created_at: str
    updated_at: str


class DiaryEntryDetail(BaseModel):
    id: int
    title: str
    content_markdown: str = ""
    entry_date: str
    mood: str = ""
    tags: List[str] = Field(default_factory=list)
    attachments: List[DiaryAttachment] = Field(default_factory=list)
    created_at: str
    updated_at: str


class DiaryEntryListResponse(BaseModel):
    entries: List[DiaryEntryListItem] = Field(default_factory=list)


class DiaryImageUploadResponse(BaseModel):
    attachment: DiaryAttachment
