window.AnalysisCard = {
  props: ['item'],
  template: `
    <a class="mc-analysis" :href="'/history/' + item.id">
      <img class="mc-analysis__thumb" :src="item.image_path" :alt="item.main_food || ''"
           @error="$event.target.style.visibility='hidden'" />
      <div class="flex-grow-1 min-w-0">
        <div class="mc-analysis__name text-truncate">{{ item.main_food || 'Not detected' }}</div>
        <div class="mc-analysis__cal">{{ Math.round(item.total_calories || 0) }} <small class="text-muted fw-normal">kcal</small></div>
        <div class="mc-analysis__meta">{{ MC.fmtTime(item.analyzed_at) }}</div>
      </div>
    </a>
  `
};
