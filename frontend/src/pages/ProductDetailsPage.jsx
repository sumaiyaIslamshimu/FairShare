import { Link } from "react-router-dom";
import RecommendationsSection from "../components/RecommendationsSection";
const MOCK_PRODUCT = {
  name: "Apple iPhone 15",
  brand: "Apple",
  category: "Smartphone",
  image_url:
    "https://placehold.co/600x450/f3f4f6/a1a1aa?text=Apple+iPhone+15",
};

const MOCK_SELLERS = [
  {
    name: "Daraz",
    price: 134999,
    availability: "In stock",
    verified: false,
  },
  {
    name: "Pickaboo",
    price: 137500,
    availability: "In stock",
    verified: false,
  },
  {
    name: "Verified Seller / Our Page",
    price: 133999,
    availability: "In stock",
    verified: true,
  },
];

export default function ProductDetailsPage() {
    const product = MOCK_PRODUCT;

  const storedBudget = sessionStorage.getItem("fairshare_budget");
  const budget = storedBudget ? Number(storedBudget) : null;

  const currentPrice = Math.min(
    ...MOCK_SELLERS.map((seller) => seller.price)
  );

  return (
    <div className="min-h-screen bg-white">
      {/* FairShare Navbar */}
      <nav className="flex items-center justify-between px-8 py-4 border-b border-gray-200 bg-white">
        <Link to="/" className="flex items-center gap-2 no-underline">
          <span className="w-7 h-7 rounded-lg bg-slate-900 flex items-center justify-center text-sm">
            🛍️
          </span>

          <span className="text-lg font-bold text-slate-900">
            FairShare
          </span>
        </Link>
      </nav>

      <div className="p-6 max-w-5xl mx-auto">
        {/* Back to Results */}
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 mb-6"
        >
          ← Back to results
        </Link>

        {/* Product Header */}
        <div className="flex flex-col md:flex-row gap-6 bg-white border border-gray-200 rounded-lg shadow-sm p-6 mb-8">
          <div className="w-full md:w-64 h-64 flex-shrink-0 bg-gray-100 rounded-lg overflow-hidden">
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          </div>

          <div className="flex flex-col justify-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              {product.name}
            </h1>

            <p className="text-sm text-gray-500 mb-1">
              Brand:{" "}
              <span className="text-gray-900 font-medium">
                {product.brand}
              </span>
            </p>

            <p className="text-sm text-gray-500">
              Category:{" "}
              <span className="text-gray-900 font-medium">
                {product.category}
              </span>
            </p>
          </div>
        </div>

        {/* Seller Comparison Section */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Compare Sellers
          </h2>

          {/* Desktop Seller Table */}
          <div className="hidden md:block border border-gray-200 rounded-lg overflow-hidden">
            <div className="grid grid-cols-5 bg-gray-50 text-xs font-semibold text-gray-500 uppercase px-4 py-3">
              <span className="col-span-2">Seller</span>
              <span>Price</span>
              <span>Availability</span>
              <span className="text-right">Action</span>
            </div>

            {MOCK_SELLERS.map((seller) => (
              <div
                key={seller.name}
                className="grid grid-cols-5 items-center px-4 py-4 border-t border-gray-100"
              >
                <div className="col-span-2 flex items-center gap-2">
                  <span className="font-medium text-gray-900">
                    {seller.name}
                  </span>

                  {seller.verified && (
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full whitespace-nowrap">
                      Verified
                    </span>
                  )}
                </div>

                <span className="font-bold text-gray-900">
                  ৳{seller.price.toLocaleString()}
                </span>

                <span className="text-sm text-gray-600">
                  {seller.availability}
                </span>

                <div className="text-right">
                  <button className="px-4 py-2 rounded font-medium text-sm bg-gray-900 text-white hover:bg-gray-800">
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Mobile Seller Cards */}
          <div className="md:hidden space-y-4">
            {MOCK_SELLERS.map((seller) => (
              <div
                key={seller.name}
                className="border border-gray-200 rounded-lg shadow-sm bg-white p-4"
              >
                <div className="flex justify-between items-start mb-3">
                  <span className="font-medium text-gray-900">
                    {seller.name}
                  </span>

                  {seller.verified && (
                    <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full whitespace-nowrap">
                      Verified
                    </span>
                  )}
                </div>

                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">
                      Price
                    </p>

                    <p className="font-bold text-lg text-gray-900">
                      ৳{seller.price.toLocaleString()}
                    </p>

                    <p className="text-xs text-gray-500 mt-1">
                      {seller.availability}
                    </p>
                  </div>

                  <button className="px-4 py-2 rounded font-medium text-sm bg-gray-900 text-white hover:bg-gray-800">
                    View
                  </button>
                </div>
              </div>
            ))}
          </div>

        </div>
          <RecommendationsSection
          productId={product._id || "mock-product"}
          budget={budget}
          currentPrice={currentPrice}
        />
      </div>
    </div>
  );
}