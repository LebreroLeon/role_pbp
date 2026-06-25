import { useEffect, useState } from "react";

import { fetchAuthenticatedBlob } from "../../api/download";

const blobCache = new Map<string, string>();

type ChatMessageImageProps = {
  imageUrl: string;
  alt: string;
  className?: string;
};

function isExternalImageUrl(url: string): boolean {
  return url.startsWith("http://") || url.startsWith("https://");
}

function resolveInitialBlobUrl(url: string | undefined): string | undefined {
  if (!url) return undefined;
  if (isExternalImageUrl(url)) return url;
  return blobCache.get(url);
}

export function ChatMessageImage({ imageUrl, alt, className = "" }: ChatMessageImageProps) {
  const [resolvedUrl, setResolvedUrl] = useState<string | undefined>(() =>
    resolveInitialBlobUrl(imageUrl),
  );
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
    if (!imageUrl) {
      setResolvedUrl(undefined);
      return;
    }

    if (isExternalImageUrl(imageUrl)) {
      setResolvedUrl(imageUrl);
      return;
    }

    const cached = blobCache.get(imageUrl);
    if (cached) {
      setResolvedUrl(cached);
      return;
    }

    let cancelled = false;
    fetchAuthenticatedBlob(imageUrl)
      .then((blob) => {
        if (cancelled) return;
        const objectUrl = URL.createObjectURL(blob);
        blobCache.set(imageUrl, objectUrl);
        setResolvedUrl(objectUrl);
      })
      .catch(() => {
        if (!cancelled) {
          setResolvedUrl(undefined);
          setFailed(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [imageUrl]);

  if (failed) {
    return <p className="muted chat-card__image-error">No se pudo cargar la imagen.</p>;
  }

  if (!resolvedUrl) {
    return <p className="muted chat-card__image-loading">Cargando imagen…</p>;
  }

  return (
    <img
      src={resolvedUrl}
      alt={alt}
      className={["chat-card__image", className].filter(Boolean).join(" ")}
      loading="lazy"
    />
  );
}
