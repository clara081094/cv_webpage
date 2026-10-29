import ImageSlot from "./ImageSlot";

export default function ProfilePhoto({ src, alt }) {
  return (
    <ImageSlot
      src={src}
      alt={alt}
      shape="circle"
      width={420}
      height="auto"
      boxShadow="0 20px 40px rgba(71,83,107,0.18)"
    />
  );
}
