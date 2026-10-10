"use client";

import { useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import MessageBubble from "./MessageBubble";

export default function ChatWindow() {
  const [msgs, setMsgs] = useState([]);
  const [q, setQ] = useState("");
  const { logout } = useAuth();

  const send = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    const question = q;
    setMsgs((m) => [...m, { role: "user", text: question }]);
    setQ("");
    try {
      const { data } = await api.post("/api/chat/", { question });
      setMsgs((m) => [...m, { role: "bot", text: data.answer }]);
    } catch (err) {
      if (err.response?.status === 401) logout(); // token expired/invalid
      else
        setMsgs((m) => [
          ...m,
          { role: "bot", text: "Error: could not reach the backend." },
        ]);
    }
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
