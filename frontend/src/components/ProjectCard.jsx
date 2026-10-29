import ImageSlot from "./ImageSlot";
import styles from "./ProjectCard.module.scss";

export default function ProjectCard({ title, description, tags = [], coverSrc, coverAlt }) {
  return (
    <div className={styles.card}>
      {coverSrc && <ImageSlot src={coverSrc} alt={coverAlt} shape="rect" width="100%" height={180} radius={0} />}
      <div className={styles.body}>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.description}>{description}</p>
        {tags.length > 0 && (
          <ul className={styles.tags}>
            {tags.map((tag) => (
              <li key={tag} className={styles.tag}>
                {tag}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
