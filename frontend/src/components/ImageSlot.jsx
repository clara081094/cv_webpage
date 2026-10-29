import styles from "./ImageSlot.module.scss";

// Image frame shared by ProfilePhoto and ProjectCard: any shape/size, with a
// neutral block when there is no image yet. Images are managed through the
// admin API, not uploaded from the public site.
// width/height/radius/boxShadow stay inline props since they're genuinely
// per-usage dynamic values, not part of the shared visual language.
export default function ImageSlot({
  src,
  alt = "",
  shape = "rounded",
  width,
  height,
  radius = 12,
  boxShadow,
}) {
  const wrapperStyle = {
    width,
    height,
    boxShadow,
    borderRadius: shape === "circle" ? undefined : radius,
  };

  return (
    <div className={`${styles.wrapper} ${shape === "circle" ? styles.circle : ""}`} style={wrapperStyle}>
      {src ? <img src={src} alt={alt} className={styles.preview} /> : <div className={styles.empty} />}
    </div>
  );
}
