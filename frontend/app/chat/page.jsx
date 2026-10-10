"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import ChatSidebar from "@/components/ChatSidebar";
import ChatWindow from "@/components/ChatWindow";

const newId = () =>
  typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`;

const histKey = (username) => `rag-history:${username}`;

export default function ChatPage() {
  const { token, user, ready, logout } = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [sideOpen, setSideOpen] = useState(false);

  useEffect(() => {
    if (ready && !token) router.replace("/login");
  }, [token, ready, router]);

  // Load per-user history (browser-local) once session is ready
  useEffect(() => {
    if (!ready || !user) return;
    try {
      const saved = JSON.parse(localStorage.getItem(histKey(user.username)) || "[]");
      if (Array.isArray(saved)) {
        setConversations(saved);
        setActiveId(saved[0]?.id ?? null);
      }
    } catch {
      /* corrupted history: start fresh */
    }
  }, [ready, user]);

  // Persist on every change
  useEffect(() => {
    if (!ready || !user) return;
    localStorage.setItem(histKey(user.username), JSON.stringify(conversations));
  }, [conversations, ready, user]);

  if (!ready || !token) return null;
  const active = conversations.find((c) => c.id === activeId) ?? null;

  const appendMsg = (id, msg) =>
    setConversations((cs) =>
      cs.map((c) => (c.id === id ? { ...c, messages: [...c.messages, msg] } : c))
    );

  const send = async (text) => {
    const question = text.trim();
    if (!question || busy) return;
    setBusy(true);
    let id = activeId;
    if (!id) {
      id = newId();
      const title =
        question.length > 44 ? `${question.slice(0, 44)}…` : question;
      setConversations((cs) => [
        { id, title, messages: [], updatedAt: Date.now() },
        ...cs,
      ]);
      setActiveId(id);
    }
    appendMsg(id, { role: "user", text: question });
    try {
      const { data } = await api.post("/api/chat/", { question });
      appendMsg(id, { role: "bot", text: data.answer, sources: data.sources });
    } catch (err) {
      if (err.response?.status === 401) {
        logout();
        router.replace("/login");
      } else {
        appendMsg(id, {
          role: "bot",
          text: "Error: could not reach the backend.",
        });
      }
    } finally {
      setBusy(false);
    }
  };

  const removeConvo = (id) =>
    setConversations((cs) => {
      const rest = cs.filter((c) => c.id !== id);
      if (id === activeId) setActiveId(rest[0]?.id ?? null);
      return rest;
    });

  const doLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <div className="chat-layout">
      <ChatSidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={(id) => {
          setActiveId(id);
          setSideOpen(false);
        }}
        onNew={() => {
          setActiveId(null);
          setSideOpen(false);
        }}
        onDelete={removeConvo}
        username={user?.username}
        onLogout={doLogout}
        open={sideOpen}
        onClose={() => setSideOpen(false)}
      />
      <main className="chat-main">
        <div className="chat-topbar">
          <button
            type="button"
            className="hamburger"
            onClick={() => setSideOpen(true)}
            aria-label="Open history"
          >
            &#9776;
          </button>
          <span className="chat-title">{active?.title ?? "New conversation"}</span>
          <span className="live-dot" title="Backend connected" />
        </div>
        <ChatWindow messages={active?.messages ?? []} busy={busy} onSend={send} />
      </main>
    </div>
  );
}
