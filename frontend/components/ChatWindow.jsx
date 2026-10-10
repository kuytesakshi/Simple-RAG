"use client";

import { useState } from "react";
import api from "@/lib/api";
import MessageBubble from "./MessageBubble";

export default function ChatWindow() {
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");

  const send = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    const question = q;
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setQ("");
    // TODO: POST /api/chat
    // const { data } = await api.post("/api/chat/", { question });
    // setMsgs((m) => [...m, { role: "bot", text: data.answer }]);
    setMsgs((m) => [...m, { role: "bot", text: "(RAG answer placeholder)" }]);
  };

  return (
    <div>
      {msgs.map((m, i) => (
        <MessageBubble key={i} {...m} />
      ))}
      <form onSubmit={send}>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Ask about your PDF..."
          style={{ width: "80%" }}
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}
