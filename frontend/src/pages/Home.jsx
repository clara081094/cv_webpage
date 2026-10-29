import Header from "../components/Header";
import Hero from "../components/Hero";
import Footer from "../components/Footer";
import useApi from "../hooks/useApi";
import layout from "../styles/layout.module.scss";

export default function Home() {
  const { data: bio } = useApi("/bio");

  return (
    <div className={layout.pageShell}>
      <Header name={bio?.full_name} resumeHref={bio?.resume_url ?? undefined} />
      <main className={layout.main}>
        <Hero bio={bio} />
      </main>
      <Footer />
    </div>
  );
}
