import { RouterProvider } from "react-router-dom";
import { LanguageProvider } from "./i18n/LanguageContext";
import { router } from "./router";

export default function App() {
  return (
    <LanguageProvider>
      <RouterProvider router={router} />
    </LanguageProvider>
  );
}
