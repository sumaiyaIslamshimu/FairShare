import { useState } from "react";
import { createProduct, deleteProduct, getMyProducts, updateInventory, updateProduct } from "../../api/seller.js";
import { getCategories } from "../../api/shopping.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import DataTable from "../../components/DataTable.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import Modal from "../../components/Modal.jsx";
import Pagination from "../../components/Pagination.jsx";
import useLoad from "../../hooks/useLoad.js";
import { formatPrice } from "../../utils/format.js";

const PAGE_SIZE = 20;
const EMPTY = {
  title: "", description: "", brand: "", category_slug: "", subcategory_slug: "",
  price: "", stock_qty: "0", image: "", quantity: "", unit: "", status: "active", attrs: [],
};

// Taka (as typed) -> integer paisa. Avoids float drift: "199.99" -> 19999.
const toPaisa = (text) => Math.round(Number(text) * 100);

function toForm(p) {
  return {
    title: p.title, description: p.description || "", brand: p.brand || "",
    category_slug: p.category_slug, subcategory_slug: p.subcategory_slug,
    price: String(p.price_paisa / 100), stock_qty: String(p.stock_qty),
    image: (p.images || [])[0] || "", quantity: p.quantity ?? "", unit: p.unit || "", status: p.status,
    attrs: Object.entries(p.attributes || {}).map(([k, v]) => ({ k, v: String(v) })),
  };
}

// Rows with a blank name are dropped; a repeated name keeps the last value.
const attrsToObject = (rows) =>
  Object.fromEntries(rows.filter((r) => r.k.trim()).map((r) => [r.k.trim(), r.v.trim()]));

function toPayload(f) {
  const hasSize = f.quantity !== "" && f.unit !== "";
  return {
    title: f.title.trim(),
    description: f.description.trim(),
    brand: f.brand.trim() || null,
    category_slug: f.category_slug,
    subcategory_slug: f.subcategory_slug,
    price_paisa: toPaisa(f.price),
    stock_qty: parseInt(f.stock_qty, 10),
    images: f.image.trim() ? [f.image.trim()] : [],
    quantity: hasSize ? Number(f.quantity) : null,
    unit: hasSize ? f.unit : null,
    attributes: attrsToObject(f.attrs),
    status: f.status,
  };
}

