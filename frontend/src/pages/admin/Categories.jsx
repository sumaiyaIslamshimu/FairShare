import { useState } from "react";
import {
  createCategory, createSubcategory, deleteCategory, deleteSubcategory, listTaxonomy, updateCategory, updateSubcategory,
} from "../../api/admin.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ErrorBox from "../../components/ErrorBox.jsx";
import FormField from "../../components/FormField.jsx";
import Loading from "../../components/Loading.jsx";
import useLoad from "../../hooks/useLoad.js";

const slugify = (text) => text.toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

export default function Categories() {
  const { data: tree, error, loading, reload } = useLoad(listTaxonomy);
  const [actionError, setActionError] = useState(null);
  const [catName, setCatName] = useState("");
  const [subName, setSubName] = useState({});

  const act = async (fn) => {
    setActionError(null);
    try {
      await fn();
      await reload();
    } catch (e) {
      setActionError(e); // e.g. "Listings still use this category" (409)
    }
  };

  if (loading && !tree) return <Loading />;
  return (
    <>
      <h1>Categories</h1>
      <p className="subtitle">
        A category or subcategory that listings still use cannot be deleted or deactivated. Sellers and shoppers see changes immediately.
      </p>
      <ErrorBox error={actionError || error} />

      <Card>
        <h2>Add a category</h2>
        <form
          style={{ display: "flex", gap: 8 }}
          onSubmit={(e) => {
            e.preventDefault();
            act(async () => {
              await createCategory({ slug: slugify(catName), name: catName.trim() });
              setCatName("");
            });
          }}
        >
          <FormField label="Name" id="new-cat" value={catName} onChange={(e) => setCatName(e.target.value)} required minLength={2} />
          <Button variant="primary" type="submit" style={{ alignSelf: "end" }}>Add</Button>
        </form>
      </Card>

      {(tree || []).map((c) => (
        <Card key={c.slug} style={{ marginTop: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
            <h2>
              {c.name} <Badge tone={c.is_active ? "green" : "red"}>{c.is_active ? "active" : "inactive"}</Badge>{" "}
              <small className="muted">{c.in_use} in use</small>
            </h2>
            <div style={{ display: "flex", gap: 6 }}>
              <Button onClick={() => act(() => updateCategory(c.slug, { is_active: !c.is_active }))}>{c.is_active ? "Deactivate" : "Activate"}</Button>
              <Button onClick={() => window.confirm(`Delete ${c.name}?`) && act(() => deleteCategory(c.slug))}>Delete</Button>
            </div>
          </div>
          <ul>
            {c.subcategories.map((s) => (
              <li key={s.slug} style={{ display: "flex", gap: 8, alignItems: "center", margin: "4px 0" }}>
                <span>{s.name}</span>
                <Badge tone={s.is_active ? "green" : "red"}>{s.is_active ? "active" : "inactive"}</Badge>
                <small className="muted">{s.in_use} in use</small>
                <Button onClick={() => act(() => updateSubcategory(s.slug, { is_active: !s.is_active }))}>{s.is_active ? "Deactivate" : "Activate"}</Button>
                <Button onClick={() => window.confirm(`Delete ${s.name}?`) && act(() => deleteSubcategory(s.slug))}>Delete</Button>
              </li>
            ))}
          </ul>
          <form
            style={{ display: "flex", gap: 8 }}
            onSubmit={(e) => {
              e.preventDefault();
              const name = (subName[c.slug] || "").trim();
              act(async () => {
                await createSubcategory({ slug: slugify(name), category_slug: c.slug, name });
                setSubName({ ...subName, [c.slug]: "" });
              });
            }}
          >
            <input className="input" placeholder="New subcategory name" aria-label={`New subcategory in ${c.name}`} minLength={2} required
                   value={subName[c.slug] || ""} onChange={(e) => setSubName({ ...subName, [c.slug]: e.target.value })} />
            <Button type="submit">Add subcategory</Button>
          </form>
        </Card>
      ))}
    </>
  );
}