# 13 — CSS 範本（Hero Dashboard）

## 1. `static/css/hero-dashboard.css`

```css
:root {
  --mc-primary: #6a11cb;
  --mc-primary-2: #2575fc;
  --mc-bg: #f5f7fb;
  --mc-text: #1f2937;
  --mc-muted: #6b7280;
  --mc-card: #ffffff;
  --mc-radius: 1rem;
  --mc-shadow: 0 6px 24px rgba(0,0,0,.06);
  --mc-success: #22c55e;
  --mc-warning: #f59e0b;
  --mc-danger: #ef4444;
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Inter", "Noto Sans TC", system-ui, -apple-system, sans-serif;
  color: var(--mc-text);
  background: var(--mc-bg);
}

/* Shell */
.mc-shell { display: flex; min-height: 100vh; }
.mc-main  { flex: 1; min-width: 0; }

/* Sidebar */
.mc-sidebar {
  width: 240px;
  background: #0f172a;
  color: #cbd5e1;
  padding: 1.25rem 1rem;
}
.mc-sidebar a {
  display: block; padding: .65rem .9rem; border-radius: .6rem;
  color: #cbd5e1; text-decoration: none; margin-bottom: .25rem;
}
.mc-sidebar a:hover, .mc-sidebar a.active {
  background: rgba(255,255,255,.08); color: #fff;
}

/* Hero */
.mc-hero {
  background: linear-gradient(135deg, var(--mc-primary) 0%, var(--mc-primary-2) 100%);
  color: #fff;
  padding: 3rem 2rem 4.5rem;
  border-bottom-left-radius: 2rem;
  border-bottom-right-radius: 2rem;
}
.mc-hero__inner {
  display: flex; justify-content: space-between; gap: 2rem; flex-wrap: wrap;
  max-width: 1200px; margin: 0 auto;
}
.mc-hero__title { font-size: 2rem; font-weight: 700; margin: 0 0 .25rem; }
.mc-hero__sub   { opacity: .85; margin-bottom: 1.25rem; }

.mc-hero__kpis { display: grid; grid-template-columns: repeat(3, minmax(140px,1fr)); gap: 1rem; }
.mc-kpi {
  background: rgba(255,255,255,.12);
  border: 1px solid rgba(255,255,255,.18);
  border-radius: var(--mc-radius);
  padding: 1rem 1.25rem;
  backdrop-filter: blur(6px);
}
.mc-kpi__label { font-size: .8rem; opacity: .85; }
.mc-kpi__value { font-size: 1.6rem; font-weight: 700; }

/* Card */
.mc-card {
  background: var(--mc-card);
  border-radius: var(--mc-radius);
  box-shadow: var(--mc-shadow);
  padding: 1.25rem 1.25rem 1rem;
  margin-top: -2rem; /* 第一排卡片覆蓋 Hero */
}
.mc-card + .mc-card { margin-top: 0; }
.mc-card__title { font-weight: 600; margin: 0 0 .75rem; }

/* Analysis Card */
.mc-analysis {
  display: flex; gap: 1rem; padding: 1rem;
  border: 1px solid #eef0f4; border-radius: var(--mc-radius);
  transition: transform .15s ease;
}
.mc-analysis:hover { transform: translateY(-2px); box-shadow: var(--mc-shadow); }
.mc-analysis__thumb {
  width: 96px; height: 96px; border-radius: .8rem; object-fit: cover; flex: 0 0 auto;
}
.mc-analysis__name { font-weight: 600; }
.mc-analysis__cal  { font-size: 1.4rem; color: var(--mc-primary); font-weight: 700; }
.mc-analysis__meta { font-size: .8rem; color: var(--mc-muted); }

/* Responsive */
@media (max-width: 768px) {
  .mc-sidebar { display: none; }
  .mc-hero { padding: 2rem 1rem 3rem; }
  .mc-hero__kpis { grid-template-columns: repeat(3, 1fr); }
  .mc-hero__title { font-size: 1.5rem; }
}
```

## 2. `static/css/components.css`

```css
.mc-btn-primary {
  background: linear-gradient(135deg, var(--mc-primary), var(--mc-primary-2));
  color: #fff; border: none; padding: .65rem 1.2rem; border-radius: 999px;
  font-weight: 600;
}
.mc-btn-primary:hover { filter: brightness(1.05); }

.mc-tag {
  display: inline-block; padding: .15rem .5rem; border-radius: .5rem;
  background: #eef2ff; color: #4338ca; font-size: .75rem;
}

.mc-camera {
  width: 100%; max-width: 480px; aspect-ratio: 4/3;
  background: #000; border-radius: var(--mc-radius); overflow: hidden;
}
.mc-camera video { width: 100%; height: 100%; object-fit: cover; }
```
