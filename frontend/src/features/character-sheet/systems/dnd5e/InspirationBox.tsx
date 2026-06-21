type InspirationBoxProps = {
  active: boolean;
  disabled?: boolean;
  onToggle: (active: boolean) => void;
};

export function InspirationBox({ active, disabled, onToggle }: InspirationBoxProps) {
  return (
    <button
      type="button"
      className={`sheet-inspiration${active ? " is-active" : ""}`}
      disabled={disabled}
      aria-pressed={active}
      aria-label={active ? "Inspiración activa — pulsa para quitar" : "Sin inspiración — pulsa para conceder"}
      title={
        active
          ? "Inspiración concedida. El jugador puede gastarla para ventaja en una tirada."
          : "Concede inspiración al personaje (típicamente el Máster la otorga por buen rol)."
      }
      onClick={() => onToggle(!active)}
    >
      <span className="sheet-inspiration__symbol" aria-hidden>
        ✦
      </span>
      <span className="sheet-inspiration__label">Inspiración</span>
      <span className="sheet-inspiration__hint">{active ? "Disponible" : "Sin usar"}</span>
    </button>
  );
}

type InspirationSpendToggleProps = {
  active: boolean;
  disabled?: boolean;
  onToggle: (active: boolean) => void;
};

export function InspirationSpendToggle({ active, disabled, onToggle }: InspirationSpendToggleProps) {
  return (
    <button
      type="button"
      className={`sheet-inspiration-spend${active ? " is-active" : ""}`}
      disabled={disabled}
      aria-pressed={active}
      aria-label={active ? "Gastar inspiración en la próxima tirada" : "Gastar inspiración para ventaja"}
      title="Gastar inspiración — la próxima tirada d20 tendrá ventaja y se consumirá la inspiración"
      onClick={() => onToggle(!active)}
    >
      <span className="sheet-inspiration-spend__symbol" aria-hidden>
        ✦
      </span>
      <span>Gastar inspiración</span>
    </button>
  );
}
