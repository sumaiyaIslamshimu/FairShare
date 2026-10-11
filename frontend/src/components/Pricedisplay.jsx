const SIZE_CLASSES = {
  xl: "text-xl",
  lg: "text-lg",
  base: "",
};

function money(amount) {
  return `৳${Number(amount).toLocaleString()}`;
}

// With no active discount this renders the same bold price as before.
// `discount` comes from GET /promotions/active.
export default function Pricedisplay({ price, discount, size = "xl" }) {
  const sizeClass = SIZE_CLASSES[size] || "";

  if (!discount) {
    return (
      <p className={`font-bold ${sizeClass} text-gray-900`}>{money(price)}</p>
    );
  }

  const percent = Math.round(discount.percentage * 100) / 100;

  return (
    <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
      <p className={`font-bold ${sizeClass} text-gray-900`}>
        {money(discount.discounted_price)}
      </p>
      <p className="text-sm text-gray-400 line-through">{money(price)}</p>
      <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full whitespace-nowrap">
        -{percent}%
      </span>
    </div>
  );
}