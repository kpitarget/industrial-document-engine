# UAT_TEST_PLAN.md
## Phase 1 MVP User Acceptance Test Plan

## Purpose
Validate that the MVP supports the intended workflow:
upload → process → reconcile → review → approve → SharePoint file

---

## UAT Roles
- **Ops Reviewer**
- **Admin / Processor**
- **Project Lead**

---

## Required Test Data
Prepare at least:
- 10 complete record sets (3 PDFs each)
- Mix of:
  - perfect matches
  - warnings (name/location differences)
  - critical mismatches (hours/date/ID)
  - missing fields
  - scanned PDFs (if in scope for MVP testing)

---

## Test Scenarios

### UAT-01: Upload a complete 3-document set
**Steps**
1. Upload client, work order, and employee PDFs
2. Confirm record created

**Expected**
- Record is created
- 3 documents are attached
- Status shows `ready_to_process` or equivalent

---

### UAT-02: Process record and view reconciliation
**Steps**
1. Trigger processing
2. Open record detail page

**Expected**
- Field-level comparison results displayed
- Record status calculated
- Mismatches highlighted

---

### UAT-03: Exact match validation
**Expected**
- `employee_id`, `work_order_number`, `shift_date` show match when identical after normalization

---

### UAT-04: Tolerance validation for total_hours
**Expected**
- Difference within ±0.25 = pass/warning per rule
- Difference > ±0.25 = exception

---

### UAT-05: Missing required field handling
**Expected**
- Missing required field flagged
- Record status becomes `exception` or `incomplete` depending on context

---

### UAT-06: Approve matched record
**Steps**
1. Open a matched record
2. Click Approve

**Expected**
- Approval status updates to `approved`
- Audit log entry created

---

### UAT-07: Approve with exceptions
**Steps**
1. Open record with mismatch
2. Click Approve with Exceptions
3. Add note

**Expected**
- Approval status updates
- Note is saved
- Audit log entry includes reviewer and note

---

### UAT-08: Reject record
**Expected**
- Status updates to `rejected`
- Audit log captures action

---

### UAT-09: SharePoint upload on approved record
**Steps**
1. Approve a record
2. Trigger SharePoint upload

**Expected**
- Upload succeeds (mock or real, depending on environment)
- Destination path logged
- Upload status visible in UI

---

### UAT-10: SharePoint retry on failure
**Expected**
- Failed upload can be retried
- Retry count increments
- Success/failure is logged

---

## UAT Signoff Criteria
All of the following must pass:
- Upload flow
- Processing + reconciliation
- Review/approval actions
- SharePoint upload flow
- Basic queue filters/search
- Audit logging for approvals and uploads

---

## Defect Severity Guide
- **Critical:** prevents processing, approval, or upload
- **High:** incorrect statuses or wrong comparison results
- **Medium:** UI issues or non-blocking logic bugs
- **Low:** cosmetic or minor usability issues
