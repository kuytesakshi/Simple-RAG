"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import ChatWindow from "@/components/ChatWindow";

export default function ChatPage() {
  const { token, ready, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (ready && !token) router.replace("/login");
  }, [token, ready, router]);

  if (!ready || !token) return null;

  return (
    <div className="container">
      <button onClick={logout} style={{ float: "right" }}>
        Logout
      </button>
      <h2>RAG Chatbot</h2>
      <ChatWindow />
    </div>
  );
}
