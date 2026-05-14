// Dashboard
const { useEffect, useState } = React;

function Kpi({ label, value }) {
  return (
    <div className="col-12 col-sm-6 col-lg">
      <div className="card kpi-card shadow-sm h-100 p-3">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
      </div>
    </div>
  );
}

function BarChart({ title, items, labelKey, valueKey }) {
  const max = Math.max(1, ...items.map((x) => x[valueKey] || 0));
  return (
    <div className="card shadow-sm border-0 p-4 h-100">
      <h6 className="fw-semibold mb-3">{title}</h6>
      {items.length === 0 ? (
        <div className="text-muted small">No data yet</div>
      ) : (
        <div className="bar-chart">
          {items.map((it, i) => {
            const pct = ((it[valueKey] || 0) / max) * 100;
            return (
              <div key={i} className="bar-row">
                <div className="d-flex justify-content-between small">
                  <span className="text-truncate me-2">{it[labelKey]}</span>
                  <span className="text-muted">{it[valueKey]}</span>
                </div>
                <div className="bar-fill" style={{ width: `${pct}%` }} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function TrendChart({ data }) {
  const max = Math.max(1, ...data.map((d) => d.count));
  return (
    <div className="card shadow-sm border-0 p-4 h-100">
      <h6 className="fw-semibold mb-3">Search volume (last 14 days)</h6>
      {data.length === 0 ? (
        <div className="text-muted small">No data yet</div>
      ) : (
        <>
          <div className="trend-chart">
            {data.map((d, i) => (
              <div key={i} className="d-flex flex-column align-items-center" style={{ flex: 1 }}>
                <div
                  className="trend-bar w-100"
                  style={{ height: `${(d.count / max) * 100}%` }}
                  title={`${d.date}: ${d.count}`}
                />
              </div>
            ))}
          </div>
          <div className="d-flex mt-2">
            {data.map((d, i) => (
              <div key={i} className="trend-bar-label text-muted text-center" style={{ flex: 1 }}>
                {d.date.slice(5)}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    window.apiClient
      .get("/stats/dashboard")
      .then((resp) => setData(resp.data))
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <div className="alert alert-danger">{error}</div>;
  if (!data) {
    return (
      <div className="text-center py-5">
        <div className="spinner-border text-primary" />
      </div>
    );
  }

  const ov = data.overview;
  return (
    <div>
      <div className="row g-3 mb-4">
        <Kpi label="Total searches" value={ov.total_queries} />
        <Kpi label="Distinct keywords" value={ov.distinct_keywords} />
        <Kpi label="Total books indexed" value={ov.total_results} />
        <Kpi label="Avg. results per search" value={ov.avg_results_per_query} />
        <Kpi label="Average book price" value={`NT$ ${ov.avg_book_price}`} />
      </div>

      <div className="row g-3 mb-4">
        <div className="col-12 col-lg-6">
          <BarChart title="Search category distribution" items={data.query_categories || []}
                    labelKey="category" valueKey="count" />
        </div>
        <div className="col-12 col-lg-6">
          <BarChart title="Book category breakdown" items={data.book_categories || []}
                    labelKey="category" valueKey="count" />
        </div>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-12 col-lg-6">
          <BarChart title="Top 10 keywords" items={data.top_keywords}
                    labelKey="keyword" valueKey="count" />
        </div>
        <div className="col-12 col-lg-6">
          <BarChart title="Top 10 publishers" items={data.top_publishers}
                    labelKey="publisher" valueKey="count" />
        </div>
      </div>

      <div className="row g-3">
        <div className="col-12">
          <TrendChart data={data.daily_trend} />
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root-dashboard")).render(<App />);
