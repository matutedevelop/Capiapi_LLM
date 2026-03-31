import { useState, useEffect } from "react";
import CapiLogin from "./components/CapiLogin";
import CapiAPI from "./components/CapiAPI_chat";
import { getSession, clearSession } from "./components/CapiLogin";

export default function App() {
  const [session, setSession] = useState(null);

  // Al cargar, revisa si ya hay sesión guardada
  useEffect(() => {
    const saved = getSession();
    if (saved) setSession(saved);
  }, []);

  const handleLoginSuccess = (data) => {
    setSession(data);
  };

  const handleLogout = () => {
    clearSession();
    setSession(null);
  };

  // Si no hay sesión → Login
  // Si hay sesión → Chat
  if (!session) {
    return <CapiLogin onLoginSuccess={handleLoginSuccess} />;
  }

  return <CapiAPI session={session} onLogout={handleLogout} />;
}
