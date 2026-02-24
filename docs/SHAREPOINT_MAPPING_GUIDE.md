# SHAREPOINT_MAPPING_GUIDE.md
## SharePoint Filing Setup for Phase 1 MVP

This guide defines how the app maps approved records to client-specific SharePoint folders.

## Goal
When a record is approved, upload the 3 PDFs into the correct client folder, typically:

`/Clients/{ClientName}/Invoices/`

---

## Mapping Strategy (Phase 1)
Use a controlled mapping table in the application/database.

### Recommended mapping fields
- `client_id` (optional but preferred)
- `client_name` (normalized)
- `site_id`
- `library_id`
- `folder_path`
- `is_active`

### Why not infer dynamically?
Dynamic matching increases risk of filing to the wrong folder.
A mapping table is safer and easier to audit.

---

## Example Mapping Rows

| client_name | client_id | site_id | library_id | folder_path | active |
|---|---|---|---|---|---|
| Acme | 102 | site_abc | lib_docs | /Clients/Acme/Invoices | Y |
| Delta Industrial | 205 | site_abc | lib_docs | /Clients/Delta Industrial/Invoices | Y |

---

## Upload Conditions
Only upload when:
- approval status = `approved` or `approved_with_exceptions`
- all 3 PDFs are present (or business allows partial uploads — confirm before enabling)

---

## File Naming Convention
Use:
`[Client]_[WorkOrder]_[EmployeeID]_[ShiftDate]_[DocType].pdf`

### Examples
- `Acme_WO4412_E10352_2026-02-20_Client.pdf`
- `Acme_WO4412_E10352_2026-02-20_WorkOrder.pdf`
- `Acme_WO4412_E10352_2026-02-20_Employee.pdf`

### Filename sanitation
Before upload:
- replace slashes and illegal path characters
- trim spaces
- cap length if needed

---

## Recommended Metadata to Store (App DB)
Store these values even if SharePoint metadata columns are not implemented in MVP:
- `record_id`
- `client_name`
- `work_order_number`
- `employee_id`
- `shift_date`
- `approval_status`
- `uploaded_at`
- `upload_result`
- `destination_path`

---

## Error Handling
If upload fails:
1. Save error message and attempt timestamp
2. Keep record approval intact
3. Mark upload status `failed`
4. Allow retry from UI

---

## Phase 2 Enhancements (Later)
- Create missing folders automatically
- Write SharePoint metadata columns
- Upload reconciliation summary PDF/CSV
- Bulk upload retries
- Notifications on failed uploads
