# Characters Module

The character system is centralized in `backend/modules/characters`.

## Directory Layout

```text
backend/modules/characters/
  api.py
  service.py
  repository.py
  schemas.py
  pack_loader.py
  pack_writer.py
  validator.py
  templates/
    default_character.json
  packs/
    role01/
      character.json
      voice_refs/
      backups/
    .trash/
```

Public templates live in `backend/modules/characters/templates`.
Each character lives in one directory under
`backend/modules/characters/packs/{character_id}/`.

`character.json` is the only required file in a character pack.
Optional voice references live under that character's own `voice_refs/`
directory. Safety backups live under that character's own `backups/`
directory.

The old `backend/data/character_packs` location is deprecated. It is kept only
to avoid deleting historical local data. New characters should not be added
there.

The default `role01` character has been migrated to:

```text
backend/modules/characters/packs/role01/
```

## CLI

Create a character:

```powershell
cd backend
python -m tools.character_pack new asa_mitaka --name "三鹰朝"
```

Validate a character:

```powershell
python -m tools.character_pack validate asa_mitaka
```

List active and trashed characters:

```powershell
python -m tools.character_pack list
```

Delete a character safely:

```powershell
python -m tools.character_pack delete asa_mitaka
```

Delete only moves the pack to `.trash`; it does not delete historical chat
records.

Restore a character:

```powershell
python -m tools.character_pack restore asa_mitaka
```

## Debug

```text
GET /debug/characters
GET /debug/characters/{character_id}
```

Debug output includes pack paths, validation state, lore/dialogue/reaction
counts, avatar and voice state, trash state, and backup state.

## API Boundary

Character management routes live in `modules.characters.api`.
Persona review still uses the same public routes, but reads and writes character
packs through this module.

Ordinary chat reads characters through this module as well. Retrieval uses the
`lore`, `dialogues`, and `reactions` already loaded from each character pack.

Do not commit official avatars, voice recordings, model weights, or private
local assets to GitHub. `character.json` is intentionally not ignored.
