import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import type { OocMessage } from "../api/types";
import { mergeOocMessage, OocChatPanel } from "../features/ooc/OocChatPanel";
import { useCampaignMembersQuery } from "../hooks/queries/useCampaignQueries";
import { useOocMessagesQuery } from "../hooks/queries/useOocQueries";
import { useCampaignWs } from "../providers/CampaignWsContext";

export function OocChatPage() {
  const { campaignId = "" } = useParams();
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const { data: initialMessages = [], isLoading } = useOocMessagesQuery(campaignId);
  const [messages, setMessages] = useState<OocMessage[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [sending, setSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const visibleMessages = hydrated ? messages : initialMessages;

  const handleSnapshot = useCallback((snapshot: OocMessage[]) => {
    setMessages(snapshot);
    setHydrated(true);
  }, []);

  const handleMessage = useCallback(
    (message: OocMessage) => {
      setMessages((current) => mergeOocMessage(current.length > 0 ? current : initialMessages, message));
      setHydrated(true);
    },
    [initialMessages],
  );

  const { connected, registerOocHandlers } = useCampaignWs();

  useEffect(() => {
    registerOocHandlers({
      onSnapshot: handleSnapshot,
      onMessage: handleMessage,
      onError: setErrorMessage,
    });
    return () => registerOocHandlers(null);
  }, [handleSnapshot, handleMessage, registerOocHandlers]);

  const sendPublic = useCallback(
    async (content: string) => {
      setSending(true);
      setErrorMessage(null);
      try {
        const message = await api.postOocMessage(campaignId, content);
        setMessages((current) => mergeOocMessage(current.length > 0 ? current : initialMessages, message));
        setHydrated(true);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No se pudo enviar el mensaje");
      } finally {
        setSending(false);
      }
    },
    [campaignId, initialMessages],
  );

  const sendWhisper = useCallback(
    async (content: string, targetUserId: string) => {
      setSending(true);
      setErrorMessage(null);
      try {
        const message = await api.postOocWhisper(campaignId, content, targetUserId);
        setMessages((current) => mergeOocMessage(current.length > 0 ? current : initialMessages, message));
        setHydrated(true);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No se pudo enviar el susurro");
      } finally {
        setSending(false);
      }
    },
    [campaignId, initialMessages],
  );

  if (isLoading && !hydrated) {
    return <p className="muted">Cargando chat OOC...</p>;
  }

  return (
    <div className="ooc-page">
      <OocChatPanel
        campaignId={campaignId}
        members={members}
        messages={visibleMessages}
        connected={connected}
        sending={sending}
        errorMessage={errorMessage}
        onSendPublic={sendPublic}
        onSendWhisper={sendWhisper}
      />
    </div>
  );
}
