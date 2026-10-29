import SocialIcon from "./icons/SocialIcon";
import useApi from "../hooks/useApi";
import { useI18n } from "../i18n/LanguageContext";
import styles from "./Footer.module.scss";

// Fetches the bio itself so every page can drop it in without passing props.
export default function Footer() {
  const { t } = useI18n();
  const { data: bio } = useApi("/bio");
  const phone = bio?.phone;
  const email = bio?.email;
  const socialLinks = bio?.social_links ?? [];

  return (
    <footer id="contact" className={styles.footer}>
      <div className={styles.inner}>
        {phone && (
          <div>
            <div className={`${styles.label} ${styles["label--forest"]}`}>{t.footer.phoneLabel}</div>
            <a href={`tel:${phone.replace(/\s+/g, "")}`} className={styles.value}>
              {phone}
            </a>
          </div>
        )}
        {email && (
          <div>
            <div className={`${styles.label} ${styles["label--forest"]}`}>{t.footer.emailLabel}</div>
            <a href={`mailto:${email}`} className={styles.value}>
              {email}
            </a>
          </div>
        )}
        {socialLinks.length > 0 && (
          <div>
            <div className={`${styles.label} ${styles["label--ink"]}`}>{t.footer.followLabel}</div>
            <div className={styles.socials}>
              {socialLinks.map(({ id, icon_name: iconName, label, url }) => (
                <a
                  key={id}
                  href={url}
                  aria-label={label}
                  className={styles.socialLink}
                  target="_blank"
                  rel="noreferrer"
                >
                  <SocialIcon name={iconName} />
                </a>
              ))}
            </div>
          </div>
        )}
        <p className={styles.credit}>
          {t.footer.credit}{" "}
          <span role="img" aria-label={t.footer.heart}>
            ❤️
          </span>
        </p>
      </div>
    </footer>
  );
}
