import Header from "../components/Header";
import ProjectCard from "../components/ProjectCard";
import Footer from "../components/Footer";
import useApi from "../hooks/useApi";
import { useI18n } from "../i18n/LanguageContext";
import layout from "../styles/layout.module.scss";
import styles from "./Projects.module.scss";

export default function Projects() {
  const { t } = useI18n();
  const { data: projects, error, loading } = useApi("/projects?per_page=100");

  return (
    <div className={layout.pageShell}>
      <Header />

      <main className={layout.main}>
        <section className={styles.section}>
          <div className={styles.container}>
            <div className={styles.eyebrow}>{t.projects.eyebrow}</div>
            <h2 className={styles.title}>{t.projects.title}</h2>

            {error && <p className={styles.message}>{t.common.loadError}</p>}
            {!loading && projects?.length === 0 && <p className={styles.message}>{t.projects.empty}</p>}

            <div className={styles.grid}>
              {(projects ?? []).map((item) => (
                <ProjectCard
                  key={item.id}
                  title={item.title}
                  description={item.data}
                  tags={item.tags}
                  coverSrc={item.cover?.url}
                  coverAlt={item.cover?.alt ?? item.title}
                />
              ))}
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
