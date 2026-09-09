const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
