import "./SuggestedForYou.css";

const suggestedProducts = [
  {
    id: "suggested-1",
    brand: "Sony",
    category: "Electronics",
    name: "Sony WH-1000XM5 Headphones",
    price: 34999,
    rating: 4.8,
    marketplace: "Daraz",
  },
  {
    id: "suggested-2",
    brand: "Samsung",
    category: "Electronics",
    name: "Samsung Galaxy Buds",
    price: 8999,
    rating: 4.6,
    marketplace: "Pickaboo",
  },
  {
    id: "suggested-3",
    brand: "Logitech",
    category: "Electronics",
    name: "Logitech Wireless Mouse",
    price: 2499,
    rating: 4.5,
    marketplace: "Daraz",
  },
  {
    id: "suggested-4",
    brand: "Bose",
    category: "Electronics",
    name: "Bose QuietComfort Headphones",
    price: 29999,
    rating: 4.7,
    marketplace: "Pickaboo",
  },
];

const SuggestedForYou = () => {
  return (
    <section className="suggested-section">
      <div className="suggested-header">
        <div>
          <h2>Suggested for You</h2>
          <p>Products you may be interested in</p>
        </div>

        <button className="suggested-view-all">
          View All
        </button>
      </div>

      <div className="suggested-products">
        {suggestedProducts.map((product) => (
          <div className="suggested-card" key={product.id}>
            <div className="suggested-image">
              <span>Product</span>
            </div>

            <div className="suggested-content">
              <p className="suggested-category">
                {product.brand} · {product.category}
              </p>

              <h3>{product.name}</h3>

              <div className="suggested-rating">
                <span>★</span>
                <span>{product.rating}</span>
              </div>

              <div className="suggested-price">
                ৳{product.price.toLocaleString()}
              </div>

              <p className="suggested-marketplace">
                {product.marketplace}
              </p>

              <button className="suggested-button">
                View Product
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default SuggestedForYou;