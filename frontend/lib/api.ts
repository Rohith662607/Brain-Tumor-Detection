// REPLACES frontend/lib/api.ts (v3 — adds assistantChat())

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export interface DetectionBox {
  class_id: number;
  class_name: "negative" | "positive" | string;
  confidence: number;
  bbox_xyxy: [number, number, number, number];
  area_px: number;
  area_pct_of_image: number | null;
}

export interface DetectionSummary {
  id: number;
  created_at: string;
  original_filename: string;
  tumor_detected: boolean;
  num_detections: number;
  total_tumor_area_pct: number;
  annotated_image_url: string | null;
  pdf_report_url: string | null;
}

export interface DetectionDetail extends DetectionSummary {
  detections: DetectionBox[];
  model_weights: string;
  ai_report: string | null;
}

export interface HistoryPage {
  total_returned: number;
  limit: number;
  offset: number;
  items: DetectionSummary[];
}

export interface ModelInfo {
  weights_path: string;
  class_names: string[];
  image_size: number;
  conf_threshold: number;
  iou_threshold: number;
  device: string;
}

export interface HealthStatus {
  status: string;
  model_loaded: boolean;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string | null;
  history: ChatMessage[];
}

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  detect(file: File): Promise<DetectionDetail> {
    const form = new FormData();
    form.append("file", file);
    return request<DetectionDetail>("/api/detect", { method: "POST", body: form });
  },

  history(limit = 30, offset = 0): Promise<HistoryPage> {
    return request<HistoryPage>(`/api/history?limit=${limit}&offset=${offset}`);
  },

  historyDetail(id: number): Promise<DetectionDetail> {
    return request<DetectionDetail>(`/api/history/${id}`);
  },

  deleteDetection(id: number): Promise<{ deleted: number }> {
    return request(`/api/history/${id}`, { method: "DELETE" });
  },

  modelInfo(): Promise<ModelInfo> {
    return request<ModelInfo>("/api/model/info");
  },

  health(): Promise<HealthStatus> {
    return request<HealthStatus>("/api/health");
  },

  imageUrl(path: string): string {
    return `${API_BASE}${path}`;
  },

  reportUrl(path: string): string {
    return `${API_BASE}${path}`;
  },

  // --- AI report (on-demand) ---
  generateReport(id: number): Promise<DetectionDetail> {
    return request<DetectionDetail>(`/api/history/${id}/report`, { method: "POST" });
  },

  // --- Per-scan chat ---
  getChat(id: number): Promise<ChatResponse> {
    return request<ChatResponse>(`/api/history/${id}/chat`);
  },

  sendChatMessage(id: number, message: string): Promise<ChatResponse> {
    return request<ChatResponse>(`/api/history/${id}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
  },

  // --- Global Assistant (app-wide, grounded in the full history index) ---
  assistantChat(message: string, history: ChatMessage[]): Promise<ChatResponse> {
    return request<ChatResponse>(`/api/assistant/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, history }),
    });
  },
};

export { ApiError };
