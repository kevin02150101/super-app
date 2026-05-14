# 14 — Vue 3 前端元件範例

> 全部以 Vue 3 Global Build + 純 JS 撰寫（不使用 SFC 編譯）。
> axios 預設帶入 CSRF token，於 `app.js` 統一設定。

## 1. `static/js/app.js`

```js
(() => {
  const meta = document.querySelector('meta[name="csrf-token"]');
  if (meta && window.axios) {
    axios.defaults.headers.common['X-CSRFToken'] = meta.content;
    axios.defaults.withCredentials = true;
  }
  window.MC = { Vue: window.Vue, axios: window.axios, Swal: window.Swal };
})();
```

## 2. `static/js/components/CaptureUploader.js`

```js
const CaptureUploader = {
  template: `
    <div class="row g-4">
      <div class="col-lg-6">
        <div class="mc-card">
          <h5 class="mc-card__title">鏡頭拍攝</h5>
          <div class="mc-camera mb-3"><video ref="video" autoplay playsinline></video></div>
          <button class="mc-btn-primary me-2" @click="startCamera" v-if="!streaming">啟動鏡頭</button>
          <button class="mc-btn-primary me-2" @click="capture" :disabled="!streaming">拍照分析</button>
          <button class="btn btn-outline-secondary" @click="stopCamera" v-if="streaming">關閉</button>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="mc-card">
          <h5 class="mc-card__title">上傳相片</h5>
          <input type="file" class="form-control mb-3" accept="image/*" @change="onPick" />
          <button class="mc-btn-primary" :disabled="!file || loading" @click="uploadFile">
            {{ loading ? '分析中…' : '開始分析' }}
          </button>
        </div>
      </div>
    </div>
  `,
  data() { return { streaming: false, stream: null, file: null, loading: false }; },
  methods: {
    async startCamera() {
      this.stream = await navigator.mediaDevices.getUserMedia({ video: true });
      this.$refs.video.srcObject = this.stream;
      this.streaming = true;
    },
    stopCamera() {
      this.stream?.getTracks().forEach(t => t.stop());
      this.streaming = false; this.stream = null;
    },
    onPick(e) { this.file = e.target.files[0] || null; },
    async capture() {
      const v = this.$refs.video;
      const canvas = document.createElement('canvas');
      canvas.width = v.videoWidth; canvas.height = v.videoHeight;
      canvas.getContext('2d').drawImage(v, 0, 0);
      const blob = await new Promise(r => canvas.toBlob(r, 'image/jpeg', 0.9));
      await this._send(blob, 'capture.jpg');
    },
    async uploadFile() { await this._send(this.file, this.file.name); },
    async _send(blob, name) {
      this.loading = true;
      try {
        const fd = new FormData();
        fd.append('image', blob, name);
        const { data } = await axios.post('/api/analyze', fd);
        await Swal.fire({ icon: 'success', title: '分析完成', text: data.data.summary });
        location.href = `/history/${data.data.id}`;
      } catch (e) {
        Swal.fire({ icon: 'error', title: '分析失敗', text: e.response?.data?.error?.message || e.message });
      } finally { this.loading = false; }
    }
  }
};
window.CaptureUploader = CaptureUploader;
```

## 3. `static/js/components/AnalysisCard.js`

```js
const AnalysisCard = {
  props: ['item'],
  template: `
    <a class="mc-analysis text-decoration-none text-reset" :href="'/history/' + item.id">
      <img class="mc-analysis__thumb" :src="item.thumb || item.image_path" alt="" />
      <div class="flex-grow-1">
        <div class="mc-analysis__name">{{ item.main_food || '—' }}</div>
        <div class="mc-analysis__cal">{{ Math.round(item.total_calories) }} <small class="text-muted">kcal</small></div>
        <div class="mc-analysis__meta">{{ formatTime(item.analyzed_at) }}</div>
      </div>
    </a>
  `,
  methods: {
    formatTime(s) { return new Date(s).toLocaleString('zh-TW'); }
  }
};
window.AnalysisCard = AnalysisCard;
```

## 4. `static/js/pages/dashboard.js`

```js
const { createApp } = Vue;

const RecentAnalyses = {
  components: { AnalysisCard: window.AnalysisCard },
  data() { return { items: [] }; },
  template: `
    <div class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="it in items" :key="it.id">
        <analysis-card :item="it"></analysis-card>
      </div>
      <div class="col-12 text-muted" v-if="!items.length">尚無紀錄，點擊右上「立即拍照分析」開始。</div>
    </div>
  `,
  async mounted() {
    const { data } = await axios.get('/api/analyses', { params: { page: 1, per_page: 6 } });
    this.items = data.data.items;
    this._loadCharts();
  },
  methods: {
    async _loadCharts() {
      const cal = (await axios.get('/api/stats/calories', { params: { days: 30 } })).data.data;
      const cat = (await axios.get('/api/stats/categories')).data.data;

      new Chart(document.getElementById('caloriesChart'), {
        type: 'line',
        data: { labels: cal.map(d => d.date),
                datasets: [{ label: 'kcal', data: cal.map(d => d.calories),
                             tension: .35, fill: true,
                             borderColor: '#6a11cb', backgroundColor: 'rgba(106,17,203,.15)' }] },
        options: { plugins: { legend: { display: false } } }
      });

      new Chart(document.getElementById('categoryChart'), {
        type: 'doughnut',
        data: { labels: cat.map(c => c.category),
                datasets: [{ data: cat.map(c => c.count) }] },
        options: { cutout: '65%' }
      });
    }
  }
};

createApp({ components: { RecentAnalyses } }).mount('#app');
```

## 5. `static/js/pages/capture.js`

```js
const { createApp } = Vue;
createApp({ components: { CaptureUploader: window.CaptureUploader } }).mount('#app');
```
