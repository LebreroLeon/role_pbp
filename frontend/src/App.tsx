import { Route, Routes } from "react-router-dom";

import { GuestRoute, ProtectedRoute } from "./components/auth/ProtectedRoute";
import { RoleGate } from "./components/auth/RoleGate";
import { Layout } from "./components/layout/Layout";
import { CampaignHubPage } from "./pages/CampaignHubPage";
import { CampaignsPage } from "./pages/CampaignsPage";
import { ChatPage } from "./pages/ChatPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { MasterPanelPage } from "./pages/MasterPanelPage";
import { RegisterPage } from "./pages/RegisterPage";
import "./App.css";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />

        <Route element={<GuestRoute />}>
          <Route path="login" element={<LoginPage />} />
          <Route path="register" element={<RegisterPage />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route path="campaigns" element={<CampaignsPage />} />
          <Route path="campaigns/:campaignId" element={<CampaignHubPage />} />
          <Route path="campaigns/:campaignId/chat" element={<ChatPage />} />
          <Route
            path="campaigns/:campaignId/master"
            element={
              <RoleGate role="MASTER">
                <MasterPanelPage />
              </RoleGate>
            }
          />
        </Route>
      </Route>
    </Routes>
  );
}
