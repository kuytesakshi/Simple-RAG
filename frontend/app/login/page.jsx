"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState("login"); // login | register
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const { login, register } = useAuth();
  const router = useRouter();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") await login(username, password);
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
    <form onSubmit={submit} className="login-form">
      <h2>{mode === "login" ? "Login" : "Register"}</h2>
      <input
        placeholder="username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <input
        placeholder="password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <p style={{ color: "red" }}>{error}</p>}
      <button type="submit" disabled={busy}>
        {busy ? "..." : mode === "login" ? "Login" : "Create account"}
      </button>
      <button
        type="button"
        onClick={() => {
          setMode(mode === "login" ? "register" : "login");
          setError("");
        }}
      >
        {mode === "login" ? "Need an account? Register" : "Have an account? Login"}
      </button>
    </form>
  );
}
