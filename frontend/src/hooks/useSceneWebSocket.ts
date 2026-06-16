import { useCallback, useEffect, useRef, useState } from "react";

import type { Scene } from "../api/types";
import { useAuthStore } from "../stores/authStore";

type SceneWsEvent =
  | { event: "scene_snapshot"; scene: Scene }
  | { event: "scene_update"; scene: Scene }
  | { event: "error"; detail: string };

type UseSceneWebSocketOptions = {
  sceneId: string | null;
  onSceneUpdate: (scene: Scene) => void;
};

function buildWsUrl(sceneId: string, token: string): string {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = window.location.host;
  const params = new URLSearchParams({ token });
  return `${protocol}//${host}/api/v1/ws/scenes/${sceneId}?${params.toString()}`;
}

export function useSceneWebSocket({ sceneId, onSceneUpdate }: UseSceneWebSocketOptions) {
  const token = useAuthStore((state) => state.token);
  const socketRef = useRef<WebSocket | null>(null);
  const onSceneUpdateRef = useRef(onSceneUpdate);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    onSceneUpdateRef.current = onSceneUpdate;
  }, [onSceneUpdate]);

  useEffect(() => {
    if (!sceneId || !token) {
      setConnected(false);
      return;
    }

    const socket = new WebSocket(buildWsUrl(sceneId, token));
    socketRef.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => {
      setConnected(false);
      if (socketRef.current === socket) {
        socketRef.current = null;
      }
    };
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data) as SceneWsEvent;
      if (data.event === "scene_snapshot" || data.event === "scene_update") {
        onSceneUpdateRef.current(data.scene);
      }
    };

    return () => {
      socket.close();
      if (socketRef.current === socket) {
        socketRef.current = null;
      }
      setConnected(false);
    };
  }, [sceneId, token]);

  const send = useCallback((payload: Record<string, string>) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }
    socket.send(JSON.stringify(payload));
    return true;
  }, []);

  const sendMessage = useCallback(
    (text: string) => send({ action: "message", text }),
    [send],
  );

  const sendDiceRoll = useCallback(
    (diceExpression: string) => send({ action: "dice", dice_expression: diceExpression }),
    [send],
  );

  return { connected, sendMessage, sendDiceRoll };
}
