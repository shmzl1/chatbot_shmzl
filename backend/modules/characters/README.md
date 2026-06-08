# Characters Module

## Module Responsibility

Owns the character/person system: character packs, templates, validation,
create/update/delete/restore, avatar updates, and character-pack filesystem
boundaries.

## Not Responsible For

Ordinary chat turns, persona feedback records, schedule data, diary data,
memories, knowledge records, or voice synthesis execution.

## Public Interfaces

- `GET /characters`
- `GET /characters/{character_id}`
- `POST /characters`
- `PATCH /characters/{character_id}`
- `DELETE /characters/{character_id}`
- `POST /characters/{character_id}/restore`
- `POST /characters/{character_id}/avatar`
- `GET /characters/{character_id}/validate`
- CLI: `python -m tools.character_pack ...`

## Internal File Responsibilities

- `api.py`: character HTTP routes and persona-review route hosting.
- `service.py`: character business operations.
- `repository.py`: module paths: templates, packs, trash, backups.
- `pack_loader.py`: read and parse `character.json`.
- `pack_writer.py`: safe writes, backups, trash, restore.
- `validator.py`: character-pack validation.
- `schemas.py`: character module request/response models.

## Data Boundary

The only character data source is:

```text
backend/modules/characters/packs/{character_id}/character.json
```

Templates live at:

```text
backend/modules/characters/templates/
```

The project no longer uses `backend/data/character_packs`.

`character.json` is not ignored by Git. Local voice files, `backups`, and
`.trash` are ignored except for `.gitkeep` placeholders.

## CLI

```powershell
cd backend
python -m tools.character_pack list
python -m tools.character_pack new asa_mitaka --name "三鹰朝"
python -m tools.character_pack validate asa_mitaka
python -m tools.character_pack delete asa_mitaka
python -m tools.character_pack restore asa_mitaka
```

Delete only moves a pack to:

```text
backend/modules/characters/packs/.trash/
```

It does not delete historical chat records.

## Allowed Dependencies

May use core schemas/config, avatar service, database avatar map compatibility,
and persona review service for hosted persona-review routes.

## Forbidden Dependencies

Other modules must not build character-pack paths themselves. They should call
the characters service or loader/writer helpers. This module must not write chat
sessions, memories, knowledge records, schedule data, or diary data.

## Codex Notes

For character tasks, start here. Usually inspect `service.py`,
`repository.py`, `pack_loader.py`, `pack_writer.py`, and `validator.py`.
Do not reintroduce old `backend/data/character_packs`.
