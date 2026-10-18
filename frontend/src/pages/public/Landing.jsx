import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";

export default function Landing() {
  return (
    <>
      <section className="hero">
        <h1>Buy, Sell, Rent—Redefined</h1>
        <p>Compare prices across Bangladeshi online stores, buy from verified FairShare sellers, and rent items from other people — all in one marketplace.</p>
        <div className="actions">
          <Button variant="primary" to="/register/user">Start Shopping</Button>
          <Button to="/register/seller">Become a Seller</Button>
        </div>
      </section>
      <section className="feature-grid">
        <Card>
          <h3>Compare prices</h3>
          <p className="muted">See listings from Daraz, Pickaboo, Chaldal, Shwapno, Agora and Rokomari next to FairShare sellers, with clear freshness labels.</p>
        </Card>
        <Card>
          <h3>Sell on FairShare</h3>
          <p className="muted">Sellers list products, manage stock and promotions, and handle orders in one portal after admin approval.</p>
        </Card>
        <Card>
          <h3>Rent short-term</h3>
          <p className="muted">A separate rental marketplace where verified owners list items and renters request dates.</p>
        </Card>
      </section>
    </>
  );
}