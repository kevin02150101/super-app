// History page
const { useEffect, useState, useCallback } = React;

function BookModal({ book, onClose }) {
  if (!book) return null;
  return (
    <>
      <div className="modal fade show d-block" tabIndex="-1" role="dialog" onClick={onClose}>
        <div
          className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">{book.title}</h5>
              <button type="button" className="btn-close" aria-label="Close" onClick={onClose} />
            </div>
            <div className="modal-body">
              <div className="row g-3">
                <div className="col-12 col-md-4 text-center">
                  {book.image_url ? (
                    <img src={book.image_url} alt={book.title}
                         className="img-fluid rounded shadow-sm"
                         style={{ maxHeight: "16rem" }} />
                  ) : (
                    <div className="text-muted small">No cover</div>
                  )}
                  <div className="mt-3">
                    <span className="badge bg-danger fs-6">
                      {book.price != null ? `NT$ ${book.price}` : "—"}
                    </span>
                  </div>
                </div>
                <div className="col-12 col-md-8">
                  {book.category && (
                    <span className="badge text-bg-info mb-2">{book.category}</span>
                  )}
                  {book.authors && (<p className="mb-1"><strong>Author:</strong>{book.authors}</p>)}
                  {book.publisher && (<p className="mb-1"><strong>Publish:</strong>{book.publisher}</p>)}
                  {book.published_at && (
                    <p className="mb-1"><strong>Publish date:</strong>{book.published_at}</p>
                  )}
                  {book.summary ? (
                    <div className="alert alert-light border mt-3 mb-3">
                      <div className="fw-semibold text-primary mb-1">📖 Summary</div>
                      <div className="small">{book.summary}</div>
                    </div>
                  ) : (
                    <div className="text-muted small mt-3">No summary yet</div>
                  )}
                </div>
              </div>
              {book.description && (
                <div className="mt-3">
                  <h6 className="text-secondary">Full synopsis</h6>
                  <div className="book-description border rounded p-3 bg-light">
                    {book.description}
                  </div>
                </div>
              )}
            </div>
            <div className="modal-footer">
              {book.product_url && (
                <a href={book.product_url} target="_blank" rel="noopener noreferrer"
                   className="btn btn-primary">Open on Books.com.tw</a>
              )}
              <button type="button" className="btn btn-secondary" onClick={onClose}>Close</button>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop fade show" />
    </>
  );
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d)) return iso;
  return d.toLocaleString("zh-TW", { hour12: false });
}

