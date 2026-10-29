import { useI18n } from "../i18n/LanguageContext";
import styles from "./LanguageSwitcher.module.scss";

const LOCALES = [
  { code: "es", label: "ES" },
  { code: "en", label: "EN" },
];

export default function LanguageSwitcher() {
  const { locale, setLocale } = useI18n();

  return (
    <div role="group" aria-label="Language" className={styles.group}>
      {LOCALES.map(({ code, label }) => (
        <button
          key={code}
          type="button"
          onClick={() => setLocale(code)}
          aria-pressed={code === locale}
          className={styles.option}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
