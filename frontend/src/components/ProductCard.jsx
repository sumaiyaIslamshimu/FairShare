import { Link } from "react-router-dom";

// Your custom sample photos for each category
const categoryImages = {
  Fashion:
    "https://static.vecteezy.com/system/resources/thumbnails/086/444/130/small/tshirt-with-discount-tag-cartoon-vector.jpg",
  Electronics:
    "https://static.vecteezy.com/system/resources/previews/077/136/847/non_2x/electronic-devices-collection-featuring-a-laptop-headphones-smartphone-tablet-smartwatch-and-computer-mouse-vector.jpg",
  Household:
    "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR24OnABBE51EB9X9UpTLh6ipJXl3DxJ-fX8-fWWLHbXQ&s=10",
  Groceries:
    "https://thumbs.dreamstime.com/b/shopping-cart-filled-groceries-essentials-460220048.jpg",
};

export default function ProductCard({ product }) {
  // 1. Try DB image
  // 2. Try Category sample photo
  // 3. Fallback to generic placeholder
  const imageUrl =
    product.image_url ||
    categoryImages[product.category] ||
    `https://placehold.co/400x300/f3f4f6/a1a1aa?text=${product.category}`;

  const cardContent = (
    <>
      {/* Product Image Section */}
      <div className="h-48 w-full bg-gray-100 border-b border-gray-100 relative">
        <img
          src={imageUrl}
          alt={product.name}
          className="w-full h-full object-cover"
        />
      </div>

      {/* Product Details Section */}
      <div className="p-4 flex flex-col flex-1">
        <div className="flex justify-between items-start mb-2">
          <h3 className="font-semibold text-lg text-gray-900 line-clamp-2">
            {product.name}
          </h3>

          {product.is_verified && (
            <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full whitespace-nowrap ml-2">
              Verified
            </span>
          )}
        </div>

        <p className="text-sm text-gray-500 mb-3">
          {product.brand} • {product.category}
        </p>

        <div className="flex items-center gap-2 mb-3">
          <span className="text-yellow-500">★</span>
          <span className="text-sm font-medium">{product.rating}</span>
          <span className="text-sm text-gray-400">
            | {product.marketplace_name}
          </span>
        </div>

        <div className="mt-auto flex justify-between items-end pt-4 border-t border-gray-100">
          <div>
            <p className="text-xs text-gray-500 mb-1">Price</p>
            <p className="font-bold text-xl text-gray-900">
              ৳{product.price.toLocaleString()}
            </p>
          </div>

          <span
            className={`px-4 py-2 rounded font-medium text-sm ${
              product.in_stock
                ? "bg-gray-900 text-white hover:bg-gray-800"
                : "bg-gray-200 text-gray-500 cursor-not-allowed"
            }`}
          >
            {product.in_stock ? "View Deal" : "Out of Stock"}
          </span>
        </div>
      </div>
    </>
  );

  // In-stock products are clickable
  if (product.in_stock) {
    return (
      <Link
        to={`/product/${product._id}`}
        className="border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition bg-white flex flex-col h-full overflow-hidden"
      >
        {cardContent}
      </Link>
    );
  }

  // Out-of-stock products are not clickable
  return (
    <div className="border border-gray-200 rounded-lg shadow-sm bg-white flex flex-col h-full overflow-hidden">
      {cardContent}
    </div>
  );
}