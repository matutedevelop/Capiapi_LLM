import { useState } from "react";

const CAPI_IMG = "data:image/png;base64,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";

// ─── AUTH SERVICE ─────────────────────────────────────────────────────────────
// Body enviado al backend: { email, password, canvas_token }
// Respuesta esperada:      { token, user: { name, email }, courses: [] }
const API_BASE_URL = "http://localhost:8000";
const USE_MOCK = false;

const authService = {
  login: async ({ email, password, canvasToken }) => {
    if (USE_MOCK) {
      await new Promise(r => setTimeout(r, 1200));
      return {
        token: canvasToken,
        user: { name: "Demie Estudiante", email },
        courses: [
          { id: "1", name: "Cálculo Diferencial",          code: "MATH101" },
          { id: "2", name: "Programación Orientada a Obj.", code: "CS201"  },
          { id: "3", name: "Estadística Aplicada",          code: "STAT302" },
          { id: "4", name: "Álgebra Lineal",                code: "MATH203" },
          { id: "5", name: "Bases de Datos",                code: "CS305"  },
        ],
      };
    }
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, canvas_token: canvasToken }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || "Credenciales incorrectas o token inválido");
    }
    return res.json();
  },
};

// ─── SESIÓN ───────────────────────────────────────────────────────────────────
export const saveSession = (data) => {
  localStorage.setItem("capi_token",   data.token);
  localStorage.setItem("capi_user",    JSON.stringify(data.user));
  localStorage.setItem("capi_courses", JSON.stringify(data.courses));
};

export const getSession = () => {
  const token = localStorage.getItem("capi_token");
  if (!token) return null;
  return {
    token,
    user:    JSON.parse(localStorage.getItem("capi_user")    || "{}"),
    courses: JSON.parse(localStorage.getItem("capi_courses") || "[]"),
  };
};

export const clearSession = () => {
  ["capi_token","capi_user","capi_courses"].forEach(k => localStorage.removeItem(k));
};

// ─── CAMPO REUTILIZABLE ───────────────────────────────────────────────────────
const Field = ({ label, type = "text", value, onChange, placeholder, error, icon, hint, extraRight }) => (
  <div style={{ marginBottom: 18 }}>
    <label style={{
      display: "block", fontSize: 11, fontWeight: 800,
      letterSpacing: "0.1em", textTransform: "uppercase",
      color: "var(--text-muted)", marginBottom: 6,
    }}>{label}</label>
    <div style={{ position: "relative" }}>
      {icon && (
        <span style={{ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", fontSize: 15, opacity: 0.45, pointerEvents: "none" }}>
          {icon}
        </span>
      )}
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: "100%",
          padding: `11px ${extraRight ? "44px" : "14px"} 11px ${icon ? "40px" : "14px"}`,
          borderRadius: 10,
          border: `2px solid ${error ? "#F09595" : "var(--capi-border)"}`,
          background: "var(--input-bg)",
          color: "var(--text)",
          fontSize: 14, fontWeight: 500,
          outline: "none", fontFamily: "inherit",
          transition: "border-color 0.15s",
        }}
        onFocus={e => { e.target.style.borderColor = error ? "#E24B4A" : "var(--capi-brown)"; }}
        onBlur={e =>  { e.target.style.borderColor = error ? "#F09595"  : "var(--capi-border)"; }}
      />
      {extraRight}
    </div>
    {hint && !error && (
      <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 5, lineHeight: 1.4 }}>{hint}</div>
    )}
    {error && (
      <div style={{ fontSize: 11, color: "#C0392B", marginTop: 5, fontWeight: 600 }}>⚠ {error}</div>
    )}
  </div>
);

