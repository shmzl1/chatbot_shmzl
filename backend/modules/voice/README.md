# Voice Module

## Module Responsibility

Optional GPT-SoVITS voice synthesis and voice test endpoints.

## Not Responsible For

Character-pack ownership, chat content generation, schedule, diary, or memory.

## Public Interfaces

- Voice test routes
- TTS service used by chat when voice is enabled

## Data Boundary

Writes generated audio to backend outputs. Reads voice configuration from the
character object loaded through the characters module.

## Allowed Dependencies

May use characters public service for resolving character-pack-relative voice
paths, settings, and HTTP calls to GPT-SoVITS.

## Forbidden Dependencies

Must not assume old character-pack paths. Must not pretend success when
reference audio or GPT-SoVITS is missing.

## Codex Notes

Voice errors should be explicit. Do not introduce a fake audio fallback.

