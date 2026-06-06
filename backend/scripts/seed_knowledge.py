import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--character-id", default=os.getenv("DEFAULT_CHARACTER_ID", "role01"))
    args = parser.parse_args()

    from core.config import settings
    from services.database_service import database_service

    result = database_service.import_jsonl_knowledge(
        data_dir=settings.data_dir,
        character_id=args.character_id,
    )
    print(
        f"Imported JSONL knowledge for {args.character_id}: "
        f"{result['inserted']} inserted, {result['skipped']} skipped"
    )


if __name__ == "__main__":
    main()
