"use client";

import { useEffect, useRef } from "react";
import { loadGoogleScript } from "@/lib/google";
import { loginWithGoogle } from "@/lib/api";

type Props = {
  onLogin: (data: any) => void;
  onError: (message: string) => void;
};

export default function AuthButton({ onLogin, onError }: Props) {
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;

    loadGoogleScript()
      .then(() => {
        if (!active || !buttonRef.current || !window.google) return;

        const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
        if (!clientId) {
          onError("NEXT_PUBLIC_GOOGLE_CLIENT_ID is not configured.");
          return;
        }

        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: async (response: any) => {
            try {
              const data = await loginWithGoogle(response.credential);
              localStorage.setItem("task_manager_token", data.token);
              localStorage.setItem("task_manager_user", JSON.stringify(data.user));
              onLogin(data);
            } catch (error: any) {
              onError(error.message || "Google login failed");
            }
          },
        });

        buttonRef.current.innerHTML = "";
        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "rectangular",
          width: 320,
        });
      })
      .catch((error) => onError(error.message));

    return () => {
      active = false;
    };
  }, [onLogin, onError]);

  return <div ref={buttonRef} />;
}
