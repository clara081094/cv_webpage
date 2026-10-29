import { Link } from "react-router-dom";
import LanguageSwitcher from "./LanguageSwitcher";
import { useI18n } from "../i18n/LanguageContext";
import { profile } from "../data/profile";
import styles from "./Header.module.scss";

export default function Header({ name = profile.name, resumeHref = profile.resumeHref }) {
  const { t } = useI18n();

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <Link to="/" className={styles.logo}>
          {name}
        </Link>
        <div className={styles.actions}>
          <LanguageSwitcher />
          <a href={resumeHref} download className={styles.resumeCta}>
            {t.common.downloadCv}
          </a>
        </div>
      </div>
    </header>
  );
}
