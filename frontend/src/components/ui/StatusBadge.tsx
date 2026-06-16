type StatusBadgeProps = {
  label: string;
  value: string;
  ok?: boolean;
};

export function StatusBadge({ label, value, ok }: StatusBadgeProps) {
  return (
    <div className="status-pill">
      {label ? <span className="status-pill__label">{label}</span> : null}
      <span className={`status-pill__value ${ok ? "is-ok" : "is-warn"}`}>
        <span className="status-pill__dot" aria-hidden />
        {value}
      </span>
    </div>
  );
}
