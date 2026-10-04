const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000";

function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("task_manager_token") || "";
}

async function request(path: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(body.error || "Request failed");
  }

  return body;
}

export function loginWithGoogle(credential: string) {
  return request("/api/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

export function getUsers() {
  return request("/api/users");
}

export function getTasks() {
  return request("/api/tasks");
}

export function createTask(payload: {
  title: string;
  description: string;
  assigned_to: string;
}) {
  return request("/api/tasks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function completeTask(taskId: string) {
  return request(`/api/tasks/${taskId}/complete`, {
    method: "PATCH",
  });
}
