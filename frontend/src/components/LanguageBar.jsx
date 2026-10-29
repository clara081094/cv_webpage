import styles from "./LanguageBar.module.scss";

export default function LanguageBar({ name, level, percentage }) {
  return (
    <div>
      <div className={styles.row}>
        <span className={styles.name}>{name}</span>
        <span className={styles.level}>{level}</span>
      </div>
      <div className={styles.track}>
        <div className={styles.fill} style={{ "--percentage": `${percentage}%` }} />
      </div>
    </div>
  );
}
