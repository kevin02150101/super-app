(async () => {
  try {
    const cal = (await axios.get('/api/stats/calories', { params: { days: 60 } })).data.data;
    const cat = (await axios.get('/api/stats/categories')).data.data;

    new Chart(document.getElementById('caloriesChart'), {
      type: 'bar',
      data: {
        labels: cal.map(d => d.date),
        datasets: [{
          label: 'kcal', data: cal.map(d => d.calories),
          backgroundColor: 'rgba(106,17,203,.7)'
        }]
      },
      options: { plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });

    new Chart(document.getElementById('categoryChart'), {
      type: 'doughnut',
      data: {
        labels: cat.map(c => c.category),
        datasets: [{ data: cat.map(c => c.count),
                     backgroundColor: ['#6a11cb','#2575fc','#22c55e','#f59e0b','#ef4444','#0ea5e9','#a855f7'] }]
      },
      options: { cutout: '65%' }
    });

    const tbody = document.getElementById('catTbody');
    tbody.innerHTML = cat.map(c =>
      `<tr><td><span class="mc-tag">${c.category}</span></td>
           <td class="text-end">${c.count}</td>
           <td class="text-end">${Math.round(c.calories)} kcal</td></tr>`
    ).join('') || `<tr><td colspan="3" class="text-center text-muted">No data yet</td></tr>`;
  } catch (e) { console.error(e); }
})();
