import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout/Layout";
import { ChatPage } from "./pages/ChatPage";
import { HomePage } from "./pages/HomePage";
import { MasterPanelPage } from "./pages/MasterPanelPage";
import "./App.css";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="master" element={<MasterPanelPage />} />
      </Route>
    </Routes>
  );
}
