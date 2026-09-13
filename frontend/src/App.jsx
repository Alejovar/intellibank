import { useEffect, useState } from "react";
import { useAppStore } from "./store/useAppStore";
import LoginScreen from "./screens/LoginScreen";
import OnboardingScreen from "./screens/OnboardingScreen";
import AssistantScreen from "./screens/AssistantScreen";
import HomeScreen from "./screens/HomeScreen";
import SavedScreensScreen from "./screens/SavedScreensScreen";
import MoreScreen from "./screens/MoreScreen";

export default function App() {
  const token = useAppStore((s) => s.token);
  const onboardingDone = useAppStore((s) => s.onboardingDone);
  const [page, setPage] = useState("home");
  const [initialMessage, setInitialMessage] = useState(null);

  useEffect(() => {
    if (token) setPage("home");
  }, [token]);

  const openAssistant = (message = null) => {
    setInitialMessage(message);
    setPage("assistant");
  };

  let screen;
  if (!token) screen = <LoginScreen />;
  else if (!onboardingDone) screen = <OnboardingScreen />;
  else if (page === "home") {
    screen = <HomeScreen onNavigate={setPage} onStartAssistant={openAssistant} />;
  } else if (page === "saved") {
    screen = <SavedScreensScreen onNavigate={setPage} onStartAssistant={openAssistant} />;
  } else if (page === "more") {
    screen = <MoreScreen onNavigate={setPage} onStartAssistant={openAssistant} />;
  } else {
    screen = (
      <AssistantScreen
        initialMessage={initialMessage}
        onInitialMessageConsumed={() => setInitialMessage(null)}
        onNavigate={setPage}
      />
    );
  }

  return (
    <>
      <div className="app-backdrop" />
      {screen}
    </>
  );
}
