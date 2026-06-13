import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { ProfileProvider } from "./state/profile";
import { UIProvider } from "./state/ui";
import "./styles.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <ProfileProvider>
        <UIProvider>
          <App />
        </UIProvider>
      </ProfileProvider>
    </BrowserRouter>
  </StrictMode>,
);
