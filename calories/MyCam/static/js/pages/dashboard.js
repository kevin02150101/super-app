const { createApp } = Vue;

const RecentAnalyses = {
  components: { AnalysisCard: window.AnalysisCard },
  data() { return { items: [] }; },
  template: `
    <div class="row g-3">
      <div class="col-md-6 col-lg-4" v-for="it in items" :key="it.id">
        <analysis-card :item="it"></analysis-card>
      </div>
      <div class="col-12 text-muted text-center py-3" v-if="!items.length">
        No records yet — <a href="/capture/">Take a photo now</a>。
      </div>
    </div>
  `,
  async mounted() {
    try {
      const { data } = await axios.get('/api/analyses', { params: { page: 1, per_page: 6 } });
      this.items = data.data.items;
    } catch (e) { console.error(e); }
    this._loadCharts();
  },
  methods: {
    async _loadCharts() {
      try {
        const cal = (await axios.get('/api/stats/calories', { params: { days: 30 } })).data.data;
        const cat = (await axios.get('/api/stats/categories')).data.data;

        new Chart(document.getElementById('caloriesChart'), {
          type: 'line',
          data: {
            labels: cal.map(d => d.date),
            datasets: [{
              label: 'kcal',
              data: cal.map(d => d.calories),
              tension: .35, fill: true,
              borderColor: '#6a11cb',
              backgroundColor: 'rgba(106,17,203,.15)',
              pointRadius: 3
            }]
          },
          options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
        });

        new Chart(document.getElementById('categoryChart'), {
          type: 'doughnut',
          data: {
            labels: cat.map(c => c.category),
            datasets: [{
              data: cat.map(c => c.count),
              backgroundColor: ['#6a11cb','#2575fc','#22c55e','#f59e0b','#ef4444','#0ea5e9','#a855f7']
            }]
          },
          options: { cutout: '65%' }
        });
      } catch (e) { console.error(e); }
    }
  }
};

createApp({ components: { RecentAnalyses } }).mount('#app');
