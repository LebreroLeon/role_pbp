import { Navigate, Route, Routes } from "react-router-dom";

import { GuestRoute, ProtectedRoute } from "./components/auth/ProtectedRoute";
import { RoleGate } from "./components/auth/RoleGate";
import { CampaignLayout } from "./components/layout/CampaignLayout";
import { Layout } from "./components/layout/Layout";
import { CreateCampaignWizard } from "./features/campaign/CreateCampaignWizard";
import { CampaignHubPage } from "./pages/CampaignHubPage";
import { CampaignsPage } from "./pages/CampaignsPage";
import { ChatPage } from "./pages/ChatPage";
import { HomePage } from "./pages/HomePage";
import { LibraryPage } from "./pages/LibraryPage";
import { LoginPage } from "./pages/LoginPage";
import { MasterDeskPage } from "./pages/MasterDeskPage";
import { RegisterPage } from "./pages/RegisterPage";
import { WorldPage } from "./pages/WorldPage";
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
          <Route path="campaigns/new" element={<CreateCampaignWizard />} />

          <Route path="campaigns/:campaignId" element={<CampaignLayout />}>
            <Route index element={<CampaignHubPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="mundo" element={<WorldPage />} />
            <Route
              path="biblioteca"
              element={
                <RoleGate role="MASTER">
                  <LibraryPage />
                </RoleGate>
              }
            />
            <Route path="mesa" element={<MasterDeskPage />} />
            {/* Rutas legacy */}
            <Route path="master" element={<Navigate to="../mesa" replace />} />
            <Route path="entities" element={<Navigate to="../mundo" replace />} />
          </Route>
        </Route>
      </Route>
    </Routes>
  );
}
