import { useEffect, useState } from "react";
import { useAppStore } from "../store/useAppStore";
import { api } from "../api/client";
import { createPlatformPasskey, platformAuthenticatorAvailable } from "../auth/passkeys";

export default function MoreScreen() {
  const fullName = useAppStore((state) => state.fullName);
  const logout = useAppStore((state) => state.logout);
  const biometricEnabled = useAppStore((state) => state.biometricEnabled);
  const setBiometricEnabled = useAppStore((state) => state.setBiometricEnabled);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [settingUp, setSettingUp] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    platformAuthenticatorAvailable().then(setBiometricAvailable).catch(() => setBiometricAvailable(false));
  }, []);

  const setupBiometric = async () => {
    setSettingUp(true);
    setMessage(null);
    try {
      const options = await api.getPasskeyRegistrationOptions();
      const credential = await createPlatformPasskey(options);
      await api.completePasskeyRegistration(credential, "web", navigator.userAgent);
      setBiometricEnabled(true);
      setMessage("Acceso biométrico configurado en este dispositivo.");
    } catch (error) {
      setMessage(error.name === "NotAllowedError" ? "Configuración cancelada." : error.message);
    } finally {
      setSettingUp(false);
    }
  };

  return (
    <main className="screen-body more-screen shell-page">
      <div><h1 className="screen-title">Perfil</h1><p className="screen-copy">Administra el acceso seguro a tus inversiones.</p></div>
      <section className="profile-card glass-panel">
        <span className="profile-avatar">{fullName?.charAt(0) || "C"}</span>
        <div><strong>{fullName || "Cliente"}</strong><small>Sesión personal de inversiones</small></div>
      </section>
      <section className="settings-card glass-panel">
        <span className="mini-face-id"><i /></span>
        <div><strong>Face ID o huella</strong><small>{biometricEnabled ? "Protección activa en este dispositivo" : "Actívala para entrar sin contraseña"}</small></div>
        {biometricEnabled
          ? <span className="badge">Activo</span>
          : <button onClick={setupBiometric} disabled={!biometricAvailable || settingUp}>{settingUp ? "Activando…" : "Activar"}</button>}
      </section>
      {message && <div className="info-banner tip"><span>{message}</span></div>}
      {!biometricAvailable && !biometricEnabled && <div className="info-banner"><span>Este navegador no expone un autenticador biométrico. La contraseña sigue disponible.</span></div>}
      <button className="btn btn-ghost more-logout" onClick={logout}>Cerrar sesión</button>
    </main>
  );
}
