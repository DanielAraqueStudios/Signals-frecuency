import { apiRequest } from "./client";

// Fixed contract (not yet built server-side, see api-gateway plan):
// POST /images -> multipart form, one file field "image"
// GET  /images -> array of past results for the logged-in user
export interface ClassificationResult {
  label: string;
  confidence: number | null;
  stub: boolean;
  reason?: string;
}

export interface ImageRecord extends ClassificationResult {
  id: string;
  createdAt: string;
}

export async function uploadImage(uri: string): Promise<ClassificationResult> {
  const filename = uri.split("/").pop() ?? "capture.jpg";
  const match = /\.(\w+)$/.exec(filename);
  const ext = match ? match[1].toLowerCase() : "jpg";
  const mimeType = ext === "png" ? "image/png" : "image/jpeg";

  const formData = new FormData();
  // React Native's FormData accepts this { uri, name, type } shape for
  // file fields; it is not a real Blob/File on-device.
  formData.append("image", {
    uri,
    name: filename,
    type: mimeType,
  } as unknown as Blob);

  const response = await apiRequest("/images", {
    method: "POST",
    body: formData,
    // Do not set Content-Type manually — fetch/RN must generate the
    // multipart boundary itself.
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body?.detail ?? body?.message ?? `Upload failed (${response.status})`
    );
  }
  return response.json();
}

export async function listImages(): Promise<ImageRecord[]> {
  const response = await apiRequest("/images", { method: "GET" });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(
      body?.detail ?? body?.message ?? `Failed to load history (${response.status})`
    );
  }
  return response.json();
}
