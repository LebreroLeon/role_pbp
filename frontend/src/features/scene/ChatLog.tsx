import { useEffect, useLayoutEffect, useRef } from "react";

import type { CampaignEntity, ChatMessage } from "../../api/types";
import type { MemberLookup } from "./ChatEntry";
import { ChatEntry } from "./ChatEntry";
import type { SceneStateInput } from "./sceneState";

const BOTTOM_THRESHOLD_PX = 96;

type ChatLogProps = {
  messages: ChatMessage[];
  members: MemberLookup;
  currentUserId: string;
  memberCount: number;
  emptyMessage: string;
  onVisible?: () => void;
  isMaster?: boolean;
  onDeleteMessage?: (messageId: string) => void;
  onToggleLike?: (messageId: string) => void;
  togglingLikeId?: string | null;
  entities?: CampaignEntity[];
  sceneState?: SceneStateInput | null;
};

function getTailSignature(messages: ChatMessage[]): string {
  if (messages.length === 0) return "0";
  const last = messages[messages.length - 1];
  return `${messages.length}:${last.id ?? last.timestamp}:${last.text ?? last.final_result ?? ""}`;
}

function isNearBottom(container: HTMLDivElement): boolean {
  const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
  return distanceFromBottom <= BOTTOM_THRESHOLD_PX;
}

export function ChatLog({
  messages,
  members,
  currentUserId,
  memberCount,
  emptyMessage,
  onVisible,
  isMaster = false,
  onDeleteMessage,
  onToggleLike,
  togglingLikeId = null,
  entities,
  sceneState,
}: ChatLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tailSignatureRef = useRef(getTailSignature(messages));
  const initialScrollRef = useRef(true);
  const onVisibleRef = useRef(onVisible);
  const markReadTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const scrollSnapshotRef = useRef(0);
  const messagesRef = useRef(messages);

  if (messagesRef.current !== messages && containerRef.current) {
    scrollSnapshotRef.current = containerRef.current.scrollTop;
  }
  messagesRef.current = messages;

  useEffect(() => {
    onVisibleRef.current = onVisible;
  }, [onVisible]);

  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (messages.length === 0) {
      tailSignatureRef.current = getTailSignature(messages);
      return;
    }

    const nextSignature = getTailSignature(messages);
    const hasNewTail = nextSignature !== tailSignatureRef.current;
    tailSignatureRef.current = nextSignature;

    if (initialScrollRef.current) {
      container.scrollTop = container.scrollHeight;
      initialScrollRef.current = false;
      return;
    }

    if (!hasNewTail) {
      container.scrollTop = scrollSnapshotRef.current;
      return;
    }

    const lastMessage = messages[messages.length - 1];
    const ownMessage = lastMessage?.sender_id === currentUserId;

    if (ownMessage || isNearBottom(container)) {
      container.scrollTop = container.scrollHeight;
      return;
    }

    container.scrollTop = scrollSnapshotRef.current;
  }, [messages, currentUserId]);

  const scheduleMarkRead = () => {
    if (!onVisibleRef.current) return;
    if (markReadTimerRef.current) clearTimeout(markReadTimerRef.current);
    markReadTimerRef.current = setTimeout(() => {
      onVisibleRef.current?.();
    }, 400);
  };

  useEffect(() => {
    const container = containerRef.current;
    if (!container || !isNearBottom(container)) return;
    scheduleMarkRead();
    return () => {
      if (markReadTimerRef.current) clearTimeout(markReadTimerRef.current);
    };
  }, [messages]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      if (isNearBottom(container)) scheduleMarkRead();
    };

    container.addEventListener("scroll", handleScroll, { passive: true });
    return () => container.removeEventListener("scroll", handleScroll);
  }, []);

  if (!messages.length) {
    return (
      <div className="chat-log" ref={containerRef}>
        <p className="muted chat-log-empty">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="chat-log" ref={containerRef}>
      <div className="chat-log-feed">
        {messages.map((entry, index) => (
          <ChatEntry
            key={entry.id ?? `${entry.timestamp}-${index}`}
            message={entry}
            members={members}
            currentUserId={currentUserId}
            memberCount={memberCount}
            isMaster={isMaster}
            onDelete={onDeleteMessage}
            onToggleLike={onToggleLike}
            togglingLikeId={togglingLikeId}
            entities={entities}
            sceneState={sceneState}
          />
        ))}
      </div>
    </div>
  );
}
