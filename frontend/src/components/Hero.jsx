import ProfilePhoto from "./ProfilePhoto";
import CircleLink from "./CircleLink";
import { useI18n } from "../i18n/LanguageContext";
import { profile } from "../data/profile";
import styles from "./Hero.module.scss";

export default function Hero({ bio }) {
  const { t } = useI18n();

  const navCircles = [
    { to: "/about", variant: "gold", label: t.nav.about },
    { to: "/projects", variant: "slate", label: t.nav.projects },
    { to: "/beyond", variant: "forest", label: t.nav.beyond_code },
  ];

  return (
    <section className={styles.hero}>
      <ProfilePhoto src={bio?.photo?.url} alt={bio?.photo?.alt ?? bio?.full_name ?? profile.name} />

      <div className={styles.content}>
        <h1 className={styles.greeting}>{bio?.greeting}</h1>
        <div className={styles.tagline}>{bio?.tagline}</div>
        <p className={styles.summary}>{bio?.headline}</p>
        <nav aria-label={t.common.mainNav} className={styles.nav}>
          {navCircles.map(({ label, ...linkProps }) => (
            <CircleLink key={label} {...linkProps}>
              {label}
            </CircleLink>
          ))}
        </nav>
      </div>
    </section>
  );
}
