import argparse
import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://chatbot:change_me_local_only@127.0.0.1:5432/role_chatbot",
    )


def export_sft(character_id: str, min_score: int, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with psycopg.connect(database_url(), row_factory=dict_row) as connection:
        rows = connection.execute(
            """
            SELECT DISTINCT ON (t.id)
                t.user_message,
                t.reply,
                t.emotion,
                f.score,
                f.note
            FROM chat_turns t
            JOIN turn_feedback f ON f.turn_id = t.id
            WHERE t.character_id = %s
              AND f.score >= %s
            ORDER BY t.id, f.score DESC, f.created_at DESC
            """,
            (character_id, min_score),
        ).fetchall()

    with output_path.open("w", encoding="utf-8") as file:
        for row in rows:
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
                    "note": row["note"],
                },
            }
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    return len(rows)


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
