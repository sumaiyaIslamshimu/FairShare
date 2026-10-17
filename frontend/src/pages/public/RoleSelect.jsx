import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";

export default function RoleSelect() {
  return (
    <>
      <div className="page-title">
        <h1>Choose Your Experience</h1>
        <p className="muted">Pick how you want to use FairShare</p>
      </div>
      <div className="role-grid">
        <Card>
          <h2>Shopper</h2>
          <p className="muted">Search products, compare prices, buy from FairShare sellers, and rent items.</p>
          <p><Button variant="primary" block to="/login/user">User Login</Button></p>
          <p><Button block to="/register/user">Create User Account</Button></p>
        </Card>
        <Card>
          <h2>Seller</h2>
          <p className="muted">List products, manage inventory and promotions, and fulfil orders.</p>
          <p><Button variant="primary" block to="/login/seller">Seller Login</Button></p>
          <p><Button block to="/register/seller">Create Seller Account</Button></p>
        </Card>
        <Card>
          <h2>Admin</h2>
          <p className="muted">Restricted. Administrator accounts are created by the platform team, not through sign-up.</p>
          <p><Button variant="primary" block to="/login/admin">Admin Login</Button></p>
        </Card>
      </div>
    </>
  );
}