# API_SPEC.md
## Phase 1 MVP API Contract (Draft)

This is a practical API contract for Codex to scaffold quickly. Responses can be refined later.

## Conventions
- Base path: `/api`
- JSON responses
- ISO timestamps
- Errors include `code`, `message`, `details`

---

## `POST /api/records/upload`
Upload one or more PDFs and assign document types.

### Request (multipart/form-data)
Fields:
- `record_group_key` (optional string; if omitted, create new record)
- `client_document` (file, optional)
- `work_order_document` (file, optional)
- `employee_document` (file, optional)
- or generic array with `doc_type` metadata

### Response
```json
{
  "record_id": "rec_123",
  "status": "incomplete",
  "documents": [
    {"document_id":"doc_1","doc_type":"client","status":"uploaded"},
    {"document_id":"doc_2","doc_type":"work_order","status":"uploaded"},
    {"document_id":"doc_3","doc_type":"employee","status":"uploaded"}
  ]
}
```

---

## `POST /api/records/{record_id}/process`
Runs extraction (mock/real) and reconciliation.

### Response
```json
{
  "record_id": "rec_123",
  "record_status": "matched_with_warnings",
  "field_results": [
    {
      "field_key": "employee_id",
      "status": "match",
      "severity": "critical",
      "values": {
        "client": "E10352",
        "work_order": "E10352",
        "employee": "E10352"
      }
    }
  ]
}
```

---

## `GET /api/records`
List records with filters.

### Query params (optional)
- `status`
- `client_id`
- `date_from`
- `date_to`
- `q` (search by work order or employee id)
- `page`
- `page_size`

### Response
```json
{
  "items": [
    {
      "record_id": "rec_123",
      "client_name": "Acme",
      "work_order_number": "WO4412",
      "employee_id": "E10352",
      "shift_date": "2026-02-20",
      "record_status": "exception",
      "approval_status": "pending_review",
      "created_at": "2026-02-24T12:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 25,
  "total": 1
}
```

---

## `GET /api/records/{record_id}`
Get full record detail.

### Response
```json
{
  "record_id": "rec_123",
  "record_status": "exception",
  "approval_status": "pending_review",
  "documents": [
    {"document_id":"doc_1","doc_type":"client","filename":"client.pdf"},
    {"document_id":"doc_2","doc_type":"work_order","filename":"workorder.pdf"},
    {"document_id":"doc_3","doc_type":"employee","filename":"employee.pdf"}
  ],
  "field_results": [
    {
      "field_key": "total_hours",
      "label": "Total Hours",
      "status": "mismatch",
      "severity": "critical",
      "threshold": 0.25,
      "values": {"client":"8.0","work_order":"8.0","employee":"7.5"},
      "normalized_values": {"client":"8.00","work_order":"8.00","employee":"7.50"},
      "reason": "Variance exceeds tolerance"
    }
  ],
  "audit_log": [
    {"event":"record_created","timestamp":"2026-02-24T12:00:00Z"}
  ]
}
```

---

## `POST /api/records/{record_id}/approve`
Approve a record.

### Request
```json
{
  "reviewer_name": "Mike Rowan",
  "notes": "Approved after reviewing time difference."
}
```

### Response
```json
{
  "record_id": "rec_123",
  "approval_status": "approved",
  "approved_at": "2026-02-24T15:00:00Z"
}
```

---

## `POST /api/records/{record_id}/approve-with-exceptions`
Approve while preserving exceptions.

### Request
```json
{
  "reviewer_name": "Mike Rowan",
  "notes": "Client confirmed employee-submitted hours should be used."
}
```

### Response
```json
{
  "record_id": "rec_123",
  "approval_status": "approved_with_exceptions"
}
```

---

## `POST /api/records/{record_id}/reject`
Reject a record.

### Request
```json
{
  "reviewer_name": "Mike Rowan",
  "notes": "Missing employee signature."
}
```

### Response
```json
{
  "record_id": "rec_123",
  "approval_status": "rejected"
}
```

---

## `POST /api/records/{record_id}/sharepoint-upload`
Trigger SharePoint upload (or mock upload in dev).

### Response
```json
{
  "record_id": "rec_123",
  "upload_status": "success",
  "destination_path": "/Clients/Acme/Invoices/",
  "files_uploaded": 3
}
```

---

## `POST /api/records/{record_id}/sharepoint-retry`
Retry failed upload.

### Response
```json
{
  "record_id": "rec_123",
  "upload_status": "success",
  "retry_count": 1
}
```

---

## `GET /api/sharepoint-mappings`
List client mapping rows.

## `POST /api/sharepoint-mappings`
Create mapping.

## `PUT /api/sharepoint-mappings/{id}`
Update mapping.

### Mapping payload example
```json
{
  "client_name": "Acme",
  "client_id": "102",
  "site_id": "site123",
  "library_id": "lib456",
  "folder_path": "/Clients/Acme/Invoices",
  "is_active": true
}
```

---

## `GET /api/metrics/summary`
Basic dashboard metrics.

### Response
```json
{
  "records_processed": 120,
  "matched": 72,
  "matched_with_warnings": 28,
  "exceptions": 20,
  "approved": 90,
  "approved_with_exceptions": 12,
  "rejected": 18,
  "upload_failures": 3
}
```
