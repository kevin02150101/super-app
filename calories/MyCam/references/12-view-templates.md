# 12 — View 樣板 sample（Jinja2）

## 1. `templates/base.html`

```html
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="csrf-token" content="{{ csrf_token() }}" />
  <title>{% block title %}MyCam{% endblock %}</title>

  <link rel="stylesheet" href="{{ url_for('static', filename='vendor/bootstrap-5.3/bootstrap.min.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='vendor/sweetalert2/sweetalert2.min.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/hero-dashboard.css') }}">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/components.css') }}">
</head>
<body>
  {% include "_layout/navbar.html" %}

  <div class="mc-shell">
    {% if current_user.is_authenticated %}
      {% include "_layout/sidebar.html" %}
    {% endif %}

    <main class="mc-main">
      {% block hero %}{% endblock %}
      <div class="container-fluid py-4" id="app">
        {% block content %}{% endblock %}
      </div>
    </main>
  </div>

  <script src="{{ url_for('static', filename='vendor/vue-3.0/vue.global.prod.js') }}"></script>
  <script src="{{ url_for('static', filename='vendor/axios/axios.min.js') }}"></script>
  <script src="{{ url_for('static', filename='vendor/sweetalert2/sweetalert2.min.js') }}"></script>
  <script src="{{ url_for('static', filename='vendor/chartjs/chart.umd.js') }}"></script>
  <script src="{{ url_for('static', filename='vendor/bootstrap-5.3/bootstrap.bundle.min.js') }}"></script>
  <script src="{{ url_for('static', filename='js/app.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
```

## 2. `templates/_layout/hero.html`

```html
<section class="mc-hero">
  <div class="mc-hero__inner">
    <div>
      <h1 class="mc-hero__title">{{ title }}</h1>
      <p class="mc-hero__sub">{{ subtitle }}</p>
      {% if cta %}<a href="{{ cta.url }}" class="btn btn-light btn-lg rounded-pill">{{ cta.text }}</a>{% endif %}
    </div>
    {% if kpis %}
    <div class="mc-hero__kpis">
      {% for k in kpis %}
        <div class="mc-kpi">
          <div class="mc-kpi__label">{{ k.label }}</div>
          <div class="mc-kpi__value">{{ k.value }}</div>
        </div>
      {% endfor %}
    </div>
    {% endif %}
  </div>
</section>
```

## 3. `templates/dashboard/index.html`

```html
{% extends "base.html" %}
{% block title %}Dashboard · MyCam{% endblock %}

{% block hero %}
  {% with title="嗨，{}！".format(current_user.nickname or current_user.email),
          subtitle="今日的飲食總覽與健康建議",
          cta={"url": url_for('capture.index'), "text": "立即拍照分析"},
          kpis=[
            {"label":"今日卡路里","value": kpi.today_calories|round|int},
            {"label":"歷史筆數","value": kpi.total_count},
            {"label":"常見食物","value": kpi.top_food or "—"},
          ] %}
    {% include "_layout/hero.html" %}
  {% endwith %}
{% endblock %}

{% block content %}
  <div class="row g-4">
    <div class="col-lg-8">
      <div class="mc-card">
        <h5 class="mc-card__title">近 30 日卡路里趨勢</h5>
        <canvas id="caloriesChart" height="120"></canvas>
      </div>
    </div>
    <div class="col-lg-4">
      <div class="mc-card">
        <h5 class="mc-card__title">食物種類分佈</h5>
        <canvas id="categoryChart" height="200"></canvas>
      </div>
    </div>

    <div class="col-12">
      <div class="mc-card">
        <h5 class="mc-card__title">最近分析</h5>
        <recent-analyses></recent-analyses>
      </div>
    </div>
  </div>
{% endblock %}

{% block scripts %}
  <script src="{{ url_for('static', filename='js/components/AnalysisCard.js') }}"></script>
  <script src="{{ url_for('static', filename='js/pages/dashboard.js') }}"></script>
{% endblock %}
```

## 4. `templates/capture/index.html`

```html
{% extends "base.html" %}
{% block content %}
  <capture-uploader></capture-uploader>
{% endblock %}
{% block scripts %}
  <script src="{{ url_for('static', filename='js/components/CaptureUploader.js') }}"></script>
  <script src="{{ url_for('static', filename='js/pages/capture.js') }}"></script>
{% endblock %}
```
