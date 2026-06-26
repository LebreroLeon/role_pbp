import { Tooltip } from "../../../../components/ui";

type InspirationBoxProps = {
  active: boolean;
  disabled?: boolean;
  /** Player view: same visual, cannot grant or revoke inspiration. */
  readOnly?: boolean;
  onToggle?: (active: boolean) => void;
};

function inspirationTooltip(active: boolean, readOnly: boolean): string {
  if (readOnly) {
    return active
      ? "Inspiración concedida por el Máster. Puedes gastarla con «Gastar inspiración»."
      : "Sin inspiración. El Máster puede concedértela por buen rol.";
  }

  return active
    ? "Inspiración concedida. El jugador puede gastarla para ventaja en una tirada."
    : "Concede inspiración al personaje (típicamente el Máster la otorga por buen rol).";
}

function InspirationBoxContent({ active }: { active: boolean }) {
  return (
    <>
      <span className="sheet-inspiration__symbol" aria-hidden>
        ✦
      </span>
      <span className="sheet-inspiration__label">Inspiración</span>
      <span className="sheet-inspiration__hint">{active ? "Disponible" : "Sin usar"}</span>
    </>
  );
}

export function InspirationBox({ active, disabled, readOnly = false, onToggle }: InspirationBoxProps) {
  const className = `sheet-inspiration${active ? " is-active" : ""}${readOnly ? " sheet-inspiration--readonly" : ""}`;
  const tooltip = inspirationTooltip(active, readOnly);

  if (readOnly) {
    return (
      <Tooltip content={tooltip}>
        <span
          className={className}
          aria-label={active ? "Inspiración disponible" : "Sin inspiración"}
        >
          <InspirationBoxContent active={active} />
        </span>
      </Tooltip>
    );
  }

  return (
    <Tooltip content={tooltip}>
      <button
        type="button"
        className={className}
        disabled={disabled}
        aria-pressed={active}
        aria-label={active ? "Inspiración activa — pulsa para quitar" : "Sin inspiración — pulsa para conceder"}
        onClick={() => onToggle?.(!active)}
      >
        <InspirationBoxContent active={active} />
      </button>
    </Tooltip>
  );
}

type InspirationSpendToggleProps = {
  active: boolean;
  disabled?: boolean;
  onToggle: (active: boolean) => void;
};

export function InspirationSpendToggle({ active, disabled, onToggle }: InspirationSpendToggleProps) {
  return (
    <Tooltip content="Gastar inspiración — la próxima tirada d20 tendrá ventaja y se consumirá la inspiración">
      <button
        type="button"
        className={`sheet-inspiration-spend${active ? " is-active" : ""}`}
        disabled={disabled}
        aria-pressed={active}
        aria-label={active ? "Gastar inspiración en la próxima tirada" : "Gastar inspiración para ventaja"}
        onClick={() => onToggle(!active)}
      >
        <span className="sheet-inspiration-spend__symbol" aria-hidden>
          ✦
        </span>
        <span>Gastar inspiración</span>
      </button>
    </Tooltip>
  );
}
