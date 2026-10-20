export default function CategoryFilter({ categories, category, subcategory, onChange }) {
  const current = categories.find((c) => c.slug === category);
  return (
    <>
      <select className="input" aria-label="Category" value={category}
        onChange={(e) => onChange({ category: e.target.value, subcategory: "" })}>
        <option value="">All categories</option>
        {categories.map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
      </select>
      <select className="input" aria-label="Subcategory" value={subcategory} disabled={!current}
        onChange={(e) => onChange({ category, subcategory: e.target.value })}>
        <option value="">All subcategories</option>
        {(current?.subcategories || []).map((s) => <option key={s.slug} value={s.slug}>{s.name}</option>)}
      </select>
    </>
  );
}