import { useEffect, useState } from "react";
import { useAppStore } from "./store/useAppStore";
import LoginScreen from "./screens/LoginScreen";
import OnboardingScreen from "./screens/OnboardingScreen";
import AssistantScreen from "./screens/AssistantScreen";
import HomeScreen from "./screens/HomeScreen";
import SavedScreensScreen from "./screens/SavedScreensScreen";
import MoreScreen from "./screens/MoreScreen";
import ThemeSelectionScreen from "./screens/ThemeSelectionScreen";

export default function App() {
  const token = useAppStore((s) => s.token);
  const onboardingDone = useAppStore((s) => s.onboardingDone);
  const topicsOnboarded = useAppStore((s) => s.topicsOnboarded);
  const completeTopicsOnboarding = useAppStore((s) => s.completeTopicsOnboarding);
  const [page, setPage] = useState("home");
  const [initialMessage, setInitialMessage] = useState(null);

  useEffect(() => {
    if (token) setPage("home");
  }, [token]);

  const openAssistant = (message = null) => {
    setInitialMessage(message);
    setPage("assistant");
  };

  const finishTopics = (nextPage = "home") => {
    completeTopicsOnboarding();
    setPage(nextPage);
  };

  const startFromThemeInput = (message) => {
    completeTopicsOnboarding();
    openAssistant(message);
  };

  let screen;
  if (!token) screen = <LoginScreen />;
  else if (!onboardingDone) screen = <OnboardingScreen />;
  else if (!topicsOnboarded) {
    screen = (
      <ThemeSelectionScreen
        onContinue={() => finishTopics("home")}
        onSkip={() => finishTopics("home")}
        onFreeInput={startFromThemeInput}
        onNavigate={(nextPage) => finishTopics(nextPage)}
      />
    );
  }
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
