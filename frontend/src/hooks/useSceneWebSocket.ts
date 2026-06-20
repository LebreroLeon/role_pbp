import { useCallback, useEffect, useRef, useState } from "react";

import type { Scene } from "../api/types";
import { normalizeScene } from "../features/scene/sceneState";
import { useAuthStore } from "../stores/authStore";
import { buildWsUrl as buildApiWsUrl } from "../api/apiBase";
import { connectWebSocketWithRetry } from "./wsReconnect";

type SceneWsEvent =
  | { event: "scene_snapshot"; scene: Scene }
  | { event: "scene_update"; scene: Scene }
  | { event: "error"; detail: string };

type UseSceneWebSocketOptions = {
  sceneId: string | null;
  onSceneUpdate: (scene: Scene) => void;
  onError?: (message: string) => void;
};

function buildWsUrl(sceneId: string, token: string): string {
  const params = new URLSearchParams({ token });
  return buildApiWsUrl(`/api/v1/ws/scenes/${sceneId}`, params);
}

export function useSceneWebSocket({ sceneId, onSceneUpdate, onError }: UseSceneWebSocketOptions) {
  const token = useAuthStore((state) => state.token);
  const socketRef = useRef<WebSocket | null>(null);
  const onSceneUpdateRef = useRef(onSceneUpdate);
  const onErrorRef = useRef(onError);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    onSceneUpdateRef.current = onSceneUpdate;
  }, [onSceneUpdate]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    if (!sceneId || !token) {
      setConnected(false);
      return;
    }

    const handle = connectWebSocketWithRetry({
      buildUrl: () => buildWsUrl(sceneId, token),
      onOpen: (socket) => {
        socketRef.current = socket;
        setConnected(true);
      },
      onMessage: (event) => {
        const data = JSON.parse(event.data) as SceneWsEvent;
        if (data.event === "scene_snapshot" || data.event === "scene_update") {
          onSceneUpdateRef.current(normalizeScene(data.scene));
        } else if (data.event === "error" && data.detail) {
          onErrorRef.current?.(data.detail);
        }
      },
      onDisconnected: () => setConnected(false),
    });

    return () => {
      handle.close();
      socketRef.current = null;
      setConnected(false);
    };
  }, [sceneId, token]);

  const send = useCallback((payload: Record<string, unknown>) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }
    socket.send(JSON.stringify(payload));
    return true;
  }, []);

  const sendMessage = useCallback(
    (
      text: string,
      messageType: string,
      speaker?: {
        speaker_type: string;
        speaker_entity_id?: string;
        speaker_display_name: string;
      },
    ) =>
      send({
        action: "message",
        text,
        message_type: messageType,
        ...(speaker ?? {}),
      }),
    [send],
  );

  const sendDiceRoll = useCallback(
    (
      diceExpression: string,
      options?: { modifier?: number; advantage?: boolean; disadvantage?: boolean; masterOnly?: boolean },
    ) =>
      send({
        action: "dice",
        dice_expression: diceExpression,
        modifier: options?.modifier ?? 0,
        advantage: options?.advantage ?? false,
        disadvantage: options?.disadvantage ?? false,
        master_only: options?.masterOnly ?? false,
      }),
    [send],
  );

  const markRead = useCallback(
    (messageIds?: string[]) =>
      send({
        action: "mark_read",
        message_ids: messageIds && messageIds.length > 0 ? messageIds : undefined,
      }),
    [send],
  );

  return { connected, sendMessage, sendDiceRoll, markRead };
}
