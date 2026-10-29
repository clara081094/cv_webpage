import { useEffect, useState } from "react";
import { apiGet } from "../api";
import { useI18n } from "../i18n/LanguageContext";

// Fetches `path` in the current locale and refetches when the locale changes.
// The previous data stays on screen while the new language loads, so switching
// ES/EN does not flash an empty page.
export default function useApi(path) {
  const { locale } = useI18n();
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    setState((previous) => ({ ...previous, loading: true }));
    apiGet(path, locale).then(
      (data) => !cancelled && setState({ data, error: null, loading: false }),
      (error) => !cancelled && setState({ data: null, error, loading: false })
    );
    return () => {
      cancelled = true;
    };
  }, [path, locale]);

  return state;
}
