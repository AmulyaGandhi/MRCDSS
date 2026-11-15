import { API_BASE } from './client';

export type AssistantContext = {
  state: string | null;
  district: string | null;
  matched: boolean;
  risk_class: string | null;
  topic?: string | null;
};

export type AssistantResponse = {
  answer: string;
  grounded: boolean;
  sources: string[];
  mode: 'ollama' | 'groq' | 'fallback' | 'general';
  intent: string;
  context: AssistantContext | null;
};

export type AssistantTurn = { role: 'user' | 'assistant'; text: string };

export type AssistantPageContext =
  | 'overview'
  | 'district_explorer'
  | 'risk_analysis'
  | 'planning_priorities'
  | 'methodology'
  | 'about';

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json() as T;
}

export function assistantChat(params: {
  message: string;
  state?: string | null;
  district?: string | null;
  page_context?: AssistantPageContext | null;
  history?: AssistantTurn[];
  scope?: AssistantContext | null;
}): Promise<AssistantResponse> {
  return apiPost<AssistantResponse>('/api/assistant/chat', {
    message: params.message,
    state: params.state ?? undefined,
    district: params.district ?? undefined,
    page_context: params.page_context ?? undefined,
    history: params.history ?? undefined,
    scope: params.scope ?? undefined,
  });
}