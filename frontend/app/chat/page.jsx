"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import api from "@/lib/api";
import ChatSidebar from "@/components/ChatSidebar";
import ChatWindow from "@/components/ChatWindow";

export default function ChatPage() {
  const { token, user, ready, logout } = useAuth();
  const router = useRouter();
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [sideOpen, setSideOpen] = useState(false);

  useEffect(() => {
    if (ready && !token) router.replace("/login");
  }, [token, ready, router]);

  const fail = useCallback(
    (err) => {
      if (err.response?.status === 401) {
        logout();
        router.replace("/login");
        return true;
      }
      return false;
    },
    [logout, router]
  );

  // Load conversation list once session is ready
  useEffect(() => {
    if (!ready || !token) return;
    api
      .get("/api/conversations/")
      .then(({ data }) => {
        setConversations(data);
        if (data[0]) selectConvo(data[0].id);
      })
      .catch(fail);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready, token]);

  const selectConvo = async (id) => {
    setActiveId(id);
    setSideOpen(false);
    try {
      const { data } = await api.get(`/api/conversations/${id}`);
      setMessages(
        data.messages.map((m) => ({ role: m.role, text: m.content, sources: m.sources }))
      );
    } catch (err) {
      fail(err);
    }
  };

  const send = async (text) => {
    const question = text.trim();
    if (!question || busy) return;
    setBusy(true);
    setMessages((ms) => [...ms, { role: "user", text: question }]);
    try {
      let id = activeId;
      if (!id) {
        const title = question.length > 44 ? `${question.slice(0, 44)}…` : question;
        ({ data: { id } } = await api.post("/api/conversations/", { title }));
        setActiveId(id);
        setConversations((cs) => [{ id, title }, ...cs]);
      }
      const { data } = await api.post(`/api/conversations/${id}/ask`, { question });
      setMessages((ms) => [...ms, { role: "bot", text: data.answer, sources: data.sources }]);
      // Sync auto-retitle from server
      const { data: list } = await api.get("/api/conversations/");
      setConversations(list);
    } catch (err) {
      if (!fail(err)) {
        setMessages((ms) => [
          ...ms,
          { role: "bot", text: "Error: could not reach the backend." },
        ]);
      }
    } finally {
      setBusy(false);
    }
  };

  const removeConvo = async (id) => {
    try {
      await api.delete(`/api/conversations/${id}`);
    } catch (err) {
      if (fail(err)) return;
    }
    setConversations((cs) => {
      const rest = cs.filter((c) => c.id !== id);
      if (id === activeId) {
        const next = rest[0]?.id ?? null;
        setActiveId(next);
        if (next) selectConvo(next);
        else setMessages([]);
      }
      return rest;
    });
  };

  const doLogout = () => {
    logout();
    router.replace("/login");
  };

  if (!ready || !token) return null;
  const active = conversations.find((c) => c.id === activeId) ?? null;

  return (
    <div className="chat-layout">
      <ChatSidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={selectConvo}
        onNew={() => {
          setActiveId(null);
          setMessages([]);
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
        <ChatWindow messages={messages} busy={busy} onSend={send} />
      </main>
    </div>
  );
}
