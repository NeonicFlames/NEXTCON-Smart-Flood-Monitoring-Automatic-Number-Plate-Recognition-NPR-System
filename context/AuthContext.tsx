"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

interface AuthContextType {
  isAdmin: boolean;
  login: (passcode: string) => boolean;
  logout: () => void;
  showLoginModal: boolean;
  setShowLoginModal: (show: boolean) => void;
}

const AuthContext = createContext<AuthContextType>({
  isAdmin: false,
  login: () => false,
  logout: () => {},
  showLoginModal: false,
  setShowLoginModal: () => {},
});

export const ADMIN_PASSCODE = process.env.NEXT_PUBLIC_ADMIN_PASSCODE || "123";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAdmin, setIsAdmin] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("npr_admin_authenticated");
    if (saved === "true") {
      setIsAdmin(true);
    }
  }, []);

  const login = (passcode: string): boolean => {
    if (passcode.trim() === ADMIN_PASSCODE) {
      setIsAdmin(true);
      localStorage.setItem("npr_admin_authenticated", "true");
      setShowLoginModal(false);
      return true;
    }
    return false;
  };

  const logout = () => {
    setIsAdmin(false);
    localStorage.removeItem("npr_admin_authenticated");
  };

  return (
    <AuthContext.Provider
      value={{
        isAdmin,
        login,
        logout,
        showLoginModal,
        setShowLoginModal,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
