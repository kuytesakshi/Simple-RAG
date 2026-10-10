"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import RobotReader from "@/components/RobotReader";

const POINTS = [
  "Private, free on-device embeddings",
  "Answers grounded in your PDFs",
  "Secure JWT-protected API",
];

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login"); // login | register
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login, register } = useAuth();
  const router = useRouter();
  const isLogin = mode === "login";

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (isLogin) await login(username, password);
      else await register(username, password);
      router.push("/chat");
    } catch (err) {
      setError(
        err.response?.data?.detail || "Login failed. Check backend is running."
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-full">
      <aside className="auth-hero">
        <div className="hero-brand">
          <span className="brand-mark" aria-hidden />
          Simple&nbsp;RAG
        </div>
        <div className="hero-art">
          <RobotReader />
        </div>
        <h2>Chat with your PDFs</h2>
        <p className="hero-sub">
          Your little robot has already read every page — just ask.
        </p>
        <ul className="hero-points">
          {POINTS.map((p) => (
            <li key={p}>
              <span className="tick" aria-hidden>
                &#10003;
              </span>
              {p}
            </li>
          ))}
        </ul>
      </aside>

      <main className="auth-panel">
        <div className="auth-form-clean">
          <h1>{isLogin ? "Welcome back" : "Create account"}</h1>
          <p className="auth-sub">
            {isLogin
              ? "Sign in to continue to your chatbot."
              : "Register to start chatting with your documents."}
          </p>
          <form onSubmit={submit}>
            <label className="field">
              Username
              <input
                placeholder="e.g. sakshi"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
              />
            </label>
            <label className="field">
              Password
              <input
                placeholder={isLogin ? "Your password" : "Min. 4 characters"}
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete={isLogin ? "current-password" : "new-password"}
              />
            </label>
            {error && <p className="error-banner">{error}</p>}
            <button type="submit" className="btn-primary" disabled={busy}>
              {busy ? "Please wait..." : isLogin ? "Sign in" : "Create account"}
            </button>
          </form>
          <p className="auth-switch">
            {isLogin ? "New here? " : "Already have an account? "}
            <button
              type="button"
              className="link-btn"
              onClick={() => {
                setMode(isLogin ? "register" : "login");
                setError("");
              }}
            >
              {isLogin ? "Create an account" : "Sign in"}
            </button>
          </p>
        </div>
      </main>
    </div>
  );
}
