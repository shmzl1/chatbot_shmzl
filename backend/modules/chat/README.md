# Chat Module

## Module Responsibility

Ordinary character chat flow: load character, retrieve context, build prompt,
call LLM, judge/rewrite reply, optionally synthesize voice, and save chat turns.

## Not Responsible For

Schedule planning, diary reading, character-pack writing, persona-review apply,
or relationship-memory persistence.

## Public Interfaces

- `POST /chat/text`
- `POST /chat`

## Data Boundary

Owns ordinary chat sessions and turns in PostgreSQL. It may read characters via
the characters module and may read memories/knowledge through their public APIs.

## Allowed Dependencies

May call public services for characters, retrieval, memory, knowledge, LLM,
style judging, rewrite, emotion, and voice.

## Forbidden Dependencies

Must not write schedule or diary data. Must not import schedule/diary
repositories. Must not build character-pack filesystem paths directly.

## Codex Notes

For chat bugs, inspect chat API/service flow and prompt/retrieval dependencies.
Do not change persona review, schedule, diary, or character-pack writing unless
the bug crosses a public interface.

