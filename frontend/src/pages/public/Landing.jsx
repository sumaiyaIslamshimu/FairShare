import Button from "../../components/Button.jsx";
import { CompareArt, StepCompare, StepSearch, StepTrack } from "../../components/art/Illustrations.jsx";
import "../../styles/landing.css";

const STORES = ["Daraz", "Pickaboo", "Chaldal", "Shwapno", "Agora", "Rokomari"];

const STEPS = [
  { no: "01", art: <StepSearch />, title: "Search",
    text: "Search by name, brand or category across supported stores and FairShare sellers." },
  { no: "02", art: <StepCompare />, title: "Compare",
    text: "See identical products side by side with size, availability and when each price was last updated." },
  { no: "03", art: <StepTrack />, title: "Track or buy",
    text: "Set a target price and get an alert on a drop, or buy from an approved FairShare seller." },
];

const Icon = ({ children }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{children}</svg>
);

const FEATURES = [
  { title: "Compare prices",
    text: "See listings from Daraz, Pickaboo, Chaldal, Shwapno, Agora and Rokomari next to FairShare sellers, with clear freshness labels.",
    icon: <Icon><path d="M12 3v18M7 21h10M5 7h14" /><path d="M5 7l-3 7a3 3 0 0 0 6 0L5 7zM19 7l-3 7a3 3 0 0 0 6 0l-3-7z" /></Icon> },
  { title: "Sell on FairShare",
    text: "Sellers list products, manage stock and promotions, and handle orders in one portal after admin approval.",
    icon: <Icon><path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6l7-3z" /><path d="M9 12l2 2 4-4" /></Icon> },
  { title: "Rent short-term",
    text: "A separate rental marketplace where verified owners list items and renters request dates.",
    icon: <Icon><rect x="3" y="5" width="18" height="16" rx="3" /><path d="M8 3v4M16 3v4M3 10h18" /></Icon> },
];

export default function Landing() {
  return (
    <main className="landing">
      <div className="l-wrap">
        <section className="l-hero">
          <span className="l-eyebrow">Price comparison for Bangladesh</span>
          <h1 className="l-title">Buy, Sell, Rent—<em>Redefined</em></h1>
          <p className="l-sub">
            Compare prices across Bangladeshi online stores, buy from verified FairShare sellers,
            and rent items from other people — all in one marketplace.
          </p>
          <div className="l-actions">
            <Button variant="primary" to="/register/user">Start Shopping →</Button>
            <Button to="/register/seller">Become a Seller</Button>
          </div>
          <ul className="l-trust">
            <li>Prices labelled fresh or possibly outdated</li>
            <li>Missing details show “Not available”</li>
            <li>Sellers approved by an admin</li>
          </ul>
          <CompareArt className="l-art" />
        </section>

        <div className="l-stores">
          <small>Supported stores</small>
          {STORES.map((s) => <span className="l-pill" key={s}>{s}</span>)}
        </div>

        <section className="l-section">
          <h2>How it works</h2>
          <p className="l-lead">Three simple steps to the fairest price.</p>
          <div className="l-grid">
            {STEPS.map((s) => (
              <article className="l-card" key={s.no}>
                {s.art}
                <div className="l-step-no">STEP {s.no}</div>
                <h3 style={{ marginTop: 4 }}>{s.title}</h3>
                <p>{s.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="l-section">
          <h2>One marketplace, three ways to use it</h2>
          <p className="l-lead">Shop smarter, sell with confidence, or rent what you need.</p>
          <div className="l-grid">
            {FEATURES.map((f) => (
              <article className="l-card" key={f.title}>
                <div className="l-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="l-cta">
          <h2>Find the fairest price in one place</h2>
          <p>Create a free account and start comparing in a minute.</p>
          <div className="l-actions">
            <Button variant="primary" to="/register/user">Create an account</Button>
            <Button to="/roles">Sign in</Button>
          </div>
        </section>

        <footer className="l-footer">FairShare · University of Asia Pacific, Department of CSE</footer>
      </div>
    </main>
  );
}