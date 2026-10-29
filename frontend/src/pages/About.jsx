import Header from "../components/Header";
import ExperienceItem from "../components/ExperienceItem";
import EducationCard from "../components/EducationCard";
import LanguageBar from "../components/LanguageBar";
import Footer from "../components/Footer";
import useApi from "../hooks/useApi";
import { useI18n } from "../i18n/LanguageContext";
import layout from "../styles/layout.module.scss";
import styles from "./About.module.scss";

export default function About() {
  const { t } = useI18n();
  const { data, error } = useApi("/about");
  const bio = data?.bio;
  const skills = Object.entries(bio?.metadata?.skills ?? {});

  return (
    <div className={layout.pageShell}>
      <Header name={bio?.full_name} resumeHref={bio?.resume_url ?? undefined} />

      <main className={layout.main}>
        <section className={styles.introSection}>
          <div className={styles.introContainer}>
            <div className={styles.eyebrow}>{t.about.eyebrow}</div>
            <h2 className={styles.title}>{bio?.headline}</h2>
            {error ? <p className={styles.intro}>{t.common.loadError}</p> : <p className={styles.intro}>{bio?.summary}</p>}
          </div>

          {data && (
            <>
              <div className={styles.block}>
                <h3 className={styles.blockTitle}>{t.about.experienceTitle}</h3>
                <div className={styles.timeline}>
                  {data.experience.map((job) => (
                    <ExperienceItem
                      key={job.id}
                      period={job.period}
                      role={job.role}
                      company={job.company}
                      description={job.description}
                      highlights={job.highlights}
                      technologies={job.metadata?.technologies}
                    />
                  ))}
                </div>
              </div>

              <div className={`${styles.block} ${styles["block--tight"]}`}>
                <h3 className={styles.blockTitle}>{t.about.educationTitle}</h3>
                <div className={styles.educationGrid}>
                  {data.education.map((edu) => (
                    <EducationCard
                      key={edu.id}
                      period={edu.period}
                      title={edu.title}
                      institution={edu.institution}
                      description={edu.description}
                    />
                  ))}
                </div>
              </div>

              {skills.length > 0 && (
                <div className={`${styles.block} ${styles["block--tight"]}`}>
                  <h3 className={styles.blockTitle}>{t.about.skillsTitle}</h3>
                  <div className={styles.skillsGrid}>
                    {skills.map(([group, items]) => (
                      <div key={group}>
                        <h4 className={styles.skillGroup}>{t.about.skillGroups[group] ?? group}</h4>
                        <ul className={styles.skillList}>
                          {items.map((skill) => (
                            <li key={skill} className={styles.skill}>
                              {skill}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </section>

        {data && data.languages.length > 0 && (
          <section className={styles.languagesSection}>
            <div className={styles.languagesContainer}>
              <div className={`${styles.eyebrow} ${styles["eyebrow--centered"]}`}>
                {t.about.languagesEyebrow}
              </div>
              <h2 className={`${styles.title} ${styles["title--spaced"]}`}>{t.about.languagesTitle}</h2>
              <div className={styles.languagesList}>
                {data.languages.map((lang) => (
                  <LanguageBar key={lang.id} name={lang.name} level={lang.level} percentage={lang.percentage} />
                ))}
              </div>
            </div>
          </section>
        )}
      </main>

      <Footer />
    </div>
  );
}
