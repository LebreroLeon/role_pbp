import { ChatMiniSheet } from "./dnd5e/ChatMiniSheet";

type GameSystemChatMiniSheetProps = {
  campaignId: string;
  gameSystem?: string;
  disabled?: boolean;
  onSceneRefresh?: () => void;
};

export function GameSystemChatMiniSheet({
  campaignId,
  gameSystem,
  disabled,
  onSceneRefresh,
}: GameSystemChatMiniSheetProps) {
  if (gameSystem === "dnd5e") {
    return (
      <ChatMiniSheet
        campaignId={campaignId}
        disabled={disabled}
        onSceneRefresh={onSceneRefresh}
      />
    );
  }
  return null;
}
