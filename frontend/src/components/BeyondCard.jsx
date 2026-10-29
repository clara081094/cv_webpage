import { useI18n } from "../i18n/LanguageContext";
import styles from "./BeyondCard.module.scss";

export default function BeyondCard({ title, data, status, tags = [], author }) {
  const { t } = useI18n();
  // Blank lines in `data` separate paragraphs.
  const paragraphs = (data ?? "").split(/\n{2,}/).filter(Boolean);

  return (
    <article className={styles.card}>
      <header className={styles.header}>
        {status && <span className={styles.status}>{t.beyond.statuses[status] ?? status}</span>}
        <h3 className={styles.title}>{title}</h3>
        {author && (
          <div className={styles.author}>
            {t.beyond.by} {author}
          </div>
        )}
      </header>
      <div className={styles.body}>
        {paragraphs.map((paragraph) => (
          <p key={paragraph.slice(0, 40)}>{paragraph}</p>
        ))}
      </div>
      {tags.length > 0 && (
        <ul className={styles.tags}>
          {tags.map((tag) => (
            <li key={tag} className={styles.tag}>
              {tag}
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}
