"""Diary context builder used only when the user explicitly selects a diary."""

from modules.diary.service import diary_service


def build_diary_context_for_chat(*, user_id: int, entry_id: int) -> str:
    entry = diary_service.get_entry(user_id=user_id, entry_id=entry_id)
    tags = "、".join(entry.tags) if entry.tags else "无"
    image_lines = []
    for attachment in entry.attachments:
        image_lines.append(
            f"- {attachment.original_filename or attachment.filename} ({attachment.content_type})"
        )
    images = "\n".join(image_lines) if image_lines else "- 无"
    return f"""标题：{entry.title or "未命名日记"}
日期：{entry.entry_date}
心情：{entry.mood or "未填写"}
标签：{tags}
正文：
{entry.content_markdown or "未填写"}
图片附件：
{images}"""