export default function Products() {
  const [page, setPage] = useState(1);
  const list = useLoad(() => getMyProducts(page), [page]);
  const cats = useLoad(getCategories);
  const [editing, setEditing] = useState(null); // null = closed, "new" or a product
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [busy, setBusy] = useState(false);

  const subs = (cats.data || []).find((c) => c.slug === form.category_slug)?.subcategories || [];

  const openNew = () => { setForm(EMPTY); setFormError(null); setEditing("new"); };
  const openEdit = (p) => { setForm(toForm(p)); setFormError(null); setEditing(p); };

  const save = async (e) => {
    e.preventDefault();
    setFormError(null);
    if (!(Number(form.price) > 0)) return setFormError("Enter a price above 0.");
    if ((form.quantity === "") !== (form.unit === "")) return setFormError("Give both the pack size and its unit, or neither.");
    setBusy(true);
    try {
      const payload = toPayload(form);
      if (editing === "new") await createProduct(payload);
      else await updateProduct(editing.id, payload);
      setEditing(null);
      list.reload();
    } catch (err) {
      setFormError(err);
    } finally {
      setBusy(false);
    }
  };

  const act = async (fn) => {
    setActionError(null);
    try {
      await fn();
      list.reload();
    } catch (err) {
      setActionError(err);
    }
  };

  const setStock = (p) => {
    const answer = window.prompt(`New stock for "${p.title}"`, String(p.stock_qty));
    if (answer === null) return;
    const qty = parseInt(answer, 10);
    if (Number.isNaN(qty) || qty < 0) return setActionError(new Error("Stock must be a whole number, 0 or more."));
    act(() => updateInventory(p.id, qty));
  };

  const columns = [
    { key: "title", header: "Product", render: (p) => <>{p.title}<br /><small className="muted">{p.category_slug} / {p.subcategory_slug}</small></> },
    { key: "price_paisa", header: "Price", render: (p) => formatPrice(p.price_paisa, p.currency || "BDT") },
    { key: "stock_qty", header: "Stock", render: (p) => (p.stock_qty === 0 ? <Badge tone="red">out of stock</Badge> : p.stock_qty) },
    { key: "status", header: "Listing", render: (p) => <Badge tone={p.status === "active" ? "green" : "neutral"}>{p.status}</Badge> },
    {
      key: "moderation_status", header: "Admin",
      render: (p) => (p.moderation_status === "visible" ? <Badge tone="green">visible</Badge> : <Badge tone="red">{p.moderation_status} by admin</Badge>),
    },
    {
      key: "actions", header: "",
      render: (p) => (
        <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
          <Button onClick={() => openEdit(p)}>Edit</Button>
          <Button onClick={() => setStock(p)}>Stock</Button>
          <Button onClick={() => window.confirm(`Delete "${p.title}"?`) && act(() => deleteProduct(p.id))}>Delete</Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>My products</h1>
        <Button variant="primary" onClick={openNew}>Add product</Button>
      </div>
      <p className="subtitle">These are your FairShare listings. Only approved sellers can add or change products. Prices are in Taka.</p>
      <ErrorBox error={actionError || list.error || cats.error} />
      <Card>
        {list.loading && !list.data ? <Loading /> : (
          <>
            <DataTable columns={columns} rows={list.data?.items} emptyText="You have no products yet." />
            <Pagination page={page} pageSize={PAGE_SIZE} total={list.data?.total || 0} onChange={setPage} />
          </>
        )}
      </Card>

      <Modal title={editing === "new" ? "Add product" : "Edit product"} open={!!editing} onClose={() => setEditing(null)}>
        <form onSubmit={save}>
          <ErrorBox error={formError} />
          <FormField label="Title" id="p-title" required minLength={2} maxLength={150} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <FormField label="Brand (optional)" id="p-brand" maxLength={80} value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} />
          <FormField label="Category" id="p-cat">
            <select id="p-cat" className="input" required value={form.category_slug} onChange={(e) => setForm({ ...form, category_slug: e.target.value, subcategory_slug: "" })}>
              <option value="">Choose…</option>
              {(cats.data || []).map((c) => <option key={c.slug} value={c.slug}>{c.name}</option>)}
            </select>
          </FormField>
          <FormField label="Subcategory" id="p-sub">
            <select id="p-sub" className="input" required value={form.subcategory_slug} onChange={(e) => setForm({ ...form, subcategory_slug: e.target.value })}>
              <option value="">Choose…</option>
              {subs.map((s) => <option key={s.slug} value={s.slug}>{s.name}</option>)}
            </select>
          </FormField>
          <FormField label="Price (Taka)" id="p-price" type="number" min="0.01" step="0.01" required value={form.price} onChange={(e) => setForm({ ...form, price: e.target.value })} />
          <FormField label="Stock" id="p-stock" type="number" min="0" step="1" required value={form.stock_qty} onChange={(e) => setForm({ ...form, stock_qty: e.target.value })} />
          <div style={{ display: "flex", gap: 8 }}>
            <FormField label="Pack size (optional)" id="p-qty" type="number" min="0" step="any" value={form.quantity} onChange={(e) => setForm({ ...form, quantity: e.target.value })} />
            <FormField label="Unit" id="p-unit">
              <select id="p-unit" className="input" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })}>
                <option value="">—</option>
                <option value="g">g</option>
                <option value="ml">ml</option>
                <option value="pcs">pcs</option>
                <option value="pack">pack</option>
              </select>
            </FormField>
          </div>
          <FormField label="Image link (http/https, optional)" id="p-img" type="url" maxLength={500} value={form.image} onChange={(e) => setForm({ ...form, image: e.target.value })} />
          <FormField label="Description" id="p-desc">
            <textarea id="p-desc" className="input" rows={3} maxLength={2000} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </FormField>
          <fieldset style={{ border: "none", padding: 0, margin: "0 0 12px" }}>
            <legend>Extra details (optional, e.g. Colour: Red)</legend>
            {form.attrs.map((row, i) => (
              <div key={i} style={{ display: "flex", gap: 6, marginBottom: 6 }}>
                <input className="input" aria-label={`Detail name ${i + 1}`} maxLength={100} placeholder="Name" value={row.k}
                       onChange={(e) => setForm({ ...form, attrs: form.attrs.map((r, j) => (j === i ? { ...r, k: e.target.value } : r)) })} />
                <input className="input" aria-label={`Detail value ${i + 1}`} maxLength={100} placeholder="Value" value={row.v}
                       onChange={(e) => setForm({ ...form, attrs: form.attrs.map((r, j) => (j === i ? { ...r, v: e.target.value } : r)) })} />
                <Button type="button" aria-label={`Remove detail ${i + 1}`} onClick={() => setForm({ ...form, attrs: form.attrs.filter((_, j) => j !== i) })}>×</Button>
              </div>
            ))}
            {form.attrs.length < 20 && (
              <Button type="button" onClick={() => setForm({ ...form, attrs: [...form.attrs, { k: "", v: "" }] })}>Add detail</Button>
            )}
          </fieldset>
          <FormField label="Listing" id="p-status">
            <select id="p-status" className="input" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
              <option value="active">Active (shoppers can buy)</option>
              <option value="inactive">Inactive (hidden from shop)</option>
            </select>
          </FormField>
          <Button variant="primary" type="submit" disabled={busy}>{busy ? "Saving…" : "Save product"}</Button>
        </form>
      </Modal>
    </>
  );
}