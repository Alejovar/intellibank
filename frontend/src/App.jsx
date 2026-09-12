import { useState } from "react";
import { useAppStore } from "./store/useAppStore";
import LoginScreen from "./screens/LoginScreen";
import OnboardingScreen from "./screens/OnboardingScreen";
import CategorySelection from "./screens/CategorySelection";
import AssistantScreen from "./screens/AssistantScreen";

export default function App() {
  const token = useAppStore((s) => s.token);
  const onboardingDone = useAppStore((s) => s.onboardingDone);
  const [categoryPicked, setCategoryPicked] = useState(false);
  const [initialMessage, setInitialMessage] = useState(null);

  let screen;
  if (!token) screen = <LoginScreen />;
  else if (!onboardingDone) screen = <OnboardingScreen />;
  else if (!categoryPicked) {
    screen = (
      <CategorySelection
        onContinue={(msg) => {
          setInitialMessage(msg || null);
          setCategoryPicked(true);
        }}
      />
    );
  } else {
    screen = <AssistantScreen initialMessage={initialMessage} />;
  }

  return (
    <>
      <div className="app-backdrop" />
      {screen}
    </>
  );
}
