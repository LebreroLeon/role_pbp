import type { UnreadCounts } from "../../api/types";

type UnreadBadgeProps = {
  count: number;
  label?: string;
};

export function UnreadBadge({ count, label }: UnreadBadgeProps) {
  if (count <= 0) return null;

  const display = count > 99 ? "99+" : String(count);

  return (
    <span className="unread-badge" aria-label={label ?? `${display} mensajes sin leer`}>
      {display}
    </span>
  );
}

export function isUnreadChannel(path: string, channel: "chat" | "ooc"): boolean {
  if (channel === "chat") return /\/chat(\/)?$/.test(path);
  return /\/ooc(\/)?$/.test(path);
}

export function adjustCountsForActiveTab(
  counts: UnreadCounts,
  pathname: string,
): UnreadCounts {
  return {
    play: isUnreadChannel(pathname, "chat") ? 0 : counts.play,
    ooc: isUnreadChannel(pathname, "ooc") ? 0 : counts.ooc,
  };
}
