import type { RecordDetail, RecordListResponse, UploadResponse } from "./types";

const apiBase = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  let errorMessage = "Request failed";
  try {
    const payload = await response.json();
    if (payload?.message && typeof payload.message === "string") {
      errorMessage = payload.message;
    }
  } catch {
    errorMessage = `Request failed (${response.status})`;
  }
  throw new Error(errorMessage);
}

export async function getRecords(search = ""): Promise<RecordListResponse> {
  const query = search ? `?q=${encodeURIComponent(search)}` : "";
  const response = await fetch(`${apiBase}/records${query}`);
  return parseResponse<RecordListResponse>(response);
}

export async function getRecord(recordId: string): Promise<RecordDetail> {
  const response = await fetch(`${apiBase}/records/${recordId}`);
  return parseResponse<RecordDetail>(response);
}

export async function processRecord(recordId: string): Promise<void> {
  const response = await fetch(`${apiBase}/records/${recordId}/process`, { method: "POST" });
  await parseResponse<unknown>(response);
}

export async function updateApproval(recordId: string, action: "approve" | "approve-with-exceptions" | "reject"): Promise<void> {
  const response = await fetch(`${apiBase}/records/${recordId}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewer_name: "Local Reviewer", notes: "Updated in MVP review UI" }),
  });

  await parseResponse<unknown>(response);
}

export async function uploadRecord(files: {
  clientDocument: File | null;
  workOrderDocument: File | null;
  employeeDocument: File | null;
}): Promise<UploadResponse> {
  const formData = new FormData();
  if (files.clientDocument) formData.append("client_document", files.clientDocument);
  if (files.workOrderDocument) formData.append("work_order_document", files.workOrderDocument);
  if (files.employeeDocument) formData.append("employee_document", files.employeeDocument);

  const response = await fetch(`${apiBase}/records/upload`, {
    method: "POST",
    body: formData,
  });
  return parseResponse<UploadResponse>(response);
}
