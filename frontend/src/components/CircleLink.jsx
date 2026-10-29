import { Link } from "react-router-dom";
import styles from "./CircleLink.module.scss";

// Same round-button shape as the design, reused for internal routes and
// same-page anchors alike (react-router Link vs. plain <a>).
export default function CircleLink({ to, href, variant, children }) {
  const className = `${styles.circle} ${styles[variant]}`;

  if (to) {
    return (
      <Link to={to} className={className}>
        {children}
      </Link>
    );
  }

  return (
    <a href={href} className={className}>
      {children}
    </a>
  );
}
