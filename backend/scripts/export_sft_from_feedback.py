import argparse
import json
from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from services.database_service import database_service  # noqa: E402


def export_sft(character_id: str, min_score: int, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    database_service.ensure_ready()
    with database_service._connect() as connection:
        rows = connection.execute(
            """
            SELECT
                t.user_message,
                t.reply,
                t.emotion,
                f.score,
                f.note
            FROM chat_turns t
            JOIN turn_feedback f ON f.turn_id = t.id
            WHERE t.character_id = ?
              AND f.score >= ?
            ORDER BY t.id ASC, f.score DESC, f.created_at DESC
            """,
            (character_id, min_score),
        ).fetchall()

    with output_path.open("w", encoding="utf-8") as file:
        seen_keys: set[tuple[str, str]] = set()
        for row in rows:
            key = (row["user_message"], row["reply"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            item = {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是角色A。外冷内热，嘴硬但关心用户。不要说自己是AI。回复短句，不要长篇说教。",
                    },
                    {"role": "user", "content": row["user_message"]},
                    {"role": "assistant", "content": row["reply"]},
                ],
                "metadata": {
                    "character_id": character_id,
                    "emotion": row["emotion"],
                    "score": row["score"],
                    "note": row["note"] or "",
                },
            }
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    return len(seen_keys)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--character-id", default="role01")
    parser.add_argument("--min-score", type=int, default=8)
    parser.add_argument(
        "--output",
        default=str(BACKEND_DIR / "data" / "sft" / "role01_train.jsonl"),
    )
    args = parser.parse_args()

    count = export_sft(
        character_id=args.character_id,
        min_score=args.min_score,
        output_path=Path(args.output),
    )
    print(f"Exported {count} samples to {args.output}")


if __name__ == "__main__":
    main()
