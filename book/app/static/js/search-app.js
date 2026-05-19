// Home: title search + card-style result rendering
const { useState, useCallback } = React;

async function searchWithRetry(keyword, retries = 2) {
  let attempt = 0;
  let lastErr;
  while (attempt <= retries) {
    try {
      return await window.apiClient.post("/books/search", { keyword });
    } catch (e) {
      const msg = String(e?.message || "");
      const transient = /\b(502|503|504)\b/.test(msg);
      lastErr = e;
      if (!transient || attempt === retries) break;
      const waitMs = 1200 * (attempt + 1);
      await new Promise((r) => setTimeout(r, waitMs));
      attempt += 1;
      continue;
    }
  }
  throw lastErr;
}

function SearchForm({ onSubmit, loading }) {
  const [keyword, setKeyword] = useState("");
  return (
    <form
      className="card shadow-sm border-0 p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (keyword.trim()) onSubmit(keyword.trim());
      }}
    >
      <label className="form-label fw-semibold">Enter a book title</label>
      <div className="input-group input-group-lg">
        <input
          type="text"
          className="form-control"
          placeholder="e.g.:Atomic Habits, JavaScript, Deep Learning…"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <button
          type="submit"
          className="btn btn-primary px-4"
          disabled={loading || !keyword.trim()}
        >
          {loading ? (
            <>
              <span className="spinner-border spinner-border-sm me-2" />
              Searching…
            </>
          ) : (
            "Search"
          )}
        </button>
      </div>
      <div className="form-text">
        Queries run via Playwright against Books.com.tw and usually take 5-15 seconds.
      </div>
    </form>
  );
}

function BookCard({ book, onOpen }) {
  return (
    <div className="col-12 col-sm-6 col-lg-4 col-xl-3">
      <div
        className="card book-card shadow-sm border-0 h-100"
        role="button"
        onClick={() => onOpen(book)}
        style={{ cursor: "pointer" }}
      >
        {book.image_url ? (
          <img
            className="card-img-top book-cover"
            src={book.image_url}
            alt={book.title}
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : (
          <div className="book-cover d-flex align-items-center justify-content-center text-muted">
            No cover
          </div>
        )}
        <div className="card-body d-flex flex-column">
          {book.category && (
            <span className="badge text-bg-info align-self-start mb-2">
              {book.category}
            </span>
          )}
          <h6 className="card-title">{book.title}</h6>
          {book.authors && (
            <p className="text-muted small mb-1">Author:{book.authors}</p>
          )}
          {book.publisher && (
            <p className="text-muted small mb-1">Publish:{book.publisher}</p>
          )}
          {book.summary && (
            <p className="small text-secondary mb-2 book-summary">
              📖 {book.summary}
            </p>
          )}
          <div className="mt-auto d-flex justify-content-between align-items-center pt-2">
            <span className="badge bg-danger fs-6">
              {book.price != null ? `NT$ ${book.price}` : "—"}
            </span>
            <span className="btn btn-sm btn-outline-primary">View summary</span>
          </div>
        </div>
      </div>
    </div>
  );
}

function BookModal({ book, onClose }) {
  if (!book) return null;
  return (
    <>
      <div
        className="modal fade show d-block"
        tabIndex="-1"
        role="dialog"
        onClick={onClose}
      >
        <div
          className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-content">
            <div className="modal-header">
              <h5 className="modal-title">{book.title}</h5>
              <button
                type="button"
                className="btn-close"
                aria-label="Close"
                onClick={onClose}
              />
            </div>
            <div className="modal-body">
              <div className="row g-3">
                <div className="col-12 col-md-4 text-center">
                  {book.image_url ? (
                    <img
                      src={book.image_url}
                      alt={book.title}
                      className="img-fluid rounded shadow-sm"
                      style={{ maxHeight: "16rem" }}
                    />
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
                    <span className="badge text-bg-info mb-2">
                      {book.category}
                    </span>
                  )}
                  {book.authors && (
                    <p className="mb-1">
                      <strong>Author:</strong>
                      {book.authors}
                    </p>
                  )}
                  {book.publisher && (
                    <p className="mb-1">
                      <strong>Publish:</strong>
                      {book.publisher}
                    </p>
                  )}
                  {book.published_at && (
                    <p className="mb-1">
                      <strong>Publish date:</strong>
                      {book.published_at}
                    </p>
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
                <a
                  href={book.product_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                >
                  Open on Books.com.tw
                </a>
              )}
              <button type="button" className="btn btn-secondary" onClick={onClose}>
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
      <div className="modal-backdrop fade show" />
    </>
  );
}

function ResultGrid({ data, onOpen }) {
  if (!data) return null;
  const { query, results, summary } = data;

  // Group by category
  const grouped = results.reduce((acc, b) => {
    const c = b.category || "Other";
    (acc[c] = acc[c] || []).push(b);
    return acc;
  }, {});
  const categoryOrder = (summary?.stats?.category_distribution || []).map(
    (x) => x.category
  );
  // Add categories missing from the distribution (rare)
  Object.keys(grouped).forEach((c) => {
    if (!categoryOrder.includes(c)) categoryOrder.push(c);
  });

  return (
    <div className="mt-4">
      <div className="d-flex justify-content-between align-items-end mb-3 flex-wrap gap-2">
        <div>
          <h4 className="mb-1">「{query.keyword}」 results</h4>
          <small className="text-muted">
            Total {query.result_count} results · took {query.duration_ms} ms · Source {query.source}
          </small>
        </div>
        {query.primary_category && (
          <span className="badge text-bg-primary fs-6">
            Main category:{query.primary_category}
          </span>
        )}
      </div>

      {summary && results.length > 0 && (
        <div className="card border-0 shadow-sm mb-4">
          <div className="card-body">
            <h6 className="card-title text-primary mb-2">📋 Search summary</h6>
            <p className="mb-3">{summary.text}</p>
            <div className="d-flex flex-wrap gap-2">
              {summary.stats.category_distribution.map((c) => (
                <span key={c.category} className="badge text-bg-light border">
                  {c.category} × {c.count}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {results.length === 0 ? (
        <div className="alert alert-warning">No related books found.</div>
      ) : (
        categoryOrder.map((cat) => (
          <section key={cat} className="mb-4">
            <h5 className="border-start border-4 border-primary ps-2 mb-3">
              {cat}{" "}
              <small className="text-muted fs-6">({grouped[cat].length})</small>
            </h5>
            <div className="row g-3">
              {grouped[cat].map((b, i) => (
                <BookCard key={b.id ?? `${cat}-${i}`} book={b} onOpen={onOpen} />
              ))}
            </div>
          </section>
        ))
      )}
    </div>
  );
}

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);

  const submit = useCallback(async (keyword) => {
    setLoading(true);
    setError("");
    setData(null);
    try {
      const resp = await searchWithRetry(keyword);
      setData(resp.data);
    } catch (e) {
      const msg = String(e?.message || "Request failed");
      if (/\b(502|503|504)\b/.test(msg)) {
        setError("Search service is waking up or temporarily unavailable. Please try again in 20-40 seconds.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div>
      <SearchForm onSubmit={submit} loading={loading} />
      {error && <div className="alert alert-danger mt-3">{error}</div>}
      <ResultGrid data={data} onOpen={setSelected} />
      <BookModal book={selected} onClose={() => setSelected(null)} />
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root-search")).render(<App />);
