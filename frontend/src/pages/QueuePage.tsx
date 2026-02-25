import { useEffect, useMemo, useState } from "react";

import { getRecords, processRecord, uploadRecord } from "../api";
import { StatusBadge } from "../components/StatusBadge";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { StateBlock } from "../components/ui/StateBlock";
import { SummaryCard } from "../components/ui/SummaryCard";
import type { ApprovalStatus, RecordListItem, RecordStatus } from "../types";

type QueuePageProps = {
  selectedRecordId: string | null;
  onSelectRecord: (recordId: string) => void;
};

export function QueuePage({ selectedRecordId, onSelectRecord }: QueuePageProps) {
  const [records, setRecords] = useState<RecordListItem[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<RecordStatus | "all">("all");
  const [approvalFilter, setApprovalFilter] = useState<ApprovalStatus | "all">("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const [clientDocument, setClientDocument] = useState<File | null>(null);
  const [workOrderDocument, setWorkOrderDocument] = useState<File | null>(null);
  const [employeeDocument, setEmployeeDocument] = useState<File | null>(null);

  async function loadRecords() {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getRecords(search);
      setRecords(response.items);
      if (!selectedRecordId && response.items.length > 0) {
        onSelectRecord(response.items[0].record_id);
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load queue.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadRecords();
  }, []);

  const filteredRecords = useMemo(() => {
    return records.filter((record) => {
      if (statusFilter !== "all" && record.record_status !== statusFilter) {
        return false;
      }
      if (approvalFilter !== "all" && record.approval_status !== approvalFilter) {
        return false;
      }
      if (dateFrom && record.shift_date && record.shift_date < dateFrom) {
        return false;
      }
      if (dateTo && record.shift_date && record.shift_date > dateTo) {
        return false;
      }
      return true;
    });
  }, [approvalFilter, dateFrom, dateTo, records, statusFilter]);

  const summary = useMemo(() => {
    const processed = records.length;
    const exceptions = records.filter((record) => record.record_status === "exception").length;
    const pendingReview = records.filter((record) => record.approval_status === "pending_review").length;
    const approved = records.filter((record) => ["approved", "approved_with_exceptions"].includes(record.approval_status)).length;

    return { processed, exceptions, pendingReview, approved };
  }, [records]);

  const selectedRecord = filteredRecords.find((record) => record.record_id === selectedRecordId) || null;

  return (
    <section className="queue-layout">
      <Card
        title="Record Queue"
        subtitle="Track processed records and triage exceptions quickly."
        actions={
          <Button onClick={() => void loadRecords()} disabled={isLoading} size="sm" variant="ghost">
            {isLoading ? "Refreshing..." : "Refresh"}
          </Button>
        }
      >
        <div className="summary-grid">
          <SummaryCard label="Processed" value={summary.processed} tone="neutral" />
          <SummaryCard label="Exceptions" value={summary.exceptions} tone="error" />
          <SummaryCard label="Pending Review" value={summary.pendingReview} tone="warning" />
          <SummaryCard label="Approved" value={summary.approved} tone="success" />
        </div>

        <div className="filters-grid">
          <label className="filter-search">
            Search
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Work order or employee"
            />
          </label>
          <label className="filter-record-status">
            Record Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as RecordStatus | "all")}> 
              <option value="all">All</option>
              <option value="matched">Matched</option>
              <option value="matched_with_warnings">Matched w/ warnings</option>
              <option value="exception">Exception</option>
              <option value="incomplete">Incomplete</option>
              <option value="ready_for_processing">Ready for processing</option>
            </select>
          </label>
          <label className="filter-approval">
            Approval
            <select value={approvalFilter} onChange={(event) => setApprovalFilter(event.target.value as ApprovalStatus | "all")}> 
              <option value="all">All</option>
              <option value="pending_review">Pending review</option>
              <option value="approved">Approved</option>
              <option value="approved_with_exceptions">Approved w/ exceptions</option>
              <option value="rejected">Rejected</option>
            </select>
          </label>
          <label className="filter-date-from">
            Date From
            <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
          </label>
          <label className="filter-date-to">
            Date To
            <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
          </label>
          <div className="filters-actions">
            <Button onClick={() => void loadRecords()} disabled={isLoading} variant="secondary">
              Apply
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setStatusFilter("all");
                setApprovalFilter("all");
                setDateFrom("");
                setDateTo("");
              }}
            >
              Clear
            </Button>
          </div>
        </div>
      </Card>

      <Card title="Upload & Process" subtitle="Attach all 3 PDFs to create a reconciliation record.">
        <div className="upload-grid">
          <label>
            Client PDF
            <input type="file" accept="application/pdf" onChange={(event) => setClientDocument(event.target.files?.[0] ?? null)} />
          </label>
          <label>
            Work Order PDF
            <input type="file" accept="application/pdf" onChange={(event) => setWorkOrderDocument(event.target.files?.[0] ?? null)} />
          </label>
          <label>
            Employee PDF
            <input type="file" accept="application/pdf" onChange={(event) => setEmployeeDocument(event.target.files?.[0] ?? null)} />
          </label>
          <Button
            variant="primary"
            fullWidth
            disabled={isUploading}
            onClick={async () => {
              if (!clientDocument || !workOrderDocument || !employeeDocument) {
                setError("Choose all three PDF files before upload.");
                return;
              }
              try {
                setIsUploading(true);
                setError(null);
                const uploaded = await uploadRecord({ clientDocument, workOrderDocument, employeeDocument });
                await processRecord(uploaded.record_id);
                await loadRecords();
                onSelectRecord(uploaded.record_id);
              } catch (uploadError) {
                setError(uploadError instanceof Error ? uploadError.message : "Upload failed.");
              } finally {
                setIsUploading(false);
              }
            }}
          >
            {isUploading ? "Uploading..." : "Upload + Process"}
          </Button>
        </div>
      </Card>

      {error ? <StateBlock title="Queue Error" message={error} tone="error" /> : null}

      <Card
        title="Records"
        subtitle={filteredRecords.length > 0 ? `${filteredRecords.length} record(s)` : "No records found"}
        actions={
          <Button
            size="sm"
            onClick={async () => {
              if (!selectedRecordId) return;
              try {
                setIsProcessing(true);
                setError(null);
                await processRecord(selectedRecordId);
                await loadRecords();
              } catch (processingError) {
                setError(processingError instanceof Error ? processingError.message : "Processing failed.");
              } finally {
                setIsProcessing(false);
              }
            }}
            disabled={!selectedRecordId || isProcessing}
          >
            {isProcessing ? "Reprocessing..." : "Reprocess Selected"}
          </Button>
        }
      >
        {isLoading ? <StateBlock title="Loading Queue" message="Fetching latest records..." tone="loading" /> : null}

        {!isLoading && filteredRecords.length === 0 ? (
          <StateBlock
            title="No Records"
            message="Upload a complete document set or adjust filters to find records."
            tone="neutral"
          />
        ) : null}

        {!isLoading && filteredRecords.length > 0 ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Work Order</th>
                  <th>Employee</th>
                  <th>Shift Date</th>
                  <th>Record Status</th>
                  <th>Approval</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((record) => (
                  <tr
                    key={record.record_id}
                    className={record.record_id === selectedRecordId ? "is-active" : ""}
                    onClick={() => onSelectRecord(record.record_id)}
                  >
                    <td>{record.work_order_number || "-"}</td>
                    <td>
                      <div className="row-title">{record.employee_id || "Unknown"}</div>
                      <div className="row-subtitle">{record.client_name || "Unknown client"}</div>
                    </td>
                    <td>{record.shift_date || "-"}</td>
                    <td>
                      <StatusBadge status={record.record_status} />
                    </td>
                    <td>
                      <StatusBadge status={record.approval_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}

        {selectedRecord ? (
          <p className="selection-caption">
            Selected: <strong>{selectedRecord.work_order_number || selectedRecord.record_id}</strong>
          </p>
        ) : null}
      </Card>
    </section>
  );
}
