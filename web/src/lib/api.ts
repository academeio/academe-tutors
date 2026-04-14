const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8001";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
}

export function createChatSocket(
  sessionId: string,
  token: string,
  onDelta: (delta: string) => void,
  onDone: (content: string) => void,
  onError: (error: string) => void,
): WebSocket {
  const ws = new WebSocket(`${WS_URL}/api/chat/ws/${sessionId}?token=${token}`);

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "delta") {
      onDelta(data.content);
    } else if (data.type === "done") {
      onDone(data.content);
    } else if (data.type === "error") {
      onError(data.content || "Unknown error");
    }
  };

  ws.onerror = () => onError("WebSocket connection error");

  return ws;
}

export async function fetchHistory(sessionId: string, token: string): Promise<ChatMessage[]> {
  const resp = await fetch(`${API_URL}/api/chat/sessions/${sessionId}/history`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!resp.ok) return [];
  const data = await resp.json();
  return data.messages || [];
}
