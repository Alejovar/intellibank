import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { useAppStore } from "../store/useAppStore";
import { Brand, StatusBar } from "../components/PhoneChrome";
import {
  createPlatformPasskey,
  getPlatformPasskey,
  platformAuthenticatorAvailable,
} from "../auth/passkeys";

const ACCOUNT_IDENTIFIER = "intellibank_account_identifier";
const BIOMETRIC_IDENTIFIER = "intellibank_biometric_identifier";
const HAS_ACCOUNT = "intellibank_has_account";

const onlyDigits = (value, maxLength) => value.replace(/\D/g, "").slice(0, maxLength);

function PoweredBy() {
  return (
    <div className="powered-by">
      <span>Powered by Nort</span><b>AI</b>
    </div>
  );
}

function CredentialMark({ type }) {
  if (type === "card") {
    return <span className="mastercard-mark" aria-label="Mastercard"><i /><i /></span>;
  }
  return <img className="field-banorte-mark" src="/logobanorte.webp" alt="Banorte" />;
}

export default function LoginScreen() {
  const savedIdentifier = localStorage.getItem(ACCOUNT_IDENTIFIER) || "";
  const savedBiometricIdentifier = localStorage.getItem(BIOMETRIC_IDENTIFIER) || "";
  const [mode, setMode] = useState(localStorage.getItem(HAS_ACCOUNT) ? "login" : "register");
  const [identifier, setIdentifier] = useState(savedIdentifier);
  const [password, setPassword] = useState("");
  const [usePassword, setUsePassword] = useState(!savedBiometricIdentifier);
  const [editIdentifier, setEditIdentifier] = useState(!savedIdentifier);
  const [credentialType, setCredentialType] = useState("clabe");
  const [registration, setRegistration] = useState({
    fullName: "",
    email: "",
    phone: "",
    password: "",
    credential: "",
  });
  const [pendingRegistration, setPendingRegistration] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [biometricAvailable, setBiometricAvailable] = useState(null);
  const login = useAppStore((state) => state.login);

  useEffect(() => {
    platformAuthenticatorAvailable()
      .then((available) => {
        setBiometricAvailable(available);
        if (!available) setUsePassword(true);
      })
      .catch(() => {
        setBiometricAvailable(false);
        setUsePassword(true);
      });
  }, []);

  const credentialLength = credentialType === "clabe" ? 18 : 16;
  const credentialComplete = registration.credential.length === credentialLength;
  const registrationValid = useMemo(() => (
    registration.fullName.trim().length >= 2
    && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registration.email)
    && registration.phone.length === 10
    && registration.password.length >= 8
    && credentialComplete
  ), [credentialComplete, registration]);

  const updateRegistration = (field, value) => {
    setRegistration((current) => ({ ...current, [field]: value }));
  };

  const finishLogin = (response, accountIdentifier) => {
    localStorage.setItem(HAS_ACCOUNT, "1");
    localStorage.setItem(ACCOUNT_IDENTIFIER, accountIdentifier);
    login(response.token, response.full_name, response.onboarding_done);
  };

  const submitRegistration = async (event) => {
    event.preventDefault();
    if (!registrationValid) {
      setError("Revisa los campos marcados antes de continuar");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const payload = {
        full_name: registration.fullName.trim(),
        email: registration.email.trim().toLowerCase(),
        phone: registration.phone,
        password: registration.password,
        clave_bancaria: credentialType === "clabe" ? registration.credential : null,
        card_number: credentialType === "card" ? registration.credential : null,
      };
      const response = await api.register(payload);
      const accountIdentifier = registration.email.trim().toLowerCase();
      localStorage.setItem("banorte_token", response.token);
      localStorage.setItem(HAS_ACCOUNT, "1");
      localStorage.setItem(ACCOUNT_IDENTIFIER, accountIdentifier);
      setPendingRegistration({ response, accountIdentifier });
      setMode("enroll");
    } catch (registrationError) {
      setError(registrationError.message);
    } finally {
      setLoading(false);
    }
  };

  const submitLogin = async (event) => {
    event.preventDefault();
    if (!identifier.trim() || !password) {
      setError("Ingresa tu cuenta y contraseña");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const response = await api.login(identifier.trim(), password);
      finishLogin(response, identifier.trim());
    } catch (loginError) {
      setError(loginError.message);
    } finally {
      setLoading(false);
    }
  };

  const enrollPasskey = async ({ response, accountIdentifier }) => {
    if (!biometricAvailable) {
      setError("Este dispositivo no tiene Face ID, huella o PIN compatible");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      localStorage.setItem("banorte_token", response.token);
      const options = await api.getPasskeyRegistrationOptions();
      const credential = await createPlatformPasskey(options);
      await api.completePasskeyRegistration(credential, "web", navigator.userAgent);
      localStorage.setItem(BIOMETRIC_IDENTIFIER, accountIdentifier);
      finishLogin(response, accountIdentifier);
    } catch (enrollError) {
      setError(enrollError.name === "NotAllowedError"
        ? "Se canceló la configuración biométrica"
        : enrollError.message);
    } finally {
      setLoading(false);
    }
  };

  const enrollFromLogin = async () => {
    if (!identifier.trim() || !password) {
      setError("Ingresa tu cuenta y contraseña para activar la biometría");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const response = await api.login(identifier.trim(), password);
      await enrollPasskey({ response, accountIdentifier: identifier.trim() });
    } catch (enrollError) {
      setError(enrollError.message);
      setLoading(false);
    }
  };

  const biometricLogin = async () => {
    const biometricIdentifier = localStorage.getItem(BIOMETRIC_IDENTIFIER) || identifier.trim();
    if (!biometricIdentifier) {
      setUsePassword(true);
      setEditIdentifier(true);
      setError("Ingresa tu correo, CLABE o tarjeta para continuar");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const options = await api.getPasskeyLoginOptions(biometricIdentifier);
      const credential = await getPlatformPasskey(options);
      const response = await api.completePasskeyLogin(biometricIdentifier, credential);
      localStorage.setItem(BIOMETRIC_IDENTIFIER, biometricIdentifier);
      finishLogin(response, biometricIdentifier);
    } catch (biometricError) {
      setUsePassword(true);
      setError(biometricError.name === "NotAllowedError"
        ? "No se completó la biometría. Entra con tu contraseña."
        : `${biometricError.message}. Entra con tu contraseña.`);
    } finally {
      setLoading(false);
    }
  };

  const switchMode = (nextMode) => {
    setError(null);
    setPassword("");
    if (nextMode === "login") {
      setUsePassword(!localStorage.getItem(BIOMETRIC_IDENTIFIER));
      setEditIdentifier(!localStorage.getItem(ACCOUNT_IDENTIFIER));
      setIdentifier(localStorage.getItem(ACCOUNT_IDENTIFIER) || "");
    }
    setMode(nextMode);
  };

  const changeAccount = () => {
    setError(null);
    setPassword("");
    setIdentifier("");
    setEditIdentifier(true);
    setUsePassword(true);
  };

  return (
    <div className={`phone-shell login-shell login-${mode}`}>
      <StatusBar />
      <div className="access-brand"><Brand /></div>

      {mode === "register" && (
        <form onSubmit={submitRegistration} className="login-content register-content">
          <div className="login-heading">
            <span className="access-kicker">Tu banca, a tu manera</span>
            <h1>Crea tu acceso</h1>
            <p>Registra tus datos una sola vez. Después podrás entrar con contraseña, Face ID o huella.</p>
          </div>

          <div className="registration-fields">
            <label className="access-field">
              <span>Nombre completo</span>
              <input
                autoComplete="name"
                placeholder="Daniela Ramírez"
                value={registration.fullName}
                onChange={(event) => updateRegistration("fullName", event.target.value.slice(0, 120))}
              />
            </label>
            <label className="access-field">
              <span>Correo electrónico</span>
              <input
                type="email"
                autoComplete="email"
                placeholder="daniela@correo.com"
                value={registration.email}
                onChange={(event) => updateRegistration("email", event.target.value.slice(0, 160))}
              />
            </label>
            <label className="access-field">
              <span>Teléfono</span>
              <div className="input-with-prefix">
                <b>+52</b>
                <input
                  inputMode="numeric"
                  autoComplete="tel-national"
                  placeholder="10 dígitos"
                  maxLength={10}
                  value={registration.phone}
                  onChange={(event) => updateRegistration("phone", onlyDigits(event.target.value, 10))}
                />
                <small>{registration.phone.length}/10</small>
              </div>
            </label>
            <label className="access-field">
              <span>Contraseña</span>
              <input
                type="password"
                autoComplete="new-password"
                placeholder="Mínimo 8 caracteres"
                maxLength={128}
                value={registration.password}
                onChange={(event) => updateRegistration("password", event.target.value)}
              />
            </label>
          </div>

          <div className="credential-choice">
            <div className="credential-tabs" role="tablist" aria-label="Tipo de cuenta">
              <button type="button" className={credentialType === "clabe" ? "active" : ""} onClick={() => { setCredentialType("clabe"); updateRegistration("credential", ""); }}>CLABE</button>
              <button type="button" className={credentialType === "card" ? "active" : ""} onClick={() => { setCredentialType("card"); updateRegistration("credential", ""); }}>Tarjeta</button>
            </div>
            <label className="access-field credential-access-field">
              <span>{credentialType === "clabe" ? "CLABE interbancaria" : "Número de tarjeta"}</span>
              <div className="credential-input-wrap">
                <input
                  inputMode="numeric"
                  autoComplete="off"
                  placeholder={credentialType === "clabe" ? "18 dígitos" : "16 dígitos"}
                  maxLength={credentialLength}
                  value={registration.credential}
                  onChange={(event) => updateRegistration("credential", onlyDigits(event.target.value, credentialLength))}
                />
                {credentialComplete
                  ? <CredentialMark type={credentialType} />
                  : <small>{registration.credential.length}/{credentialLength}</small>}
              </div>
            </label>
          </div>

          {error && <div className="info-banner warning"><span>!</span><span>{error}</span></div>}
          <button className="btn btn-primary login-cta" disabled={loading || !registrationValid}>
            {loading ? "Creando acceso…" : "Crear mi acceso"}
          </button>
          <button type="button" className="access-switch" onClick={() => switchMode("login")}>Ya tengo una cuenta</button>
        </form>
      )}

      {mode === "login" && (
        <form
          onSubmit={usePassword ? submitLogin : (event) => {
            event.preventDefault();
            biometricLogin();
          }}
          className="login-content"
        >
          <div className="login-heading">
            <span className="access-kicker">Qué gusto verte</span>
            <h1>Iniciar sesión</h1>
            <p>{usePassword ? "Confirma tu identidad con tu contraseña." : "Tu cuenta está lista. Confirma tu identidad en este dispositivo."}</p>
          </div>

          {editIdentifier ? (
            <label className="credential-card">
              <span className="field-label">Cuenta</span>
              <input
                autoComplete="username"
                placeholder="Correo, CLABE o tarjeta"
                value={identifier}
                onChange={(event) => setIdentifier(event.target.value)}
              />
            </label>
          ) : (
            <div className="saved-account-card">
              <span className="saved-account-avatar">{identifier.slice(0, 1).toUpperCase()}</span>
              <span className="saved-account-copy"><small>Cuenta guardada</small><strong>{identifier}</strong></span>
              <button type="button" onClick={changeAccount}>Cambiar</button>
            </div>
          )}

          {usePassword ? (
            <label className="credential-card password-card">
              <span className="field-label">Contraseña</span>
              <input
                autoFocus
                autoComplete="current-password"
                placeholder="••••••••"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
              />
            </label>
          ) : (
            <div className="biometric-ready">
              <span className="biometric-glyph" aria-hidden="true">◎</span>
              <span><strong>Face ID o huella</strong><small>Se solicitará al tocar “Entrar”.</small></span>
            </div>
          )}

          {error && <div className="info-banner warning"><span>!</span><span>{error}</span></div>}
          <button className="btn btn-primary login-cta" disabled={loading || (!usePassword && biometricAvailable !== true)}>
            {loading ? (usePassword ? "Entrando…" : "Verificando…") : biometricAvailable === null && !usePassword ? "Preparando biometría…" : "Entrar"}
          </button>

          {!usePassword && (
            <button type="button" className="access-switch" onClick={() => { setError(null); setUsePassword(true); }} disabled={loading}>
              Entrar con contraseña
            </button>
          )}
          {usePassword && biometricAvailable && savedBiometricIdentifier && (
            <button type="button" className="access-switch biometric-switch" onClick={() => { setError(null); setUsePassword(false); }} disabled={loading}>
              Usar Face ID o huella
            </button>
          )}
          {usePassword && biometricAvailable && !savedBiometricIdentifier && (
            <button type="button" className="biometric-enroll-link" onClick={enrollFromLogin} disabled={loading}>
              Activar biometría con mi contraseña
            </button>
          )}
          <button type="button" className="access-switch" onClick={() => switchMode("register")}>Crear una cuenta nueva</button>
          {usePassword && <div className="demo-note">Demo · clave <b>4152</b> / contraseña <b>demo1234</b></div>}
        </form>
      )}

      {mode === "enroll" && pendingRegistration && (
        <main className="login-content biometric-setup">
          <div className="biometric-hero" aria-hidden="true"><span>◎</span></div>
          <div className="login-heading centered">
            <span className="access-kicker">Acceso creado</span>
            <h1>Activa tu biometría</h1>
            <p>Usa Face ID, huella o el PIN seguro de este dispositivo para entrar más rápido la próxima vez.</p>
          </div>
          {error && <div className="info-banner warning"><span>!</span><span>{error}</span></div>}
          <button type="button" className="btn btn-primary login-cta" onClick={() => enrollPasskey(pendingRegistration)} disabled={loading || !biometricAvailable}>
            {loading ? "Configurando…" : biometricAvailable ? "Activar Face ID o huella" : "Biometría no disponible"}
          </button>
          <button type="button" className="access-switch" onClick={() => finishLogin(pendingRegistration.response, pendingRegistration.accountIdentifier)} disabled={loading}>
            Ahora no, continuar
          </button>
          <div className="security-note"><span>✓</span> Banorte no almacena tu rostro ni tu huella.</div>
        </main>
      )}

      <div className="brand-wave"><PoweredBy /></div>
    </div>
  );
}
