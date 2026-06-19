import { useEffect, useState } from "react";

import { fetchAuthenticatedBlob } from "../../api/download";
import { isExternalAvatarUrl } from "../entities/entityAvatar";
import { getInitials } from "./messageTypes";

const blobCache = new Map<string, string>();

type ChatAvatarProps = {
  name: string;
  avatarUrl?: string;
  className?: string;
};

function resolveInitialBlobUrl(url: string | undefined): string | undefined {
  if (!url) return undefined;
  if (isExternalAvatarUrl(url)) return url;
  return blobCache.get(url);
}

export function ChatAvatar({ name, avatarUrl, className = "" }: ChatAvatarProps) {
  const [resolvedUrl, setResolvedUrl] = useState<string | undefined>(() =>
    resolveInitialBlobUrl(avatarUrl),
  );

  useEffect(() => {
    if (!avatarUrl) {
      setResolvedUrl(undefined);
      return;
    }

    if (isExternalAvatarUrl(avatarUrl)) {
      setResolvedUrl(avatarUrl);
      return;
    }

    const cached = blobCache.get(avatarUrl);
    if (cached) {
      setResolvedUrl(cached);
      return;
    }

    let cancelled = false;
    fetchAuthenticatedBlob(avatarUrl)
      .then((blob) => {
        if (cancelled) return;
        const objectUrl = URL.createObjectURL(blob);
        blobCache.set(avatarUrl, objectUrl);
        setResolvedUrl(objectUrl);
      })
      .catch(() => {
        if (!cancelled) setResolvedUrl(undefined);
      });

    return () => {
      cancelled = true;
    };
  }, [avatarUrl]);

  const classes = ["chat-card__avatar", className].filter(Boolean).join(" ");

  if (resolvedUrl) {
    return <img src={resolvedUrl} alt="" className={`${classes} chat-card__avatar--image`} />;
  }

  return (
    <span className={classes} aria-hidden>
      {getInitials(name)}
    </span>
  );
}
