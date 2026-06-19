import { useEffect, useRef, useState } from "react";

import type { OocMessage } from "../api/types";
import { useAuthStore } from "../stores/authStore";

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

    const socket = new WebSocket(buildWsUrl(campaignId, token));

    socket.onopen = () => setConnected(true);
    socket.onerror = () => setConnected(false);
    socket.onclose = () => setConnected(false);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as OocWsEvent;
      if (data.event === "ooc_snapshot") {
        onSnapshotRef.current(data.messages);
      } else if (data.event === "ooc_message") {
        onMessageRef.current(data.message);
      } else if (data.event === "error" && data.detail) {
        onErrorRef.current?.(data.detail);
      }
    };

    return () => {
      socket.close();
      setConnected(false);
    };
  }, [campaignId, token]);

  return { connected };
}
