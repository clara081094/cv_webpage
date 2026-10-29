import Header from "../components/Header";
import BeyondCard from "../components/BeyondCard";
import Footer from "../components/Footer";
import useApi from "../hooks/useApi";
import { useI18n } from "../i18n/LanguageContext";
import layout from "../styles/layout.module.scss";
import styles from "./Beyond.module.scss";

export default function Beyond() {
  const { t } = useI18n();
  const { data: items, error, loading } = useApi("/beyond?per_page=100");

  return (
    <div className={layout.pageShell}>
      <Header />

      <main className={layout.main}>
        <section className={styles.section}>
          <div className={styles.container}>
            <div className={styles.eyebrow}>{t.beyond.eyebrow}</div>
            <h2 className={styles.title}>{t.beyond.title}</h2>

            {error && <p className={styles.message}>{t.common.loadError}</p>}
            {!loading && items?.length === 0 && <p className={styles.message}>{t.beyond.empty}</p>}

            <div className={styles.list}>
              {(items ?? []).map((item) => (
                <BeyondCard
                  key={item.id}
                  title={item.title}
                  data={item.data}
                  status={item.status}
                  tags={item.tags}
                  author={item.metadata?.author}
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
