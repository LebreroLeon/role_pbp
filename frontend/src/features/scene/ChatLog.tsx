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
  onLoadMore?: () => void;
  hasMoreHistory?: boolean;
  loadingMore?: boolean;
  scrollResetKey?: string;
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
  onLoadMore,
  hasMoreHistory = false,
  loadingMore = false,
  scrollResetKey = "",
}: ChatLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tailSignatureRef = useRef(getTailSignature(messages));
  const prevMessageCountRef = useRef(messages.length);
  const stickToBottomRef = useRef(true);
  const scrollResetKeyRef = useRef(scrollResetKey);
  const onVisibleRef = useRef(onVisible);
  const markReadTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    onVisibleRef.current = onVisible;
  }, [onVisible]);

  useLayoutEffect(() => {
    if (scrollResetKey !== scrollResetKeyRef.current) {
      scrollResetKeyRef.current = scrollResetKey;
      stickToBottomRef.current = true;
      tailSignatureRef.current = "0";
      prevMessageCountRef.current = 0;
    }
  }, [scrollResetKey]);

  useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (messages.length === 0) {
      tailSignatureRef.current = getTailSignature(messages);
      prevMessageCountRef.current = 0;
      return;
    }

    const nextSignature = getTailSignature(messages);
    const hasNewTail = nextSignature !== tailSignatureRef.current;
    const prevCount = prevMessageCountRef.current;
    const prevScrollHeight = container.scrollHeight;
    const prevScrollTop = container.scrollTop;

    const lastMessage = messages[messages.length - 1];
    const ownMessage = lastMessage?.sender_id === currentUserId;
    const isPrepend = !hasNewTail && messages.length > prevCount;

    if (stickToBottomRef.current || ownMessage || (hasNewTail && !isPrepend)) {
      container.scrollTop = container.scrollHeight;
    } else if (isPrepend) {
      const heightDelta = container.scrollHeight - prevScrollHeight;
      if (heightDelta > 0) {
        container.scrollTop = prevScrollTop + heightDelta;
      }
    }

    tailSignatureRef.current = nextSignature;
    prevMessageCountRef.current = messages.length;
  }, [messages, currentUserId, scrollResetKey]);

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
      stickToBottomRef.current = isNearBottom(container);
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
        {hasMoreHistory && onLoadMore ? (
          <div className="chat-log-load-more">
            <button
              type="button"
              className="button button--ghost button--small"
              onClick={onLoadMore}
              disabled={loadingMore}
            >
              {loadingMore ? "Cargando…" : "Cargar mensajes anteriores"}
            </button>
          </div>
        ) : null}
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
