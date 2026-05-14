window.HistoryTable = {
  data() { return { items: [], page: 1, perPage: 12, total: 0, loading: false }; },
  computed: {
    totalPages() { return Math.max(1, Math.ceil(this.total / this.perPage)); }
  },
  mounted() { this.load(); },
  methods: {
    async load() {
      this.loading = true;
      try {
        const { data } = await axios.get('/api/analyses', { params: { page: this.page, per_page: this.perPage } });
        this.items = data.data.items;
        this.total = data.data.total;
      } catch (e) { MC.notify('error', 'Load failed', MC.errorOf(e)); }
      finally { this.loading = false; }
    },
    fmt(s) { return MC.fmtTime(s); },
    go(p) { if (p < 1 || p > this.totalPages) return; this.page = p; this.load(); },
    async del(id) {
      const r = await Swal.fire({ icon: 'warning', title: 'Delete this entry?', showCancelButton: true });
      if (!r.isConfirmed) return;
      try {
        await axios.delete('/api/analyses/' + id);
        this.load();
      } catch (e) { MC.notify('error', 'Delete failed', MC.errorOf(e)); }
    }
  },
  template: `
    <div>
      <div v-if="loading" class="text-center py-4 text-muted">Loading…</div>
      <div v-else-if="!items.length" class="text-center py-5 text-muted">
        No records yet.<a href="/capture/">Take a photo now</a>
      </div>
      <div v-else class="table-responsive">
        <table class="table align-middle">
          <thead><tr>
            <th></th><th>Main foods</th><th class="text-end">Total calories</th>
            <th>Time</th><th class="text-end"></th>
          </tr></thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td style="width:90px"><img :src="it.image_path" style="width:72px;height:72px;object-fit:cover;border-radius:.5rem" /></td>
              <td><a :href="'/history/' + it.id">{{ it.main_food || 'Not detected' }}</a><br>
                  <small class="text-muted text-truncate d-block" style="max-width:340px">{{ it.summary }}</small></td>
              <td class="text-end fw-bold" style="color:var(--mc-primary)">{{ Math.round(it.total_calories) }} kcal</td>
              <td>{{ fmt(it.analyzed_at) }}</td>
              <td class="text-end">
                <a :href="'/history/' + it.id" class="btn btn-sm btn-outline-primary">View</a>
                <button class="btn btn-sm btn-outline-danger" @click="del(it.id)"><i class="bi bi-trash"></i></button>
              </td>
            </tr>
          </tbody>
        </table>
        <nav v-if="totalPages > 1" class="d-flex justify-content-center">
          <ul class="pagination">
            <li class="page-item" :class="{disabled: page===1}"><a class="page-link" href="#" @click.prevent="go(page-1)">‹</a></li>
            <li class="page-item disabled"><span class="page-link">{{ page }} / {{ totalPages }}</span></li>
            <li class="page-item" :class="{disabled: page===totalPages}"><a class="page-link" href="#" @click.prevent="go(page+1)">›</a></li>
          </ul>
        </nav>
      </div>
    </div>
  `
};
