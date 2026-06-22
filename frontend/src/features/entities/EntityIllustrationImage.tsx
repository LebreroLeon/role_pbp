import { useEffect, useState } from "react";

import { fetchAuthenticatedBlob } from "../../api/download";
import { isExternalIllustrationUrl } from "./entityIllustration";

const blobCache = new Map<string, string>();

type EntityIllustrationImageProps = {
  illustrationUrl: string;
  alt: string;
  className?: string;
};

function resolveInitialBlobUrl(url: string | undefined): string | undefined {
  if (!url) return undefined;
  if (isExternalIllustrationUrl(url)) return url;
  return blobCache.get(url);
}

export function EntityIllustrationImage({
  illustrationUrl,
  alt,
  className = "",
}: EntityIllustrationImageProps) {
  const [resolvedUrl, setResolvedUrl] = useState<string | undefined>(() =>
    resolveInitialBlobUrl(illustrationUrl),
  );
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
    if (!illustrationUrl) {
      setResolvedUrl(undefined);
      return;
    }

    if (isExternalIllustrationUrl(illustrationUrl)) {
      setResolvedUrl(illustrationUrl);
      return;
    }

    const cached = blobCache.get(illustrationUrl);
    if (cached) {
      setResolvedUrl(cached);
      return;
    }

    let cancelled = false;
    fetchAuthenticatedBlob(illustrationUrl)
      .then((blob) => {
        if (cancelled) return;
        const objectUrl = URL.createObjectURL(blob);
        blobCache.set(illustrationUrl, objectUrl);
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
  }, [illustrationUrl]);

  if (failed) {
    return <p className="muted entity-illustration-preview__error">No se pudo cargar la ilustración.</p>;
  }

  if (!resolvedUrl) {
    return <p className="muted entity-illustration-preview__loading">Cargando ilustración…</p>;
  }

  return (
    <img
      src={resolvedUrl}
      alt={alt}
      className={["entity-illustration-preview__image", className].filter(Boolean).join(" ")}
    />
  );
}
