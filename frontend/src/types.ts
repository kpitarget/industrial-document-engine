export type RecordStatus = "matched" | "matched_with_warnings" | "exception" | "incomplete" | "ready_for_processing";
export type ApprovalStatus = "pending_review" | "approved" | "approved_with_exceptions" | "rejected";

export type DocumentItem = {
  document_id: number;
  doc_type: string;
  filename: string;
  status: string;
};

export type AuditLogEntry = {
  event: string;
  timestamp: string;
  details: string;
};

export type RecordListItem = {
  record_id: string;
  client_name: string | null;
  work_order_number: string | null;
  employee_id: string | null;
  shift_date: string | null;
  record_status: RecordStatus;
  approval_status: ApprovalStatus;
  created_at: string;
};

export type RecordListResponse = {
  items: RecordListItem[];
  page: number;
  page_size: number;
  total: number;
};

export type UploadResponse = {
  record_id: string;
  status: string;
  documents: DocumentItem[];
};

export type FieldResult = {
  field_key: string;
  status: "match" | "warning" | "mismatch" | "missing";
  severity: "critical" | "warning";
  threshold: number | null;
  values: Record<string, string | null>;
  normalized_values: Record<string, string | null>;
  reason: string | null;
};

export type RecordDetail = {
  record_id: string;
  record_status: RecordStatus;
  approval_status: ApprovalStatus;
  documents: DocumentItem[];
  field_results: FieldResult[];
  audit_log: AuditLogEntry[];
};
