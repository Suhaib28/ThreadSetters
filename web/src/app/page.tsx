"use client";
import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL!;

type RecItem = {
  item_id: string;
  score: number;
  brand: string;
  title: string;
  category: string;
  image_url: string;
  current_price: number;
};

export default function Home() {
  const [itemId, setItemId] = useState("");
  const [similar, setSimilar] = useState<RecItem[]>([]);
  const [complete, setComplete] = useState<RecItem[]>([]);
  const [targetCat, setTargetCat] = useState("shoes");

  const fetchSimilar = async () => {
    if (!itemId) return;
    const res = await fetch(`${API}/recommend/similar?item_id=${encodeURIComponent(itemId)}&k=10`);
    setSimilar(await res.json());
  };

  const fetchComplete = async () => {
    if (!itemId) return;
    const res = await fetch(
      `${API}/recommend/complete-look?seed_item_id=${encodeURIComponent(itemId)}&target_category=${targetCat}&k=10`
    );
    setComplete(await res.json());
  };

  return (
    <main style={{ padding: 24, maxWidth: 1100, margin: "0 auto", fontFamily: "ui-sans-serif, system-ui" }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 16 }}>Clozyt Recommender Demo</h1>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "1fr auto auto" }}>
        <input
          placeholder="Paste an item_id from data/catalog.csv"
          value={itemId}
          onChange={(e) => setItemId(e.target.value)}
          style={{ padding: 10, border: "1px solid #ccc", borderRadius: 8 }}
        />
        <button onClick={fetchSimilar} style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid #ddd" }}>
          Similar
        </button>
        <div>
          <select
            value={targetCat}
            onChange={(e) => setTargetCat(e.target.value)}
            style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid #ddd", marginRight: 8 }}
          >
            <option value="shoes">shoes</option>
            <option value="bottoms">bottoms</option>
            <option value="outerwear">outerwear</option>
            <option value="tops">tops</option>
            <option value="dress">dress</option>
            <option value="accessories">accessories</option>
          </select>
          <button onClick={fetchComplete} style={{ padding: "10px 14px", borderRadius: 8, border: "1px solid #ddd" }}>
            Complete the Look
          </button>
        </div>
      </div>

      <Section title="Similar Items" items={similar} />
      <Section title={`Complete the Look → ${targetCat}`} items={complete} />
    </main>
  );
}

function Section({ title, items }: { title: string; items: RecItem[] }) {
  return (
    <section style={{ marginTop: 24 }}>
      <h2 style={{ fontSize: 22, fontWeight: 600, marginBottom: 12 }}>{title}</h2>
      {!items?.length ? <p style={{ color: "#666" }}>No results yet.</p> : null}
      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))" }}>
        {items?.map((it) => (
          <Card key={it.item_id} item={it} />
        ))}
      </div>
    </section>
  );
}

function Card({ item }: { item: RecItem }) {
  return (
    <div style={{ border: "1px solid #eee", borderRadius: 12, overflow: "hidden" }}>
      <div style={{ aspectRatio: "4 / 5", background: "#f7f7f7" }}>
        {item.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={item.image_url} alt={item.title} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
        ) : null}
      </div>
      <div style={{ padding: 10 }}>
        <div style={{ fontSize: 12, color: "#666" }}>{item.brand}</div>
        <div style={{ fontSize: 14, fontWeight: 600, marginTop: 2 }}>{item.title}</div>
        <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>{item.category}</div>
        <div style={{ fontSize: 14, marginTop: 6 }}>${Number(item.current_price || 0).toFixed(2)}</div>
      </div>
    </div>
  );
}

