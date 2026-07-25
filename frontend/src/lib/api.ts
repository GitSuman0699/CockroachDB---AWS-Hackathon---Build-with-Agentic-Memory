export const API_BASE_URL = "http://localhost:8000/api";

async function fetchMemory<T>(url: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(url);
    if (!response.ok) return fallback;
    return await response.json() as T;
  } catch (error) {
    // Memory is an enhancement to the workspace. Keep the UI responsive when
    // the optional local API is stopped or unreachable.
    console.warn("Memory API is unavailable. Start the backend to enable live memory.", error);
    return fallback;
  }
}

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
  const data = await fetchMemory<{ context?: MemoryContext }>(
    `${API_BASE_URL}/memory/working?session_id=${sessionId}`,
    {}
  );
  return data.context || {};
}

/**
 * Fetch Semantic Memory (Knowledge Base)
 */
export async function getSemanticMemory(userId: string = "default"): Promise<MemoryItem[]> {
  const data = await fetchMemory<{ memories?: MemoryItem[] }>(
    `${API_BASE_URL}/memory/semantic?user_id=${userId}`,
    {}
  );
  return data.memories || [];
}

/**
 * Fetch Procedural Memory (Learned Preferences)
 */
export async function getProceduralMemory(userId: string = "default"): Promise<MemoryItem[]> {
  const data = await fetchMemory<{ memories?: MemoryItem[] }>(
    `${API_BASE_URL}/memory/procedural?user_id=${userId}`,
    {}
  );
  return data.memories || [];
}
