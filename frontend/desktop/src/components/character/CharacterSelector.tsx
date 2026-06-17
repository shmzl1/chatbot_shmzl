import * as Dialog from "@radix-ui/react-dialog";
import { useQuery } from "@tanstack/react-query";
import { Check, ChevronDown, RotateCcw } from "lucide-react";
import { useEffect } from "react";
import { listCharacters } from "../../api/chatApi";
import { resolveAssetUrl } from "../../api/client";
import { useAppStore } from "../../stores/appStore";
import type { CharacterSummary } from "../../types/chat";

interface CharacterSelectorProps {
  disabled?: boolean;
  onCharacterChange?: (characterId: string) => void;
}

function initial(name: string) {
  return (name.trim()[0] || "角").toUpperCase();
}

function CharacterAvatar({ character }: { character: CharacterSummary }) {
  if (character.avatar_url) {
    return (
      <img
        className="character-selector-avatar"
        src={resolveAssetUrl(character.avatar_url)}
        alt={character.display_name || character.id}
      />
    );
  }
  return <span className="character-selector-avatar fallback">{initial(character.display_name || character.id)}</span>;
}

export function CharacterSelector({ disabled, onCharacterChange }: CharacterSelectorProps) {
  const selectedCharacterId = useAppStore((state) => state.selectedCharacterId);
  const setSelectedCharacterId = useAppStore((state) => state.setSelectedCharacterId);
  const charactersQuery = useQuery({ queryKey: ["characters"], queryFn: listCharacters, retry: 0 });
  const characters = charactersQuery.data?.characters || [];
  const selected = characters.find((character) => character.id === selectedCharacterId) || null;

  useEffect(() => {
    if (!charactersQuery.data) {
      return;
    }
    if (!characters.length) {
      if (selectedCharacterId) {
        setSelectedCharacterId(null);
      }
      return;
    }
    if (!selectedCharacterId || !characters.some((character) => character.id === selectedCharacterId)) {
      const [firstCharacter] = characters;
      setSelectedCharacterId(firstCharacter.id);
    }
  }, [characters, charactersQuery.data, selectedCharacterId, setSelectedCharacterId]);

  if (charactersQuery.isLoading) {
    return (
      <button className="character-selector-button loading" type="button" disabled>
        <span className="character-selector-avatar fallback" />
        <span>角色</span>
      </button>
    );
  }

  if (charactersQuery.error instanceof Error) {
    return (
      <div className="character-selector-error">
        <span>角色加载失败</span>
        <button type="button" onClick={() => void charactersQuery.refetch()}>
          <RotateCcw size={14} />
          重试
        </button>
      </div>
    );
  }

  if (!characters.length) {
    return <div className="character-selector-empty">暂无可用角色</div>;
  }

  const [firstCharacter] = characters;
  const current = selected || firstCharacter;

  function choose(characterId: string) {
    if (characterId === selectedCharacterId) {
      return;
    }
    setSelectedCharacterId(characterId);
    onCharacterChange?.(characterId);
  }

  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button className="character-selector-button" type="button" disabled={disabled}>
          <CharacterAvatar character={current} />
          <span>{current.display_name || current.id}</span>
          <ChevronDown size={15} />
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-30 bg-black/10" />
        <Dialog.Content className="character-selector-menu">
          <Dialog.Title className="sr-only">选择角色</Dialog.Title>
          <div className="character-selector-list">
            {characters.map((character) => (
              <button
                className={character.id === current.id ? "active" : ""}
                key={character.id}
                type="button"
                onClick={() => choose(character.id)}
              >
                <CharacterAvatar character={character} />
                <span>{character.display_name || character.id}</span>
                {character.id === current.id ? <Check size={15} /> : null}
              </button>
            ))}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
