const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options) {
  const response = await fetch(`${API_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || "The API request failed.");
  }
  return response.json();
}

export function uploadDocument(file) {
  const body = new FormData();
  body.append("file", file);
  return request("/documents/upload", { method: "POST", body });
}

export function listVectors() {
  return request("/vectors");
}

export function deleteVector(vectorId) {
  return request(`/vectors/${vectorId}`, { method: "DELETE" });
}

export function runAttack(payload) {
  return request("/attacks/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function reportUrl(experimentId) {
  return `${API_URL}/reports/${experimentId}/download`;
}

export async function runExperiment(payload) {
  const response = await fetch(`${API_URL}/experiments/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("The experiment could not be completed.");
  return response.json();
}

export async function listExperiments() {
  const response = await fetch(`${API_URL}/experiments`);
  if (!response.ok) throw new Error("The experiment history is unavailable.");
  return response.json();
}
