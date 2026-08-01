"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { Lock, ShieldAlert, KeyRound, ArrowRight } from "lucide-react";

export function AdminPasscodeModal({
  isOpen,
  onClose,
  onSuccess,
}: {
  isOpen: boolean;
  onClose?: () => void;
  onSuccess?: () => void;
}) {
  const { login } = useAuth();
  const [passcode, setPasscode] = useState("");
  const [error, setError] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const success = login(passcode);
    if (success) {
      setError(false);
      setPasscode("");
      if (onSuccess) onSuccess();
    } else {
      setError(true);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-md p-6 rounded-xl shadow-2xl border flex flex-col gap-5"
        style={{
          background: "var(--color-paper-2)",
          borderColor: "var(--color-rule)",
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="p-3 rounded-lg shrink-0"
            style={{
              background: "var(--color-accent-subtle)",
              color: "var(--color-accent)",
              border: "1px solid var(--color-rule)",
            }}
          >
            <KeyRound size={24} />
          </div>
          <div>
            <h3
              className="text-lg font-semibold tracking-tight"
              style={{ color: "var(--color-ink)", fontFamily: "var(--font-display)" }}
            >
              Admin Authentication Required
            </h3>
            <p className="text-xs mt-0.5" style={{ color: "var(--color-neutral)" }}>
              Please enter the administrator passcode (default: <span className="font-mono font-bold text-accent">123</span>)
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              className="block text-xs font-medium mb-1.5"
              style={{ color: "var(--color-neutral)" }}
            >
              Administrator Passcode
            </label>
            <div className="relative">
              <input
                type="password"
                value={passcode}
                onChange={(e) => {
                  setPasscode(e.target.value);
                  setError(false);
                }}
                placeholder="Enter passcode..."
                className="w-full px-3.5 py-2.5 rounded-md text-sm border focus:outline-none focus:ring-2"
                style={{
                  background: "var(--color-paper-3)",
                  color: "var(--color-ink)",
                  borderColor: error ? "var(--color-danger)" : "var(--color-rule)",
                  fontFamily: "var(--font-outlier)",
                }}
                autoFocus
              />
            </div>
            {error && (
              <p
                className="text-xs mt-1.5 flex items-center gap-1 font-medium"
                style={{ color: "var(--color-danger)" }}
              >
                <ShieldAlert size={14} /> Incorrect passcode. Please try again.
              </p>
            )}
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition"
                style={{ color: "var(--color-neutral)" }}
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-md shadow transition"
              style={{
                background: "var(--color-accent)",
                color: "#ffffff",
              }}
            >
              <span>Unlock Admin Access</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function AdminGuard({ children }: { children: React.ReactNode }) {
  const { isAdmin } = useAuth();
  const [showModal, setShowModal] = useState(!isAdmin);

  if (!isAdmin) {
    return (
      <>
        <AdminPasscodeModal
          isOpen={true}
          onSuccess={() => setShowModal(false)}
        />
        <div
          className="flex flex-col items-center justify-center p-12 text-center rounded-xl border my-8"
          style={{
            background: "var(--color-paper-2)",
            borderColor: "var(--color-rule)",
          }}
        >
          <div
            className="p-4 rounded-full mb-4"
            style={{
              background: "var(--color-paper-3)",
              color: "var(--color-neutral)",
            }}
          >
            <Lock size={36} />
          </div>
          <h2
            className="text-xl font-bold tracking-tight"
            style={{ color: "var(--color-ink)" }}
          >
            Protected Admin Area
          </h2>
          <p
            className="text-sm mt-1.5 max-w-md"
            style={{ color: "var(--color-neutral)" }}
          >
            Access to this section requires administrator authorization. Passcode prompt is active above.
          </p>
        </div>
      </>
    );
  }

  return <>{children}</>;
}
