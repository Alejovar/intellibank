import BottomNav from "../components/BottomNav";
import { Brand, StatusBar } from "../components/PhoneChrome";
import { useAppStore } from "../store/useAppStore";

export default function MoreScreen({ onNavigate, onChangeCategories }) {
  const fullName = useAppStore((s) => s.fullName);
  const activeCategories = useAppStore((s) => s.activeCategories);
  const logout = useAppStore((s) => s.logout);

  return (
    <div className="phone-shell">
      <StatusBar />
      <div className="app-header">
        <div><Brand compact /><div className="tagline">Cuenta y preferencias</div></div>
      </div>
      <main className="screen-body more-screen">
        <div><h1 className="screen-title">Más</h1><p className="screen-copy">Administra tu perfil y cómo te ayuda el asistente.</p></div>
        <section className="profile-card">
          <span className="profile-avatar">{fullName?.charAt(0) || "C"}</span>
          <div><strong>{fullName || "Cliente"}</strong><small>Sesión personal</small></div>
        </section>
        <section className="settings-card">
          <div><strong>Temas del asistente</strong><small>{activeCategories.length ? activeCategories.join(" · ") : "Aún no elegiste temas"}</small></div>
          <button onClick={onChangeCategories}>Cambiar</button>
        </section>
        <button className="btn btn-ghost more-logout" onClick={logout}>Cerrar sesión</button>
      </main>
      <BottomNav activeTab="more" onChange={onNavigate} />
    </div>
  );
}
