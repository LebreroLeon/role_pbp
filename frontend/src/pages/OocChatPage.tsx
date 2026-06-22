import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";

import { api } from "../api/client";
import type { OocMessage } from "../api/types";
import { mergeOocMessage, OocChatPanel } from "../features/ooc/OocChatPanel";
import type { OocChannelId } from "../features/ooc/oocChannels";
import { buildOocChannelTabs } from "../features/ooc/oocChannels";
import { useCampaignMembersQuery, useCampaignQuery } from "../hooks/queries/useCampaignQueries";
import { useOocMessagesQuery } from "../hooks/queries/useOocQueries";
import { useCampaignWs } from "../providers/CampaignWsContext";

export function OocChatPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign } = useCampaignQuery(campaignId);
  const { data: members = [] } = useCampaignMembersQuery(campaignId);
  const viewerRole = campaign?.role ?? "PLAYER";
  const [activeChannel, setActiveChannel] = useState<OocChannelId>("all");

  const channelTabs = useMemo(
    () => buildOocChannelTabs(members, viewerRole),
    [members, viewerRole],
  );

  useEffect(() => {
    if (!channelTabs.some((tab) => tab.id === activeChannel)) {
      setActiveChannel("all");
    }
  }, [activeChannel, channelTabs]);

  const { data: channelMessages = [], isLoading } = useOocMessagesQuery(campaignId, activeChannel);
  const [messages, setMessages] = useState<OocMessage[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [sending, setSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (channelMessages.length === 0) return;
    setMessages((current) => {
      let next = current;
      for (const message of channelMessages) {
        next = mergeOocMessage(next, message);
      }
      return next;
    });
    setHydrated(true);
  }, [channelMessages]);

  const handleSnapshot = useCallback((snapshot: OocMessage[]) => {
    setMessages(snapshot);
    setHydrated(true);
  }, []);

  const handleMessage = useCallback((message: OocMessage) => {
    setMessages((current) => mergeOocMessage(current, message));
    setHydrated(true);
  }, []);

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
        setMessages((current) => mergeOocMessage(current, message));
        setHydrated(true);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No se pudo enviar el mensaje");
      } finally {
        setSending(false);
      }
    },
    [campaignId],
  );

  const sendWhisper = useCallback(
    async (content: string, targetUserId: string) => {
      setSending(true);
      setErrorMessage(null);
      try {
        const message = await api.postOocWhisper(campaignId, content, targetUserId);
        setMessages((current) => mergeOocMessage(current, message));
        setHydrated(true);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : "No se pudo enviar el mensaje privado");
      } finally {
        setSending(false);
      }
    },
    [campaignId],
  );

  const markOocRead = useCallback(() => {
    api.markOocRead(campaignId).catch(() => undefined);
  }, [campaignId]);

  useEffect(() => {
    if (!hydrated && channelMessages.length === 0) return;
    const timer = setTimeout(markOocRead, 400);
    return () => clearTimeout(timer);
  }, [hydrated, channelMessages.length, messages.length, activeChannel, markOocRead]);

  if (isLoading && !hydrated) {
    return <p className="muted">Cargando chat OOC...</p>;
  }

  return (
    <div className="ooc-page">
      <OocChatPanel
        members={members}
        viewerRole={viewerRole}
        messages={messages}
        activeChannel={activeChannel}
        onChannelChange={setActiveChannel}
        connected={connected}
        sending={sending}
        errorMessage={errorMessage}
        onSendPublic={sendPublic}
        onSendWhisper={sendWhisper}
      />
    </div>
  );
}
