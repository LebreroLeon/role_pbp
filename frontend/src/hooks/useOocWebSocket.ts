import { useEffect, useRef, useState } from "react";

import type { OocMessage } from "../api/types";
import { useAuthStore } from "../stores/authStore";
import { connectWebSocketWithRetry } from "./wsReconnect";

type OocWsEvent =
  | { event: "ooc_snapshot"; messages: OocMessage[] }
  | { event: "ooc_message"; message: OocMessage }
  | { event: "error"; detail: string };

type UseOocWebSocketOptions = {
  campaignId: string | null;
  onSnapshot: (messages: OocMessage[]) => void;
  onMessage: (message: OocMessage) => void;
  onError?: (message: string) => void;
};

function buildWsUrl(campaignId: string, token: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  const params = new URLSearchParams({ token });
  return `${protocol}//${host}/api/v1/ws/campaigns/${campaignId}?${params.toString()}`;
}

export function useOocWebSocket({
  campaignId,
  onSnapshot,
  onMessage,
  onError,
}: UseOocWebSocketOptions) {
  const token = useAuthStore((state) => state.token);
  const onSnapshotRef = useRef(onSnapshot);
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    onSnapshotRef.current = onSnapshot;
  }, [onSnapshot]);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    if (!campaignId || !token) {
      setConnected(false);
      return;
    }

    const handle = connectWebSocketWithRetry({
      buildUrl: () => buildWsUrl(campaignId, token),
      onOpen: () => setConnected(true),
      onMessage: (event) => {
        const data = JSON.parse(event.data) as OocWsEvent;
        if (data.event === "ooc_snapshot") {
          onSnapshotRef.current(data.messages);
        } else if (data.event === "ooc_message") {
          onMessageRef.current(data.message);
        } else if (data.event === "error" && data.detail) {
          onErrorRef.current?.(data.detail);
        }
      },
      onDisconnected: () => setConnected(false),
    });

    return () => {
      handle.close();
      setConnected(false);
    };
  }, [campaignId, token]);

  return { connected };
}
