import { useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";

export default function LoginScreen() {
  const [claveBancaria, setClaveBancaria] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const login = useAppStore((s) => s.login);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(claveBancaria, password);
      login(res.token, res.full_name, res.onboarding_done);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="phone-shell">
      <div className="app-header">
        <div>
          <div className="brand">Banorte AI</div>
          <div className="tagline">Tu banco, a tu manera</div>
        </div>
      </div>
      <div className="screen-body" style={{ paddingBottom: 24, justifyContent: "center" }}>
        <div style={{ textAlign: "center", marginBottom: 8 }}>
          <div style={{ fontSize: 20, fontWeight: 700 }}>Inicia sesion</div>
          <div style={{ fontSize: 13, color: "var(--ink-600)" }}>
            Usa tu clave bancaria y contraseña.
          </div>
        </div>
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <input
            placeholder="Clave bancaria"
            value={claveBancaria}
            onChange={(e) => setClaveBancaria(e.target.value)}
            style={{ padding: 13, borderRadius: 12, border: "1px solid var(--line-100)" }}
          />
          <input
            placeholder="Contraseña"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ padding: 13, borderRadius: 12, border: "1px solid var(--line-100)" }}
          />
          {error && <div style={{ color: "#b3261e", fontSize: 13 }}>{error}</div>}
          <button className="btn btn-primary" disabled={loading}>
            {loading ? "Entrando..." : "Entrar"}
          </button>
        </form>
        <div style={{ textAlign: "center", fontSize: 11.5, color: "var(--ink-400)", marginTop: 16 }}>
          Demo hackathon — clave <b>4152</b> / contraseña <b>demo1234</b>
        </div>
      </div>
    </div>
  );
}
