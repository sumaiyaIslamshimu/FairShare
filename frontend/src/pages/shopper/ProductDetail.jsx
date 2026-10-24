import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getSellerProduct } from "../../api/shopping.js";
import { listProductReviews } from "../../api/reviews.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import Loading from "../../components/Loading.jsx";
import Pagination from "../../components/Pagination.jsx";
import Stars from "../../components/Stars.jsx";
import { useCart } from "../../context/CartContext.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatDate, formatPrice, formatSize } from "../../utils/format.js";

export default function ProductDetail() {
  const { id } = useParams();
  const [page, setPage] = useState(1);
  const [notice, setNotice] = useState(null);
  const [addError, setAddError] = useState(null);
  const { add: addItem } = useCart();
  const product = useLoad(() => getSellerProduct(id), [id]);
  const reviews = useLoad(() => listProductReviews(id, page), [id, page]);

  const add = async () => {
    setAddError(null);
    setNotice(null);
    try {
      await addItem(id, 1);
      setNotice("Added to your cart.");
    } catch (err) {
      setAddError(err);
    }
  };

  if (product.loading && !product.data) return <Loading />;
  if (product.error) return <ErrorBox error={product.error} />;
  const p = product.data;
  if (!p) return null;
  const inStock = p.availability === "in_stock";
  const size = formatSize(p.quantity, p.unit);
  const attrs = Object.entries(p.attributes || {});
  const r = reviews.data;

  return (
    <>
      <p><Link to="/app/search">← Back to search</Link></p>
      <h1>{p.title}</h1>
      <p className="subtitle">Sold on FairShare{p.seller_name ? ` by ${p.seller_name}` : ""}{p.brand ? ` · ${p.brand}` : ""}</p>

      <Card style={{ marginBottom: 16 }}>
        {p.images?.[0] && <img src={p.images[0]} alt={p.title} style={{ maxWidth: 240 }} />}
        <p>
          <strong>{formatPrice(p.effective_price_paisa, p.currency)}</strong>
          {p.discount_percent ? <> <s>{formatPrice(p.price_paisa, p.currency)}</s> <Badge tone="amber">{p.discount_percent}% off</Badge></> : null}
        </p>
        <p><Badge tone={inStock ? "green" : "red"}>{inStock ? "In Stock" : "Out of stock"}</Badge>{size && <> · Size: {size}</>}</p>
        {p.description && <p>{p.description}</p>}
        {attrs.length > 0 && (
          <dl>
            {attrs.map(([k, v]) => (<div key={k}><dt>{k}</dt><dd>{String(v)}</dd></div>))}
          </dl>
        )}
        <ErrorBox error={addError} />
        {notice && <p role="status">{notice}</p>}
        <Button variant="primary" onClick={add} disabled={!inStock}>Add to cart</Button>
      </Card>

      <h2>Reviews</h2>
      {r && r.count > 0 && <p><Stars value={r.average} /> {r.average} out of 5 · {r.count} {r.count === 1 ? "review" : "reviews"}</p>}
      <ErrorBox error={reviews.error} />
      {reviews.loading && !r ? <Loading /> : null}
      {r && r.items.length === 0 && <p>No reviews yet. Only shoppers who received this product can review it.</p>}
      {(r?.items || []).map((rv) => (
        <Card key={rv.id} style={{ marginBottom: 12 }}>
          <p><Stars value={rv.rating} /> <strong>{rv.reviewer_name || "A shopper"}</strong> <small>{formatDate(rv.created_at)}</small></p>
          {rv.comment && <p>{rv.comment}</p>}
        </Card>
      ))}
      {r && <Pagination page={r.page} pageSize={r.page_size} total={r.total} onChange={setPage} />}
    </>
  );
}