function HistoryList({ items, onSelect, onDelete, selectedId }) {
  if (!items.length) {
    return <div className="alert alert-info">No records yet.</div>;
  }
  return (
    <div className="list-group shadow-sm">
      {items.map((q) => (
        <div
          key={q.id}
          className={
            "list-group-item list-group-item-action d-flex justify-content-between align-items-center" +
            (selectedId === q.id ? " active" : "")
          }
          role="button"
          onClick={() => onSelect(q.id)}
        >
          <div className="me-2">
            <div className="fw-semibold d-flex align-items-center gap-2 flex-wrap">
              <span>{q.keyword}</span>
              {q.primary_category && (
                <span className={
                  "badge " + (selectedId === q.id ? "text-bg-light" : "text-bg-info")
                }>
                  {q.primary_category}
                </span>
              )}
            </div>
            <small className={selectedId === q.id ? "text-white-50" : "text-muted"}>
              {fmtDate(q.created_at)} · {q.result_count} records · {q.duration_ms}ms
            </small>
          </div>
          <button
            className="btn btn-sm btn-outline-danger"
            onClick={(e) => {
              e.stopPropagation();
              if (confirm(`Delete "${q.keyword}」this record?`)) onDelete(q.id);
            }}
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}

function ResultPanel({ detail, loading, onOpen }) {
  if (loading) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" />
      </div>
    );
  }
  if (!detail) {
    return <div className="text-muted text-center py-5">Pick a record on the left to view its results</div>;
  }
  const { query, results } = detail;
  // group by category
  const grouped = results.reduce((acc, b) => {
    const c = b.category || "Other";
    (acc[c] = acc[c] || []).push(b);
    return acc;
  }, {});
  const cats = Object.keys(grouped);

  return (
    <div>
      <h5 className="mb-2 d-flex align-items-center flex-wrap gap-2">
        <span>「{query.keyword}」</span>
        {query.primary_category && (
          <span className="badge text-bg-primary">{query.primary_category}</span>
        )}
        <small className="text-muted ms-auto">{fmtDate(query.created_at)}</small>
      </h5>
      {query.summary_text && (
        <div className="alert alert-light border small mb-3">
          📋 {query.summary_text}
        </div>
      )}
      {results.length === 0 ? (
        <div className="alert alert-warning">This search returned no results.</div>
      ) : (
        cats.map((cat) => (
          <section key={cat} className="mb-4">
            <h6 className="border-start border-4 border-primary ps-2 mb-3">
              {cat} <small className="text-muted">({grouped[cat].length})</small>
            </h6>
            <div className="row g-3">
              {grouped[cat].map((b) => (
                <div key={b.id} className="col-12 col-md-6 col-lg-4">
                  <div
                    className="card book-card shadow-sm border-0 h-100"
                    role="button"
                    style={{ cursor: "pointer" }}
                    onClick={() => onOpen(b)}
                  >
                    {b.image_url && (
                      <img className="card-img-top book-cover" src={b.image_url} alt={b.title}
                           loading="lazy"
                           onError={(e) => (e.currentTarget.style.display = "none")} />
                    )}
                    <div className="card-body d-flex flex-column">
                      {b.category && (
                        <span className="badge text-bg-info align-self-start mb-2">
                          {b.category}
                        </span>
                      )}
                      <h6 className="card-title">{b.title}</h6>
                      {b.authors && <p className="small text-muted mb-1">Author:{b.authors}</p>}
                      {b.publisher && <p className="small text-muted mb-1">Publish:{b.publisher}</p>}
                      {b.summary && (
                        <p className="small text-secondary mb-2 book-summary">📖 {b.summary}</p>
                      )}
                      <div className="mt-auto d-flex justify-content-between align-items-center pt-2">
                        <span className="badge bg-danger fs-6">
                          {b.price != null ? `NT$ ${b.price}` : "—"}
                        </span>
                        <span className="btn btn-sm btn-outline-primary">View summary</span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

function App() {
  const [items, setItems] = useState([]);
  const [keyword, setKeyword] = useState("");
  const [category, setCategory] = useState("");
  const [categories, setCategories] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);

  const loadList = useCallback(async (kw, cat) => {
    setLoadingList(true);
    try {
      const params = {};
      if (kw) params.keyword = kw;
      if (cat) params.category = cat;
      const resp = await window.apiClient.get("/search-records", { params });
      setItems(resp.data || []);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoadingList(false);
    }
  }, []);

  const loadCategories = useCallback(async () => {
    try {
      const resp = await window.apiClient.get("/search-records/categories");
      setCategories(resp.data || []);
    } catch (e) {
      console.warn(e.message);
    }
  }, []);

  const loadDetail = useCallback(async (id) => {
    setSelectedId(id);
    setLoadingDetail(true);
    setDetail(null);
    try {
      const resp = await window.apiClient.get(`/search-records/${id}`);
      setDetail(resp.data);
    } catch (e) {
      alert(e.message);
    } finally {
      setLoadingDetail(false);
    }
  }, []);

  const remove = useCallback(async (id) => {
    try {
      await window.apiClient.delete(`/search-records/${id}`);
      setItems((prev) => prev.filter((x) => x.id !== id));
      if (selectedId === id) {
        setSelectedId(null);
        setDetail(null);
      }
    } catch (e) {
      alert(e.message);
    }
  }, [selectedId]);

  useEffect(() => { loadList("", ""); loadCategories(); }, [loadList, loadCategories]);

  return (
    <div className="row g-4">
      <div className="col-12 col-lg-5">
        <form className="mb-3 d-flex gap-2 flex-wrap"
              onSubmit={(e) => { e.preventDefault(); loadList(keyword.trim(), category); }}>
          <input className="form-control" style={{ minWidth: "10rem", flex: "1 1 12rem" }}
                 placeholder="Filter keywords…"
                 value={keyword} onChange={(e) => setKeyword(e.target.value)} />
          <select className="form-select" style={{ flex: "0 1 9rem" }}
                  value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <button className="btn btn-primary" type="submit">Filter</button>
          {(keyword || category) && (
            <button type="button" className="btn btn-outline-secondary"
                    onClick={() => { setKeyword(""); setCategory(""); loadList("", ""); }}>
              Clear
            </button>
          )}
        </form>
        {loadingList ? (
          <div className="text-center py-4"><div className="spinner-border text-primary" /></div>
        ) : (
          <HistoryList items={items} onSelect={loadDetail} onDelete={remove} selectedId={selectedId} />
        )}
      </div>
      <div className="col-12 col-lg-7">
        <div className="card shadow-sm border-0 p-4">
          <ResultPanel detail={detail} loading={loadingDetail} onOpen={setSelectedBook} />
        </div>
      </div>
      <BookModal book={selectedBook} onClose={() => setSelectedBook(null)} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root-history")).render(<App />);
