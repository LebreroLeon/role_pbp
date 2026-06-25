import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import type { OocMessage, UnreadCounts } from "../api/types";
import { buildWsUrl as buildApiWsUrl } from "../api/apiBase";
import { connectWebSocketWithRetry } from "../hooks/wsReconnect";
import { useAuthStore } from "../stores/authStore";

const HEARTBEAT_INTERVAL_MS = 45_000;

type CampaignWsEvent =
  | { event: "ooc_snapshot"; messages: OocMessage[] }
  | { event: "ooc_message"; message: OocMessage }
  | { event: "ooc_message_deleted"; message_id: string }
  | { event: "unread_counts"; play: number; ooc: number }
  | { event: "presence_snapshot"; online_user_ids: string[] }
  | { event: "presence_update"; online_user_ids: string[] }
  | { event: "heartbeat_ack" }
  | { event: "error"; detail: string };

export type OocWsHandlers = {
  onSnapshot?: (messages: OocMessage[]) => void;
  onMessage?: (message: OocMessage) => void;
  onMessageDeleted?: (messageId: string) => void;
  onError?: (detail: string) => void;
};

type CampaignWsContextValue = {
  connected: boolean;
  onlineUserIds: ReadonlySet<string>;
  registerOocHandlers: (handlers: OocWsHandlers | null) => void;
};

const CampaignWsContext = createContext<CampaignWsContextValue | null>(null);

function buildCampaignWsUrl(campaignId: string, token: string): string {
  const params = new URLSearchParams({ token });
  return buildApiWsUrl(`/api/v1/ws/campaigns/${campaignId}`, params);
}

type CampaignWsProviderProps = {
  campaignId: string;
  children: ReactNode;
  onUnreadCounts?: (counts: UnreadCounts) => void;
};

export function CampaignWsProvider({ campaignId, children, onUnreadCounts }: CampaignWsProviderProps) {
  const token = useAuthStore((state) => state.token);
  const [connected, setConnected] = useState(false);
  const [onlineUserIds, setOnlineUserIds] = useState<ReadonlySet<string>>(() => new Set());
  const oocHandlersRef = useRef<OocWsHandlers>({});
  const socketRef = useRef<WebSocket | null>(null);
  const onUnreadCountsRef = useRef(onUnreadCounts);

  useEffect(() => {
    onUnreadCountsRef.current = onUnreadCounts;
  }, [onUnreadCounts]);

  const registerOocHandlers = useCallback((handlers: OocWsHandlers | null) => {
    oocHandlersRef.current = handlers ?? {};
  }, []);

  useEffect(() => {
    if (!campaignId || !token) {
      setConnected(false);
      setOnlineUserIds(new Set());
      return;
    }

    const handle = connectWebSocketWithRetry({
      buildUrl: () => buildCampaignWsUrl(campaignId, token),
      onOpen: (socket) => {
        socketRef.current = socket;
        setConnected(true);
      },
      onMessage: (event) => {
        const data = JSON.parse(event.data) as CampaignWsEvent;
        if (data.event === "presence_snapshot" || data.event === "presence_update") {
          setOnlineUserIds(new Set(data.online_user_ids));
        } else if (data.event === "ooc_snapshot") {
          oocHandlersRef.current.onSnapshot?.(data.messages);
        } else if (data.event === "ooc_message") {
          oocHandlersRef.current.onMessage?.(data.message);
        } else if (data.event === "ooc_message_deleted") {
          oocHandlersRef.current.onMessageDeleted?.(data.message_id);
        } else if (data.event === "unread_counts") {
          onUnreadCountsRef.current?.({ play: data.play, ooc: data.ooc });
        } else if (data.event === "error" && data.detail) {
          oocHandlersRef.current.onError?.(data.detail);
        }
      },
      onDisconnected: () => {
        socketRef.current = null;
        setConnected(false);
      },
    });

    return () => {
      handle.close();
      socketRef.current = null;
      setConnected(false);
      setOnlineUserIds(new Set());
    };
  }, [campaignId, token]);

  useEffect(() => {
    if (!connected) return;

    const interval = setInterval(() => {
      const socket = socketRef.current;
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ action: "heartbeat" }));
      }
    }, HEARTBEAT_INTERVAL_MS);

    return () => clearInterval(interval);
  }, [connected, campaignId]);

  const value: CampaignWsContextValue = {
    connected,
    onlineUserIds,
    registerOocHandlers,
  };

  return <CampaignWsContext.Provider value={value}>{children}</CampaignWsContext.Provider>;
}

export function useCampaignWs(): CampaignWsContextValue {
  const context = useContext(CampaignWsContext);
  if (!context) {
    throw new Error("useCampaignWs must be used within CampaignWsProvider");
  }
  return context;
}