// ─── LOGIN ────────────────────────────────────────────────────────────────────
export default function CapiLogin({ onLoginSuccess }) {
  const [dark, setDark] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", canvasToken: "" });
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPwd, setShowPwd] = useState(false);
  const [showToken, setShowToken] = useState(false);

  const set = field => val => setForm(f => ({ ...f, [field]: val }));

  const validate = () => {
    const e = {};
    if (!form.email.trim())       e.email       = "El correo es requerido";
    else if (!form.email.includes("@")) e.email = "Ingresa un correo válido";
    if (!form.password.trim())    e.password    = "La contraseña es requerida";
    if (!form.canvasToken.trim()) e.canvasToken = "El token de Canvas es requerido";
    return e;
  };

  const handleSubmit = async () => {
    const e = validate();
    if (Object.keys(e).length) { setErrors(e); return; }
    setErrors({}); setGlobalError(""); setLoading(true);
    try {
      const data = await authService.login({
        email: form.email.trim(),
        password: form.password,
        canvasToken: form.canvasToken.trim(),
      });
      saveSession(data);
      onLoginSuccess(data);
    } catch (err) {
      setGlobalError(err.message || "Error al iniciar sesión. Verifica tus datos.");
    } finally {
      setLoading(false);
    }
  };

  const onKey = e => { if (e.key === "Enter") handleSubmit(); };

  // Botón ojo para password/token
  const EyeBtn = ({ show, onToggle }) => (
    <button onClick={onToggle} type="button" style={{
      position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
      background: "transparent", border: "none", cursor: "pointer",
      fontSize: 15, opacity: 0.45, padding: 2,
    }}>{show ? "🙈" : "👁️"}</button>
  );

  const T = dark ? {
    "--bg": "#18140F", "--surface": "#221C14",
    "--text": "#EDE0D0", "--text-muted": "#8A7560",
    "--capi-brown": "#D4A574", "--capi-accent-bg": "#2A2018",
    "--capi-border": "#3A2E20", "--capi-shadow": "rgba(0,0,0,0.5)",
    "--input-bg": "#1C1710",
  } : {
    "--bg": "#FDF8F2", "--surface": "#FFFFFF",
    "--text": "#2D1F0E", "--text-muted": "#9B7E5E",
    "--capi-brown": "#8B5E3C", "--capi-accent-bg": "#FEF3E8",
    "--capi-border": "#E8D5C0", "--capi-shadow": "rgba(139,94,60,0.18)",
    "--input-bg": "#FEF9F4",
  };

  return (
    <div style={{
      ...T, minHeight: "100vh", display: "flex",
      alignItems: "center", justifyContent: "center",
      background: "var(--bg)", fontFamily: "\'Nunito\', \'Segoe UI\', sans-serif",
      color: "var(--text)", padding: "1rem", position: "relative",
    }}>
      <style>{`
        @import url(\'https://fonts.googleapis.com/css2?family=Fredoka+One&family=Nunito:wght@400;500;600;700;800&display=swap\');
        * { box-sizing: border-box; margin: 0; padding: 0; }
        @keyframes capiFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes spin { to{transform:rotate(360deg)} }
        input::placeholder { color: var(--text-muted); opacity: 0.6; font-weight: 400; }
      `}</style>

      {/* Dark toggle */}
      <button onClick={() => setDark(d => !d)} style={{
        position: "absolute", top: 20, right: 20,
        padding: "8px 12px", borderRadius: 9,
        border: "2px solid var(--capi-border)",
        background: "transparent", color: "var(--text-muted)",
        fontSize: 16, cursor: "pointer",
      }}>{dark ? "☀️" : "🌙"}</button>

      {/* Card */}
      <div style={{
        width: "100%", maxWidth: 420,
        background: "var(--surface)",
        borderRadius: 20, border: "2px solid var(--capi-border)",
        boxShadow: `0 20px 60px var(--capi-shadow)`,
        padding: "2.5rem 2rem",
        animation: "fadeUp 0.4s ease both",
      }}>

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "2rem" }}>
          <div style={{ animation: "capiFloat 3.5s ease-in-out infinite", display: "inline-block", marginBottom: 10 }}>
            <img src={CAPI_IMG} width={88} height={88}
              style={{ objectFit: "contain", mixBlendMode: dark ? "screen" : "multiply" }}
              alt="CapiAPI" />
          </div>
          <div style={{
            fontSize: 30, fontWeight: 800,
            fontFamily: "\'Fredoka One\', cursive",
            color: "var(--capi-brown)", letterSpacing: "0.05em", marginBottom: 4,
          }}>CapiAPI</div>
          <div style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 500 }}>
            Inicia sesión con tus credenciales
          </div>
        </div>

        {/* Campos */}
        <div onKeyDown={onKey}>

          {/* Correo */}
          <Field
            label="Correo electrónico"
            type="email"
            value={form.email}
            onChange={set("email")}
            placeholder="tu@correo.edu"
            error={errors.email}
            icon="✉️"
          />

          {/* Contraseña */}
          <Field
            label="Contraseña"
            type={showPwd ? "text" : "password"}
            value={form.password}
            onChange={set("password")}
            placeholder="••••••••"
            error={errors.password}
            icon="🔒"
            extraRight={<EyeBtn show={showPwd} onToggle={() => setShowPwd(s => !s)} />}
          />

          {/* Token de Canvas */}
          <Field
            label="Token de Canvas"
            type={showToken ? "text" : "password"}
            value={form.canvasToken}
            onChange={set("canvasToken")}
            placeholder="12734~CWPyxJJ..."
            error={errors.canvasToken}
            icon="🔑"
            hint="Encuéntralo en Canvas → Configuración de cuenta → Token de acceso"
            extraRight={<EyeBtn show={showToken} onToggle={() => setShowToken(s => !s)} />}
          />
        </div>

        {/* Error global */}
        {globalError && (
          <div style={{
            padding: "10px 14px", borderRadius: 10, marginBottom: 16,
            background: dark ? "rgba(220,38,38,.1)" : "#FFF0F0",
            border: "2px solid #F09595",
            color: dark ? "#F09595" : "#A32D2D",
            fontSize: 13, fontWeight: 600,
          }}>⚠️ {globalError}</div>
        )}

        {/* Botón */}
        <button onClick={handleSubmit} disabled={loading} style={{
          width: "100%", padding: "13px",
          borderRadius: 12, border: "none",
          background: loading ? "var(--capi-border)" : "var(--capi-brown)",
          color: loading ? "var(--text-muted)" : "#FFF8F0",
          fontSize: 15, fontWeight: 800,
          cursor: loading ? "default" : "pointer",
          fontFamily: "\'Fredoka One\', cursive",
          letterSpacing: "0.06em", transition: "all 0.2s",
          display: "flex", alignItems: "center", justifyContent: "center", gap: 10,
        }}>
          {loading ? (
            <>
              <div style={{ width: 18, height: 18, borderRadius: "50%", border: "3px solid var(--text-muted)", borderTopColor: "var(--capi-brown)", animation: "spin 0.8s linear infinite" }} />
              Verificando...
            </>
          ) : "Entrar a CapiAPI"}
        </button>

        {/* Hint modo demo */}
        {USE_MOCK && (
          <div style={{
            marginTop: 16, padding: "8px 12px", borderRadius: 10,
            background: dark ? "#2A2018" : "#FEF3E2",
            border: "2px solid var(--capi-border)",
            fontSize: 11, color: "var(--text-muted)", textAlign: "center", lineHeight: 1.5,
          }}>
            <span style={{ fontWeight: 800, color: "var(--capi-brown)" }}>Modo demo</span> — Llena los 3 campos con cualquier valor. Cambia <code style={{ fontSize: 10 }}>USE_MOCK = false</code> al conectar el backend.
          </div>
        )}
      </div>
    </div>
  );
}
