const MAX_WS_RETRIES = 5;
const BASE_WS_RETRY_MS = 1000;

export type WsReconnectHandle = {
  close: () => void;
};

type ConnectWebSocketOptions = {
  buildUrl: () => string;
  onOpen: (socket: WebSocket) => void;
  onMessage: (event: MessageEvent) => void;
  onDisconnected?: () => void;
};

export function connectWebSocketWithRetry({
  buildUrl,
  onOpen,
  onMessage,
  onDisconnected,
}: ConnectWebSocketOptions): WsReconnectHandle {
  let socket: WebSocket | null = null;
  let retryCount = 0;
  let retryTimer: ReturnType<typeof setTimeout> | null = null;
  let intentionalClose = false;

  const clearRetryTimer = () => {
    if (retryTimer !== null) {
      clearTimeout(retryTimer);
      retryTimer = null;
    }
  };

  const connect = () => {
    if (intentionalClose) {
      return;
    }

    socket = new WebSocket(buildUrl());
    const current = socket;

    current.onopen = () => {
      retryCount = 0;
      onOpen(current);
    };

    current.onmessage = onMessage;

    current.onerror = () => {
      onDisconnected?.();
    };

    current.onclose = () => {
      onDisconnected?.();
      if (intentionalClose || current !== socket) {
        return;
      }
      if (retryCount >= MAX_WS_RETRIES) {
        return;
      }
      const delay = BASE_WS_RETRY_MS * 2 ** retryCount;
      retryCount += 1;
      retryTimer = setTimeout(connect, delay);
    };
  };

  connect();

  return {
    close: () => {
      intentionalClose = true;
      clearRetryTimer();
      socket?.close();
      socket = null;
    },
  };
}
