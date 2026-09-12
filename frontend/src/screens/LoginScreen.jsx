import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { Brand, StatusBar } from "../components/PhoneChrome";
import {
  createPlatformPasskey,
  getPlatformPasskey,
  platformAuthenticatorAvailable,
} from "../auth/passkeys";

const BIOMETRIC_IDENTIFIER = "intellibank_biometric_identifier";

export default function LoginScreen() {
  const [claveBancaria, setClaveBancaria] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const login = useAppStore((s) => s.login);

  useEffect(() => {
    platformAuthenticatorAvailable()
      .then(setBiometricAvailable)
      .catch(() => setBiometricAvailable(false));
  }, []);

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

  const biometricLogin = async () => {
    const identifier = claveBancaria || localStorage.getItem(BIOMETRIC_IDENTIFIER) || "";
    if (!identifier) {
      setError("Ingresa tu CLABE para iniciar con biometría");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const options = await api.getPasskeyLoginOptions(identifier);
      const credential = await getPlatformPasskey(options);
      const res = await api.completePasskeyLogin(identifier, credential);
      localStorage.setItem(BIOMETRIC_IDENTIFIER, identifier);
      login(res.token, res.full_name, res.onboarding_done);
    } catch (err) {
      setError(err.name === "NotAllowedError" ? "No se completó la verificación biométrica" : err.message);
    } finally {
      setLoading(false);
    }
  };

  const enrollPasskey = async () => {
    if (!claveBancaria || !password) {
      setError("Ingresa tu CLABE y contraseña para configurar la biometría");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const res = await api.login(claveBancaria, password);
      localStorage.setItem("banorte_token", res.token);
      const options = await api.getPasskeyRegistrationOptions();
      const credential = await createPlatformPasskey(options);
      await api.completePasskeyRegistration(credential, "web", navigator.userAgent);
      localStorage.setItem(BIOMETRIC_IDENTIFIER, claveBancaria);
      login(res.token, res.full_name, res.onboarding_done);
    } catch (err) {
      localStorage.removeItem("banorte_token");
      setError(err.name === "NotAllowedError" ? "Se canceló la configuración biométrica" : err.message);
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
        <div className="login-divider"><span>o usa este dispositivo</span></div>
        <button
          type="button"
          className="btn biometric-login-cta"
          onClick={biometricLogin}
          disabled={loading || !biometricAvailable}
        >
          {biometricAvailable ? "Iniciar con Face ID o biometría" : "Biometría no disponible"}
        </button>
        {biometricAvailable && (
          <button type="button" className="biometric-enroll-link" onClick={enrollPasskey} disabled={loading}>
            Configurar biometría con mi contraseña
          </button>
        )}
        <div className="demo-note">Demo · clave <b>4152</b> / contraseña <b>demo1234</b></div>
      </form>
      <div className="brand-wave"><span>Un mejor futuro<br />empieza hoy.</span></div>
    </div>
  );
}
