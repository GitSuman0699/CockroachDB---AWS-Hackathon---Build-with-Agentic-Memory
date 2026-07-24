export const API_BASE_URL = "http://localhost:8000/api";

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface MemoryItem {
  id: string;
  content: string;
  category?: string;
  importance?: number;
  pattern?: string;
  pattern_type?: string;
}

export interface MemoryContext {
  [key: string]: string;
}

/**
 * Send a message to the agent and get a response.
 */
export async function sendChatMessage(
  sessionId: string,
  message: string,
  userId: string = "default"
): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: userId,
      session_id: sessionId,
      message,
    }),
  });

  if (!res.ok) {
    throw new Error(`Chat API error: ${res.statusText}`);
  }

  const data = await res.json();
  return data.response;
}

/**
 * Trigger memory consolidation for a session.
 */
export async function consolidateSession(
  sessionId: string,
  userId: string = "default"
) {
  const res = await fetch(
    `${API_BASE_URL}/session/consolidate?session_id=${sessionId}&user_id=${userId}`,
    {
      method: "POST",
    }
  );

  if (!res.ok) {
    throw new Error(`Consolidation error: ${res.statusText}`);
  }

  return await res.json();
}

/**
 * Fetch Working Memory (Active Context)
 */
export async function getWorkingMemory(sessionId: string): Promise<MemoryContext> {
  const res = await fetch(`${API_BASE_URL}/memory/working?session_id=${sessionId}`);
  if (!res.ok) return {};
  const data = await res.json();
  return data.context || {};
}

/**
 * Fetch Semantic Memory (Knowledge Base)
 */
export async function getSemanticMemory(userId: string = "default"): Promise<MemoryItem[]> {
  const res = await fetch(`${API_BASE_URL}/memory/semantic?user_id=${userId}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.memories || [];
}

/**
 * Fetch Procedural Memory (Learned Preferences)
 */
export async function getProceduralMemory(userId: string = "default"): Promise<MemoryItem[]> {
  const res = await fetch(`${API_BASE_URL}/memory/procedural?user_id=${userId}`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.memories || [];
}
