"use client";

import { createContext, useContext, useState, useEffect } from "react";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);

  useEffect(() => {
    setToken(localStorage.getItem("token"));
  }, []);

  const login = async (username, password) => {
    // TODO: POST to backend /api/auth/login, save JWT
    // const { data } = await api.post("/api/auth/login", { username, password });
    const fake = "dev-token";
    localStorage.setItem("token", fake);
    setToken(fake);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  return (
    <AuthCtx.Provider value={{ token, login, logout }}>
      {children}
    </AuthCtx.Provider>
  );
}
