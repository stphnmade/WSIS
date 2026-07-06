import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/fraunces/latin-700.css";
import "@fontsource/fraunces/latin-900.css";
import "@fontsource/fraunces/latin-900-italic.css";
import { App } from "./App";
import "./styles.css";
import "./map-loading.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
