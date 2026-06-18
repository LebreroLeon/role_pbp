import { Link, NavLink, Outlet } from "react-router-dom";
import { useState } from "react";
import { LayoutDashboard, LogOut, Scroll, User } from "lucide-react";

import { SectionToneProvider } from "../ui";
import { PlayerNameModal } from "../../features/auth/PlayerNameModal";
import { useLogout } from "../../hooks/mutations/useAuthMutations";
import { useAuthStore } from "../../stores/authStore";

export function Layout() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  const logout = useLogout();
  const [nameModalOpen, setNameModalOpen] = useState(false);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header__brand">
          <span className="app-header__logo" aria-hidden>
            <Scroll size={20} strokeWidth={2} />
          </span>
          <div>
            <p className="eyebrow">Project Chronicler</p>
            <h1>
              <Link to="/">RolePBP</Link>
            </h1>
          </div>
        </div>
        <nav>
          {isAuthenticated ? (
            <>
              <button
                type="button"
                className="nav-user nav-user--button"
                onClick={() => setNameModalOpen(true)}
                title="Cambiar nombre visible"
              >
                <User size={15} aria-hidden />
                {user?.display_name}
              </button>
              <NavLink to="/campaigns" className="nav-link">
                <LayoutDashboard size={15} aria-hidden />
                Campañas
              </NavLink>
              <button type="button" className="link-button" onClick={logout}>
                <LogOut size={15} aria-hidden />
                Salir
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">
                Entrar
              </Link>
              <Link to="/register" className="nav-link">
                Registro
              </Link>
            </>
          )}
        </nav>
      </header>
      <main className="app-main">
        <SectionToneProvider>
          <Outlet />
        </SectionToneProvider>
      </main>
      {nameModalOpen && user && (
        <PlayerNameModal currentName={user.display_name} onClose={() => setNameModalOpen(false)} />
      )}
    </div>
  );
}
