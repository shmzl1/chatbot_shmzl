import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from core.config import settings
from services.character_service import CHARACTER_FILE, PACK_TEMPLATE_ID, character_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Create, validate, and list character packs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="Create a new character pack from the template.")
    new_parser.add_argument("character_id")
    new_parser.add_argument("--name", required=True, help="Display name for the character.")

    validate_parser = subparsers.add_parser("validate", help="Validate one character pack.")
    validate_parser.add_argument("character_id")

    subparsers.add_parser("list", help="List character packs.")

    args = parser.parse_args()
    if args.command == "new":
        return create_pack(args.character_id, args.name)
    if args.command == "validate":
        return validate_pack(args.character_id)
    if args.command == "list":
        return list_packs()

    parser.print_help()
    return 2


def create_pack(character_id: str, display_name: str) -> int:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", character_id):
        print("ERROR: character_id may only contain letters, numbers, underscore, and hyphen.")
        return 1

    packs_dir = settings.data_dir / "character_packs"
    template_path = packs_dir / PACK_TEMPLATE_ID / CHARACTER_FILE
    pack_dir = packs_dir / character_id
    character_path = pack_dir / CHARACTER_FILE

    if character_path.exists():
        print(f"ERROR: character pack already exists: {character_path}")
        return 1
    if not template_path.exists():
        print(f"ERROR: template does not exist: {template_path}")
        return 1

    try:
        template = _read_json(template_path)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    template["id"] = character_id
    template["display_name"] = display_name
    voice = template.get("voice")
    if isinstance(voice, dict) and isinstance(voice.get("ref_audio_path"), str):
        voice["ref_audio_path"] = voice["ref_audio_path"].replace("new_character", character_id)

    (pack_dir / "voice_refs" / "neutral").mkdir(parents=True, exist_ok=True)
    character_path.write_text(
        json.dumps(template, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Created character pack: {pack_dir}")
    print(f"Created character file: {character_path}")
    print(f"Created voice refs directory: {pack_dir / 'voice_refs' / 'neutral'}")
    return 0


def validate_pack(character_id: str) -> int:
    result = character_service.validate_pack(character_id)
    _print_validation_result(result)
    return 1 if result["errors"] else 0


def list_packs() -> int:
    results = character_service.validate_all_packs()
    rows = [
        [
            "id",
            "display_name",
            "lore",
            "dialogues",
            "reactions",
            "voice",
            "errors",
        ]
    ]
    for result in results:
        rows.append(
            [
                result["character_id"],
                result["display_name"],
                str(result["lore_count"]),
                str(result["dialogue_count"]),
                str(result["reaction_count"]),
                "yes" if result["has_voice_config"] else "no",
                str(len(result["errors"])),
            ]
        )

    _print_table(rows)
    for result in results:
        if result["errors"]:
            print("")
            _print_validation_result(result)

    return 1 if any(result["errors"] for result in results) else 0


def _read_json(file_path: Path) -> Dict[str, Any]:
    try:
        with file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{file_path} is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError(f"{file_path} must contain a JSON object.")
    return payload


def _print_validation_result(result: Dict[str, Any]) -> None:
    print(f"character_id: {result['character_id']}")
    print(f"display_name: {result['display_name']}")
    print(f"pack_path: {result['pack_path']}")
    print(f"character_path: {result['character_path']}")
    print(f"lore_count: {result['lore_count']}")
    print(f"dialogue_count: {result['dialogue_count']}")
    print(f"reaction_count: {result['reaction_count']}")
    print(f"has_voice_config: {result['has_voice_config']}")
    if result["errors"]:
        print("errors:")
        for error in result["errors"]:
            print(f"- {error}")
    else:
        print("errors: none")


def _print_table(rows: List[List[str]]) -> None:
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    for row_index, row in enumerate(rows):
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))
        if row_index == 0:
            print("  ".join("-" * width for width in widths))


if __name__ == "__main__":
    sys.exit(main())
