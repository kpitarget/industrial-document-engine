import { useEffect, useState } from "react";

import { getRecord, updateApproval } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ApprovalActionsBar } from "../components/ui/ApprovalActionsBar";
import { StateBlock } from "../components/ui/StateBlock";
import type { RecordDetail } from "../types";

type RecordDetailPageProps = {
  recordId: string | null;
  onCloseRecord: () => void;
};

function prettyFieldName(fieldKey: string): string {
  return fieldKey.replace(/^derived_/, "").replace(/_/g, " ");
}

export function RecordDetailPage({ recordId, onCloseRecord }: RecordDetailPageProps) {
  const [detail, setDetail] = useState<RecordDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function loadDetail(targetRecordId: string) {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getRecord(targetRecordId);
      setDetail(response);
    } catch (detailError) {
      setError(detailError instanceof Error ? detailError.message : "Could not load record details.");
      setDetail(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function runAction(action: "approve" | "approve-with-exceptions" | "reject") {
    if (!detail) return;
    try {
      setIsSubmitting(true);
      await updateApproval(detail.record_id, action);
      await loadDetail(detail.record_id);
      onCloseRecord();
    } catch (actionError) {
      setError(actionError instanceof Error ? actionError.message : "Action failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  useEffect(() => {
    if (recordId) {
      void loadDetail(recordId);
    } else {
      setDetail(null);
    }
  }, [recordId]);

  if (!recordId) {
    return (
      <section className="detail-layout">
        <StateBlock
          title="Record Detail"
          message="Select a record from the queue to review field-level reconciliation and submit approval actions."
          tone="neutral"
        />
      </section>
    );
  }

  if (isLoading) {
    return (
      <section className="detail-layout">
        <StateBlock title="Loading Detail" message="Fetching reconciliation output and audit history..." tone="loading" />
      </section>
    );
  }

  if (error) {
    return (
      <section className="detail-layout">
        <StateBlock title="Detail Error" message={error} tone="error" action={<Button onClick={() => void loadDetail(recordId)}>Retry</Button>} />
      </section>
    );
  }

  if (!detail) {
    return (
      <section className="detail-layout">
        <StateBlock title="No Detail Available" message="No data is currently available for this record." tone="neutral" />
      </section>
    );
  }

  const summaryMeta = [
    { label: "Record ID", value: detail.record_id },
    { label: "Documents", value: String(detail.documents.length) },
    { label: "Field Checks", value: String(detail.field_results.length) },
    { label: "Audit Events", value: String(detail.audit_log.length) },
  ];

  return (
    <section className="detail-layout">
      <Card
        title="Record Detail"
        subtitle="Review comparison results and approve with confidence."
        actions={
          <div className="detail-header-badges">
            <StatusBadge status={detail.record_status} />
            <StatusBadge status={detail.approval_status} />
          </div>
        }
      >
        <div className="meta-grid">
          {summaryMeta.map((item) => (
            <div className="meta-item" key={item.label}>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <ApprovalActionsBar
          disabled={isSubmitting}
          onApprove={() => void runAction("approve")}
          onApproveWithExceptions={() => void runAction("approve-with-exceptions")}
          onReject={() => void runAction("reject")}
        />
      </Card>

      <Card title="Comparison Grid" subtitle="Normalized values across source documents.">
        <div className="table-wrap">
          <table className="data-table data-table--comparison">
            <thead>
              <tr>
                <th>Field</th>
                <th>Client</th>
                <th>Work Order</th>
                <th>Employee</th>
                <th>Status</th>
                <th>Rule Detail</th>
              </tr>
            </thead>
            <tbody>
              {detail.field_results.map((field) => (
                <tr key={field.field_key}>
                  <td>{prettyFieldName(field.field_key)}</td>
                  <td className="mono">{field.normalized_values.client || "-"}</td>
                  <td className="mono">{field.normalized_values.work_order || "-"}</td>
                  <td className="mono">{field.normalized_values.employee || "-"}</td>
                  <td>
                    <StatusBadge status={field.status} />
                  </td>
                  <td>{field.reason || (field.threshold !== null ? `Threshold ${field.threshold}` : "-")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="detail-secondary-grid">
        <Card title="Source Documents" subtitle="Uploaded files in this record.">
          <ul className="document-list">
            {detail.documents.map((document) => (
              <li key={document.document_id}>
                <span>{document.doc_type}</span>
                <strong>{document.filename}</strong>
              </li>
            ))}
          </ul>
        </Card>

        <Card title="Audit Trail" subtitle="Latest processing and approval activity.">
          {detail.audit_log.length === 0 ? (
            <StateBlock title="No Audit Events" message="This record has no audit history yet." />
          ) : (
            <ul className="timeline-list">
              {detail.audit_log.map((entry, index) => (
                <li key={`${entry.timestamp}-${index}`}>
                  <div>
                    <strong>{entry.event.replace(/_/g, " ")}</strong>
                    <p>{entry.details || "No details"}</p>
                  </div>
                  <span>{new Date(entry.timestamp).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </section>
  );
}
