import { Link, Outlet } from "react-router-dom";

import { useLogout } from "../../hooks/mutations/useAuthMutations";
import { useAuthStore } from "../../stores/authStore";

export function Layout() {
  const user = useAuthStore((state) => state.user);
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated());
  const logout = useLogout();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Project Chronicler</p>
          <h1>
            <Link to="/">RolePBP</Link>
          </h1>
        </div>
        <nav>
          {isAuthenticated ? (
            <>
              <span className="nav-user">{user?.display_name}</span>
              <Link to="/campaigns">Campañas</Link>
              <button type="button" className="link-button" onClick={logout}>
                Salir
              </button>
            </>
          ) : (
            <>
              <Link to="/login">Entrar</Link>
              <Link to="/register">Registro</Link>
            </>
          )}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
