type StatusBadgeProps = {
  label: string;
  value: string;
  ok?: boolean;
};

export function StatusBadge({ label, value, ok }: StatusBadgeProps) {
  return (
    <div className="status-row">
      <span>{label}</span>
      <strong className={ok ? "ok" : "warn"}>{value}</strong>
    </div>
  );
}
