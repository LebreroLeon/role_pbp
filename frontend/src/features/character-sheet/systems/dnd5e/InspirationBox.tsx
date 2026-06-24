import { Tooltip } from "../../../../components/ui";

type InspirationBoxProps = {
  active: boolean;
  disabled?: boolean;
  onToggle: (active: boolean) => void;
};

export function InspirationBox({ active, disabled, onToggle }: InspirationBoxProps) {
  return (
    <Tooltip
      content={
        active
          ? "Inspiración concedida. El jugador puede gastarla para ventaja en una tirada."
          : "Concede inspiración al personaje (típicamente el Máster la otorga por buen rol)."
      }
    >
      <button
        type="button"
        className={`sheet-inspiration${active ? " is-active" : ""}`}
        disabled={disabled}
        aria-pressed={active}
        aria-label={active ? "Inspiración activa — pulsa para quitar" : "Sin inspiración — pulsa para conceder"}
        onClick={() => onToggle(!active)}
      >
        <span className="sheet-inspiration__symbol" aria-hidden>
          ✦
        </span>
        <span className="sheet-inspiration__label">Inspiración</span>
        <span className="sheet-inspiration__hint">{active ? "Disponible" : "Sin usar"}</span>
      </button>
    </Tooltip>
  );
}

type InspirationStatusProps = {
  active: boolean;
};

export function InspirationStatus({ active }: InspirationStatusProps) {
  if (!active) return null;

  return (
    <Tooltip content="Inspiración concedida por el Máster. Puedes gastarla en la barra de tiradas.">
      <span
        className="sheet-inspiration sheet-inspiration--readonly is-active"
        aria-label="Inspiración disponible"
      >
        <span className="sheet-inspiration__symbol" aria-hidden>
          ✦
        </span>
        <span className="sheet-inspiration__label">Inspiración</span>
        <span className="sheet-inspiration__hint">Disponible</span>
      </span>
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
