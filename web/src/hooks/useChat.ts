"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { ChatMessage, createChatSocket } from "@/lib/api";

export function useChat(sessionId: string | null, token: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const streamBufferRef = useRef("");
  const messageIdRef = useRef(0);

  useEffect(() => {
    if (!sessionId || !token) return;

    const ws = createChatSocket(
      sessionId,
      token,
      // onDelta
      (delta) => {
        streamBufferRef.current += delta;
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.streaming) {
            return [...prev.slice(0, -1), { ...last, content: streamBufferRef.current }];
          }
          return prev;
        });
      },
      // onDone
      (content) => {
        streamBufferRef.current = "";
        setStreaming(false);
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.streaming) {
            return [...prev.slice(0, -1), { ...last, content, streaming: false }];
          }
          return prev;
        });
      },
      // onError
      (error) => {
        setStreaming(false);
        console.error("Chat error:", error);
      },
    );

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    wsRef.current = ws;

    return () => ws.close();
  }, [sessionId, token]);

  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || streaming) return;

      const userMsg: ChatMessage = {
        id: `msg-${++messageIdRef.current}`,
        role: "user",
        content,
      };
      const assistantMsg: ChatMessage = {
        id: `msg-${++messageIdRef.current}`,
        role: "assistant",
        content: "",
        streaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setStreaming(true);
      streamBufferRef.current = "";

      wsRef.current.send(JSON.stringify({ type: "message", content }));
    },
    [streaming],
  );

  return { messages, streaming, connected, sendMessage };
}
