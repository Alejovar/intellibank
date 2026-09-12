import { useEffect, useState } from "react";
import { useAppStore } from "./store/useAppStore";
import LoginScreen from "./screens/LoginScreen";
import OnboardingScreen from "./screens/OnboardingScreen";
import CategorySelection from "./screens/CategorySelection";
import AssistantScreen from "./screens/AssistantScreen";
import HomeScreen from "./screens/HomeScreen";
import SavedScreensScreen from "./screens/SavedScreensScreen";
import MoreScreen from "./screens/MoreScreen";

export default function App() {
  const token = useAppStore((s) => s.token);
  const onboardingDone = useAppStore((s) => s.onboardingDone);
  const [page, setPage] = useState("home");
  const [categoryPicked, setCategoryPicked] = useState(false);
  const [initialMessage, setInitialMessage] = useState(null);

  useEffect(() => {
    if (token) setPage("home");
  }, [token]);

  const openAssistant = (message = null) => {
    setInitialMessage(message);
    setCategoryPicked(Boolean(message));
    setPage("assistant");
  };

  const changeCategories = () => {
    setInitialMessage(null);
    setCategoryPicked(false);
    setPage("assistant");
  };

  let screen;
  if (!token) screen = <LoginScreen />;
  else if (!onboardingDone) screen = <OnboardingScreen />;
  else if (page === "home") {
    screen = <HomeScreen onNavigate={setPage} onStartAssistant={openAssistant} />;
  } else if (page === "saved") {
    screen = <SavedScreensScreen onNavigate={setPage} />;
  } else if (page === "more") {
    screen = <MoreScreen onNavigate={setPage} onChangeCategories={changeCategories} />;
  } else if (!categoryPicked) {
    screen = <CategorySelection onNavigate={setPage} onContinue={(msg) => {
      setInitialMessage(msg || null);
      setCategoryPicked(true);
    }} />;
  } else {
    screen = (
      <AssistantScreen
        initialMessage={initialMessage}
        onInitialMessageConsumed={() => setInitialMessage(null)}
        onNavigate={setPage}
        onChangeCategories={changeCategories}
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
