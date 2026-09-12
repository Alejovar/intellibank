import { useEffect, useState } from "react";
import { useAppStore } from "./store/useAppStore";
import LoginScreen from "./screens/LoginScreen";
import HomeScreen from "./screens/HomeScreen";
import SavedScreensScreen from "./screens/SavedScreensScreen";
import MoreScreen from "./screens/MoreScreen";
import InvestmentShell from "./components/InvestmentShell";
import { api } from "./api/client";

export default function App() {
  const token = useAppStore((s) => s.token);
  const pushChat = useAppStore((s) => s.pushChat);
  const applyResponse = useAppStore((s) => s.applyResponse);
  const setLoading = useAppStore((s) => s.setLoading);
  const setError = useAppStore((s) => s.setError);
  const [page, setPage] = useState("home");

  useEffect(() => {
    if (token) setPage("home");
  }, [token]);

  const sendToAgent = async (message, inputMode = "text") => {
    if (!message?.trim()) return;
    setPage("home");
    setError(null);
    pushChat("user", message.trim());
    setLoading(true);
    try {
      const result = await api.sendMessage(message.trim(), { inputMode });
      applyResponse(result.response);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return <><div className="app-backdrop" /><LoginScreen /></>;
  }

  const screen = page === "history"
    ? <SavedScreensScreen />
    : page === "profile"
      ? <MoreScreen />
      : <HomeScreen onStartAssistant={sendToAgent} />;

  return (
    <>
      <div className="app-backdrop" />
      <InvestmentShell page={page} onNavigate={setPage} onSend={sendToAgent}>
        {screen}
      </InvestmentShell>
    </>
  );
}
