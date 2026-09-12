import { useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { Brand, StatusBar } from "../components/PhoneChrome";

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
    <div className="phone-shell login-shell">
      <StatusBar />
      <div className="access-brand">
        <Brand />
        <span>Tu dinero con<br />más posibilidades</span>
      </div>
      <form onSubmit={submit} className="login-content">
        <div className="login-heading">
          <h1>Iniciar sesión</h1>
          <p>Ingresa tu CLABE interbancaria para reconocer tu cuenta.</p>
        </div>
        <div className="credential-card">
          <label className="field-label" htmlFor="clave-bancaria">CLABE interbancaria</label>
          <input
            id="clave-bancaria"
            placeholder="072 180 01234567890"
            value={claveBancaria}
            onChange={(e) => setClaveBancaria(e.target.value)}
          />
          <span className="field-help">18 dígitos · la encuentras en tu estado de cuenta</span>
        </div>
        <div className="credential-card">
          <label className="field-label" htmlFor="password">Contraseña</label>
          <input
            id="password"
            placeholder="••••••••"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <div className="info-banner warning"><span>!</span><span>{error}</span></div>}
        <button className="btn btn-primary login-cta" disabled={loading}>
          {loading ? "Entrando…" : "Continuar"}
        </button>
        <div className="demo-note">Demo · clave <b>4152</b> / contraseña <b>demo1234</b></div>
      </form>
      <div className="brand-wave"><span>Un mejor futuro<br />empieza hoy.</span></div>
    </div>
  );
}
