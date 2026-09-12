import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { Brand, StatusBar } from "../components/PhoneChrome";
import {
  createPlatformPasskey,
  getPlatformPasskey,
  platformAuthenticatorAvailable,
} from "../auth/passkeys";

const DEVICE_READY = "intellibank_account_ready";
const DEVICE_IDENTIFIER = "intellibank_identifier";
const BIOMETRIC_READY = "intellibank_biometric_ready";

export default function LoginScreen() {
  const [returning, setReturning] = useState(localStorage.getItem(DEVICE_READY) === "1");
  const [identifier, setIdentifier] = useState(localStorage.getItem(DEVICE_IDENTIFIER) || "");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [loginCredential, setLoginCredential] = useState("clave");
  const [password, setPassword] = useState("");
  const [usePassword, setUsePassword] = useState(localStorage.getItem(BIOMETRIC_READY) !== "1");
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [biometricRequested, setBiometricRequested] = useState(true);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const login = useAppStore((state) => state.login);

  useEffect(() => {
    platformAuthenticatorAvailable().then(setBiometricAvailable).catch(() => setBiometricAvailable(false));
  }, []);

  const rememberDevice = (value) => {
    localStorage.setItem(DEVICE_READY, "1");
    localStorage.setItem(DEVICE_IDENTIFIER, value);
  };

  const passwordLogin = async (event) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await api.login(identifier, password);
      rememberDevice(identifier);
      login(response.token, response.full_name, response.onboarding_done, response.biometric_enabled);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const register = async (event) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await api.register({
        full_name: fullName,
        email,
        phone,
        password,
        clave_bancaria: loginCredential === "clave" ? identifier : null,
        card_number: loginCredential === "card" ? identifier : null,
      });
      localStorage.setItem("banorte_token", response.token);
      const rememberedIdentifier = email || identifier;
      rememberDevice(rememberedIdentifier);

      let biometricEnabled = false;
      if (biometricRequested && biometricAvailable) {
        try {
          const options = await api.getPasskeyRegistrationOptions();
          const credential = await createPlatformPasskey(options);
          await api.completePasskeyRegistration(credential, "web", navigator.userAgent);
          biometricEnabled = true;
        } catch { /* El acceso queda disponible por contraseña y puede activarse desde Perfil. */ }
      }
      login(response.token, response.full_name, response.onboarding_done, biometricEnabled);
    } catch (requestError) {
      setError(requestError.name === "NotAllowedError" ? "Se canceló la configuración biométrica" : requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const biometricLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      const options = await api.getPasskeyLoginOptions(identifier);
      const credential = await getPlatformPasskey(options);
      const response = await api.completePasskeyLogin(identifier, credential);
      login(response.token, response.full_name, response.onboarding_done, true);
    } catch (requestError) {
      setError(requestError.name === "NotAllowedError" ? "No se completó la verificación biométrica" : requestError.message);
    } finally {
      setLoading(false);
    }
  };

  const resetDeviceFlow = () => {
    localStorage.removeItem(DEVICE_READY);
    localStorage.removeItem(DEVICE_IDENTIFIER);
    localStorage.removeItem(BIOMETRIC_READY);
    setReturning(false);
    setUsePassword(false);
    setIdentifier("");
    setPassword("");
    setError(null);
  };

  return (
    <div className="phone-shell login-shell">
      <StatusBar />
      <div className="access-brand"><Brand /><span>Tu dinero con<br />más posibilidades</span></div>

      {returning ? (
        <main className="login-content returning-access">
          <div className="login-heading">
            <span className="eyebrow">Acceso seguro</span>
            <h1>Bienvenido<br />de vuelta.</h1>
            <p>Entra a tu espacio de inversiones con la seguridad de este dispositivo.</p>
          </div>

          {!usePassword && (
            <div className="biometric-login-panel">
              <div className="biometric-orb"><span className="face-corners" /><i /></div>
              <strong>{biometricAvailable ? "Face ID o huella" : "Biometría no disponible"}</strong>
              <small>{biometricAvailable ? "Tu información biométrica nunca sale del dispositivo." : "Puedes entrar con tu contraseña."}</small>
              <button className="btn btn-primary login-cta" onClick={biometricLogin} disabled={loading || !biometricAvailable}>
                {loading ? "Verificando…" : "Entrar"}
              </button>
              <button className="text-action" onClick={() => setUsePassword(true)}>Usar mi contraseña</button>
            </div>
          )}

          {usePassword && (
            <form className="password-access" onSubmit={passwordLogin}>
              <div className="credential-card"><label className="field-label" htmlFor="return-identifier">Correo, CLABE o tarjeta</label><input id="return-identifier" value={identifier} onChange={(event) => setIdentifier(event.target.value)} autoComplete="username" /></div>
              <div className="credential-card"><label className="field-label" htmlFor="return-password">Contraseña</label><input id="return-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="••••••••" autoComplete="current-password" /></div>
              <button className="btn btn-primary login-cta" disabled={loading}>{loading ? "Entrando…" : "Entrar con contraseña"}</button>
              {biometricAvailable && <button type="button" className="text-action" onClick={() => setUsePassword(false)}>Volver a biometría</button>}
            </form>
          )}

          {error && <div className="info-banner warning"><span>{error}</span></div>}
          <button className="device-reset-link" onClick={resetDeviceFlow}>Configurar otra cuenta en este dispositivo</button>
        </main>
      ) : (
        <form onSubmit={register} className="login-content registration-flow">
          <div className="login-heading">
            <span className="eyebrow">Primera vez</span>
            <h1>Crea tu acceso.</h1>
            <p>Completa tus datos una sola vez. Después entrarás con biometría o contraseña.</p>
          </div>
          <div className="registration-grid">
            <div className="credential-card"><label className="field-label" htmlFor="full-name">Nombre completo</label><input id="full-name" required placeholder="Tu nombre" value={fullName} onChange={(event) => setFullName(event.target.value)} autoComplete="name" /></div>
            <div className="credential-card"><label className="field-label" htmlFor="email">Correo</label><input id="email" required type="email" placeholder="tu@correo.com" value={email} onChange={(event) => setEmail(event.target.value)} autoComplete="email" /></div>
            <div className="credential-card"><label className="field-label" htmlFor="phone">Teléfono</label><input id="phone" required type="tel" placeholder="55 0000 0000" value={phone} onChange={(event) => setPhone(event.target.value)} autoComplete="tel" /></div>
            <div className="credential-card">
              <div className="credential-switch"><button type="button" className={loginCredential === "clave" ? "selected" : ""} onClick={() => setLoginCredential("clave")}>CLABE</button><button type="button" className={loginCredential === "card" ? "selected" : ""} onClick={() => setLoginCredential("card")}>Tarjeta</button></div>
              <label className="field-label" htmlFor="identifier">{loginCredential === "clave" ? "CLABE interbancaria" : "Número de tarjeta"}</label>
              <input id="identifier" required inputMode="numeric" placeholder={loginCredential === "clave" ? "18 dígitos" : "16 dígitos"} value={identifier} onChange={(event) => setIdentifier(event.target.value)} />
            </div>
            <div className="credential-card"><label className="field-label" htmlFor="password">Contraseña</label><input id="password" required minLength="8" type="password" placeholder="Mínimo 8 caracteres" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" /></div>
            <button type="button" className={`biometric-setup-card ${biometricRequested ? "selected" : ""}`} onClick={() => setBiometricRequested((value) => !value)} disabled={!biometricAvailable}>
              <span className="mini-face-id"><i /></span>
              <span><strong>Face ID o huella</strong><small>{biometricAvailable ? "Se solicitará al terminar" : "No disponible en este navegador"}</small></span>
              <b>{biometricRequested && biometricAvailable ? "✓" : ""}</b>
            </button>
          </div>
          {error && <div className="info-banner warning"><span>{error}</span></div>}
          <button className="btn btn-primary login-cta" disabled={loading}>{loading ? "Configurando…" : "Crear mi acceso"}</button>
          <button type="button" className="device-reset-link" onClick={() => { setReturning(true); setIdentifier("4152"); }}>Ya tengo una cuenta en este dispositivo</button>
        </form>
      )}
      <div className="brand-wave"><span>Un mejor futuro<br />empieza hoy.</span></div>
    </div>
  );
}
