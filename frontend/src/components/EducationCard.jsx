import styles from "./EducationCard.module.scss";

export default function EducationCard({ period, title, institution, description }) {
  return (
    <div className={styles.card}>
      <div className={styles.period}>{period}</div>
      <h3 className={styles.title}>{title}</h3>
      <div className={styles.institution}>{institution}</div>
      {description && <p className={styles.description}>{description}</p>}
    </div>
  );
}
