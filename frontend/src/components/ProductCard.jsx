function ProductArtwork({ product }) {
  const category = product.category?.toLowerCase() || '';
  const name = product.name?.toLowerCase() || '';

  if (name.includes('headphone') || name.includes('headset')) {
    return (
      <svg className="product-artwork" viewBox="0 0 160 100" aria-hidden="true">
        <path d="M44 57V46a36 36 0 0 1 72 0v11" />
        <path d="M42 51h11v26H42a7 7 0 0 1-7-7V58a7 7 0 0 1 7-7Zm76 0h-11v26h11a7 7 0 0 0 7-7V58a7 7 0 0 0-7-7Z" />
      </svg>
    );
  }

  if (name.includes('airpod') || name.includes('earbud')) {
    return (
      <svg className="product-artwork product-artwork-light" viewBox="0 0 160 100" aria-hidden="true">
        <path d="M40 46 28 35m12 11-12 12m12-12h9m63 0 12-12m-12 12 12 12m-12-12h-9" />
        <rect x="40" y="39" width="39" height="18" rx="9" />
        <rect x="81" y="39" width="39" height="18" rx="9" />
      </svg>
    );
  }

  if (name.includes('tv') || name.includes('monitor') || name.includes('display')) {
    return (
      <svg className="product-artwork product-artwork-blue" viewBox="0 0 160 100" aria-hidden="true">
        <rect x="24" y="19" width="84" height="51" rx="4" />
        <path d="M66 71v10m-14 0h28" />
        <rect x="116" y="23" width="15" height="55" rx="3" />
      </svg>
    );
  }

  const artClass = category.includes('electronic') ? 'product-artwork product-artwork-blue' : 'product-artwork';
  return (
    <svg className={artClass} viewBox="0 0 160 100" aria-hidden="true">
      <rect x="40" y="20" width="80" height="58" rx="8" />
      <path d="M52 68h56M57 31h46" />
      <circle cx="80" cy="86" r="2" />
    </svg>
  );
}

function formatPrice(value) {
  return new Intl.NumberFormat('en-BD', {
    style: 'currency',
    currency: 'BDT',
    maximumFractionDigits: 0,
  }).format(value);
}

function ProductCard({ product, isCompared, isSaved, onCompare, onSave }) {
  const image = product.image_url || product.image_link;
  const discount = product.original_price > product.price
    ? Math.round((1 - product.price / product.original_price) * 100)
    : null;

  return (
    <article className="product-card">
      <div className={`product-visual product-visual-${(product.category || 'default').toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}>
        {image ? (
          <img src={image} alt={product.name} loading="lazy" />
        ) : (
          <ProductArtwork product={product} />
        )}
        {discount && <span className="discount-badge">-{discount}%</span>}
        <span className={`stock-badge${product.in_stock === false ? ' out-of-stock' : ''}`}>
          {product.in_stock === false ? 'Out of stock' : 'In stock'}
        </span>
      </div>
      <div className="product-details">
        <p className="product-category">{product.brand} · {product.category}</p>
        <h2 title={product.name}>{product.name}</h2>
        <div className="product-prices">
          <span className="current-price">{formatPrice(product.price)}</span>
          {product.original_price > product.price && (
            <span className="original-price">{formatPrice(product.original_price)}</span>
          )}
        </div>
        <p className="product-rating">
          <span aria-label={`${product.rating} out of 5 stars`}>★</span>
          {Number(product.rating || 0).toFixed(1)}
        </p>
        <div className="marketplace-row">
          <p className="marketplace-name">{product.marketplace_name}</p>
          {product.is_verified && (
            <span className="verified-badge" aria-label="Verified seller">
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="m12 2 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 2Z" />
              </svg>
              Verified
            </span>
          )}
        </div>
        <div className="product-actions">
          <button
            className={isCompared ? 'selected' : ''}
            type="button"
            aria-pressed={isCompared}
            onClick={onCompare}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M7 7h13m0 0-4-4m4 4-4 4M17 17H4m0 0 4 4m-4-4 4-4" />
            </svg>
            {isCompared ? 'Added' : 'Compare'}
          </button>
          <button
            className={isSaved ? 'selected' : ''}
            type="button"
            aria-pressed={isSaved}
            onClick={onSave}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1-4.4-4.3 6.1-.9L12 3Z" />
            </svg>
            {isSaved ? 'Saved' : 'Save'}
          </button>
        </div>
        {product.product_link && (
          <a className="product-link" href={product.product_link} target="_blank" rel="noreferrer">
            View seller offer
          </a>
        )}
      </div>
    </article>
  );
}

export default ProductCard;
