import type { ApprovalStatus, RecordStatus } from "../types";

type StatusBadgeProps = {
  status: string | RecordStatus | ApprovalStatus;
};

function normalizeStatus(status: string): string {
  return status.toLowerCase();
}

function statusLabel(status: string): string {
  return status.replace(/_/g, " ");
}

function statusTone(status: string): "success" | "warning" | "error" | "neutral" {
  const normalized = normalizeStatus(status);

  if (["matched", "approved", "match"].includes(normalized)) {
    return "success";
  }
  if (["matched_with_warnings", "approved_with_exceptions", "warning"].includes(normalized)) {
    return "warning";
  }
  if (["exception", "rejected", "mismatch", "missing"].includes(normalized)) {
    return "error";
  }
  return "neutral";
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const tone = statusTone(status);

  return (
    <span className={`badge badge--${tone}`}>
      <span className="badge__dot" aria-hidden="true" />
      {statusLabel(status)}
    </span>
  );
}
