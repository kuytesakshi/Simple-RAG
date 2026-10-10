"use client";

import { createContext, useContext, useState, useEffect } from "react";
import api from "@/lib/api";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  // On load: validate any saved token against /me (clears it if expired/invalid)
  useEffect(() => {
    const saved = localStorage.getItem("token");
    if (!saved) {
      setReady(true);
      return;
    }
    api
      .get("/api/auth/me")
      .then(({ data }) => {
        setToken(saved);
        setUser(data);
      })
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setReady(true));
  }, []);

  const saveSession = (tok, userData) => {
    localStorage.setItem("token", tok);
    setToken(tok);
    setUser(userData);
  };

  const login = async (username, password) => {
    // Backend uses OAuth2PasswordRequestForm -> form-encoded body
    const params = new URLSearchParams({ username, password });
    const { data } = await api.post("/api/auth/login", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const { data: me } = await api.get("/api/auth/me", {
      headers: { Authorization: `Bearer ${data.access_token}` },
    });
    saveSession(data.access_token, me);
  };

  const register = async (username, password) => {
    await api.post("/api/auth/register", { username, password });
    await login(username, password);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthCtx.Provider value={{ token, user, ready, login, register, logout }}>
      {children}
    </AuthCtx.Provider>
  );
}
