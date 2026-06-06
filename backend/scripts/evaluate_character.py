import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


BACKEND_DIR = Path(__file__).resolve().parents[1]


def read_eval_set(path: Path) -> list[dict]:
    items = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def evaluate(base_url: str, character_id: str, eval_path: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cases = read_eval_set(eval_path)
    results = []
    for case in cases:
        response = requests.post(
            f"{base_url.rstrip('/')}/chat/text",
            json={
                "character_id": character_id,
                "message": case["message"],
            },
            timeout=120,
        )
        payload = response.json()
        results.append(
            {
                "id": case.get("id"),
                "message": case["message"],
                "status_code": response.status_code,
                "response": payload,
            }
        )

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "character_id": character_id,
        "eval_path": str(eval_path),
        "results": results,
    }
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(results)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--character-id", default="role01")
    parser.add_argument(
        "--eval",
        default=str(BACKEND_DIR / "data" / "eval" / "role01_eval.jsonl"),
    )
    parser.add_argument(
        "--output",
        default=str(BACKEND_DIR / "outputs" / "eval" / "role01_eval_report.json"),
    )
    args = parser.parse_args()

    count = evaluate(
        base_url=args.base_url,
        character_id=args.character_id,
        eval_path=Path(args.eval),
        output_path=Path(args.output),
    )
    print(f"Evaluated {count} cases. Report: {args.output}")


if __name__ == "__main__":
    main()
