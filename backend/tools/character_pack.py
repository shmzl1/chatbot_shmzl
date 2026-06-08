import argparse
import sys
from typing import Any, Dict, List

from fastapi import HTTPException

from modules.characters.service import character_service


def main() -> int:
    parser = argparse.ArgumentParser(description="Create, validate, list, delete, and restore character packs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    new_parser = subparsers.add_parser("new", help="Create a new character pack from a template.")
    new_parser.add_argument("character_id")
    new_parser.add_argument("--name", required=True, help="Display name for the character.")
    new_parser.add_argument("--template", default="default", help="Base template name. Defaults to 'default'.")

    validate_parser = subparsers.add_parser("validate", help="Validate one character pack.")
    validate_parser.add_argument("character_id")

    delete_parser = subparsers.add_parser("delete", help="Move a character pack to trash.")
    delete_parser.add_argument("character_id")

    restore_parser = subparsers.add_parser("restore", help="Restore a character pack from trash.")
    restore_parser.add_argument("character_id")

    subparsers.add_parser("list", help="List active and trashed character packs.")

    args = parser.parse_args()
    try:
        if args.command == "new":
            return create_pack(args.character_id, args.name, args.template)
        if args.command == "validate":
            return validate_pack(args.character_id)
        if args.command == "delete":
            return delete_pack(args.character_id)
        if args.command == "restore":
            return restore_pack(args.character_id)
        if args.command == "list":
            return list_packs()
    except HTTPException as exc:
        print(f"ERROR: {exc.detail}")
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

    parser.print_help()
    return 2


def create_pack(character_id: str, display_name: str, base_template: str) -> int:
    character = character_service.create_character(
        character_id=character_id,
        display_name=display_name,
        base_template=base_template,
    )
    validation = character_service.validate_pack(character.id)
    _print_validation_result(validation)
    print(f"Created character pack: {validation['pack_path']}")
    return 0


def validate_pack(character_id: str) -> int:
    result = character_service.validate_pack(character_id)
    _print_validation_result(result)
    return 1 if result["errors"] else 0


def delete_pack(character_id: str) -> int:
    result = character_service.delete_character(character_id)
    print(f"Moved character pack to trash: {result['trash_path']}")
    return 0


def restore_pack(character_id: str) -> int:
    result = character_service.restore_character(character_id)
    print(f"Restored character pack: {result['pack_path']}")
    return 0


def list_packs() -> int:
    debug = character_service.debug_all_characters()
    rows = [
        [
            "id",
            "display_name",
            "valid",
            "lore",
            "dialogues",
            "reactions",
            "has_voice",
            "state",
        ]
    ]
    had_errors = False
    for state, key in (("active", "characters"), ("trashed", "trashed_characters")):
        for result in debug[key]:
            had_errors = had_errors or bool(result["errors"])
            rows.append(
                [
                    result["character_id"],
                    result["display_name"],
                    "yes" if result["valid"] else "no",
                    str(result["lore_count"]),
                    str(result["dialogue_count"]),
                    str(result["reaction_count"]),
                    "yes" if result["has_voice_config"] else "no",
                    state,
                ]
            )

    _print_table(rows)
    for result in debug["characters"] + debug["trashed_characters"]:
        if result["errors"]:
            print("")
            _print_validation_result(result)

    return 1 if had_errors else 0


def _print_validation_result(result: Dict[str, Any]) -> None:
    print(f"character_id: {result['character_id']}")
    print(f"display_name: {result['display_name']}")
    print(f"pack_path: {result['pack_path']}")
    print(f"character_path: {result['character_path']}")
    print(f"valid: {result['valid']}")
    print(f"lore_count: {result['lore_count']}")
    print(f"dialogue_count: {result['dialogue_count']}")
    print(f"reaction_count: {result['reaction_count']}")
    print(f"has_voice: {result['has_voice_config']}")
    print(f"state: {'trashed' if result['is_trashed'] else 'active'}")
    if result["warnings"]:
        print("warnings:")
        for warning in result["warnings"]:
            print(f"- {warning}")
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
