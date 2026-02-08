/**
 * Filter management (pattern from trip's category/filter system).
 *
 * Handles borough selection, date range, and layer toggles.
 */
const Filters = {
  borough: '',
  startDate: null,
  endDate: null,

  init() {
    // Borough filter buttons (pattern from trip: quick filter buttons)
    document.getElementById('borough-filters').addEventListener('click', (e) => {
      const btn = e.target.closest('.filter-btn');
      if (!btn) return;

      document.querySelectorAll('#borough-filters .filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      this.borough = btn.dataset.borough;
      document.dispatchEvent(new CustomEvent('filters-changed'));
    });

    // Apply button for date range
    document.getElementById('apply-filters').addEventListener('click', () => {
      this.startDate = document.getElementById('filter-start').value || null;
      this.endDate = document.getElementById('filter-end').value || null;
      document.dispatchEvent(new CustomEvent('filters-changed'));
    });

    // Layer toggles
    ['stations', 'safety', 'heatmap'].forEach(layer => {
      const el = document.getElementById(`layer-${layer}`);
      if (el) {
        el.addEventListener('change', (e) => {
          document.dispatchEvent(new CustomEvent('layer-toggled', {
            detail: { layer, visible: e.target.checked },
          }));
        });
      }
    });

    return this;
  },

  /** Get current filter params for API calls. */
  getParams() {
    const params = {};
    if (this.borough) params.borough = this.borough;
    if (this.startDate) params.start = this.startDate;
    if (this.endDate) params.end = this.endDate;
    return params;
  },
};
