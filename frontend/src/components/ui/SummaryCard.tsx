type SummaryCardProps = {
  label: string;
  value: number;
  tone?: "neutral" | "success" | "warning" | "error";
};

export function SummaryCard({ label, value, tone = "neutral" }: SummaryCardProps) {
  return (
    <article className={`summary-card summary-card--${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}
