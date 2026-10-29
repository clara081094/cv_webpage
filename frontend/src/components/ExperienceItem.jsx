import styles from "./ExperienceItem.module.scss";

export default function ExperienceItem({ period, role, company, description, highlights = [], technologies = [] }) {
  return (
    <div className={styles.item}>
      <div className={styles.rail}>
        <div className={styles.dot} />
        <div className={styles.line} />
      </div>
      <div className={styles.content}>
        <div className={styles.period}>{period}</div>
        <h3 className={styles.role}>{role}</h3>
        <div className={styles.company}>{company}</div>
        {description && <p className={styles.description}>{description}</p>}
        {highlights.length > 0 && (
          <ul className={styles.highlights}>
            {highlights.map((highlight) => (
              <li key={highlight}>{highlight}</li>
            ))}
          </ul>
        )}
        {technologies.length > 0 && (
          <ul className={styles.tags}>
            {technologies.map((tech) => (
              <li key={tech} className={styles.tag}>
                {tech}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
