/**
 * SkillGap Analyzer — Main JavaScript
 *
 * Handles:
 *  1. Mobile nav toggle
 *  2. Input tabs (paste text / upload file)
 *  3. File drag-and-drop zones
 *  4. Form submit spinner
 *  5. Result page: skill filter pills + search + sort
 *  6. History: auto-submit on sort change
 */

// ── 1. Mobile nav toggle ─────────────────────────────────────────────────────
(function () {
  const toggle = document.getElementById('navToggle');
  const links  = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
    });
  }
})();

// ── 2. Input tabs ─────────────────────────────────────────────────────────────
(function () {
  document.querySelectorAll('.input-tabs').forEach(function (tabGroup) {
    const buttons = tabGroup.querySelectorAll('.tab-btn');
    const parent  = tabGroup.parentElement;

    buttons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        const targetId = btn.getAttribute('data-tab');
        const target   = document.getElementById(targetId);
        if (!target) return;

        // Deactivate all tabs + content within same section
        buttons.forEach(b => b.classList.remove('active'));
        parent.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        btn.classList.add('active');
        target.classList.add('active');
      });
    });
  });
})();

// ── 3. File drag-and-drop ─────────────────────────────────────────────────────
(function () {
  function setupDropZone(dropZoneId, fileInputId, selectedId, fileNameId) {
    const zone     = document.getElementById(dropZoneId);
    const input    = document.getElementById(fileInputId);
    const selected = document.getElementById(selectedId);
    const nameLbl  = document.getElementById(fileNameId);
    if (!zone || !input) return;

    function showFile(file) {
      if (!file) return;
      if (selected) selected.style.display = 'flex';
      if (nameLbl)  nameLbl.textContent = file.name;
      zone.querySelector('.file-drop-content').style.display = 'none';
    }

    input.addEventListener('change', function () {
      showFile(this.files[0]);
    });

    zone.addEventListener('dragover', function (e) {
      e.preventDefault();
      zone.classList.add('drag-over');
    });
    zone.addEventListener('dragleave', function () {
      zone.classList.remove('drag-over');
    });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      zone.classList.remove('drag-over');
      const file = e.dataTransfer.files[0];
      if (file) {
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        showFile(file);
      }
    });
  }

  setupDropZone('resumeDropZone', 'resume_file', 'resumeFileSelected', 'resumeFileName');
  setupDropZone('jdDropZone',     'jd_file',     'jdFileSelected',     'jdFileName');
})();

// ── 4. Form submit spinner ────────────────────────────────────────────────────
(function () {
  const form = document.getElementById('analyzeForm');
  if (!form) return;
  form.addEventListener('submit', function () {
    const btn     = document.getElementById('submitBtn');
    const text    = btn && btn.querySelector('.btn-text');
    const spinner = btn && btn.querySelector('.btn-spinner');
    if (btn) btn.disabled = true;
    if (text)    text.style.display    = 'none';
    if (spinner) spinner.style.display = 'inline';
  });
})();

// ── 5. Result page: filter + search + sort ────────────────────────────────────
(function () {
  const searchInput = document.getElementById('skillSearch');
  const sortSelect  = document.getElementById('skillSort');
  const pills       = document.querySelectorAll('.filter-pills .pill');
  const skillItems  = document.querySelectorAll('.skill-item');
  const groups      = document.querySelectorAll('.skills-group');

  if (!searchInput && !pills.length) return;

  let activeFilter = 'all';
  let activeSearch = '';
  let activeSort   = 'status';

  function applyFilter() {
    skillItems.forEach(function (item) {
      const status   = item.getAttribute('data-status') || '';
      const priority = item.getAttribute('data-priority') || '';
      const name     = (item.getAttribute('data-name') || '').toLowerCase();

      // Search
      const matchSearch = !activeSearch || name.includes(activeSearch.toLowerCase());

      // Filter
      let matchFilter = false;
      if (activeFilter === 'all') {
        matchFilter = true;
      } else if (['matched', 'partial', 'missing'].includes(activeFilter)) {
        matchFilter = status === activeFilter;
      } else if (['HIGH', 'MEDIUM', 'LOW'].includes(activeFilter)) {
        matchFilter = priority === activeFilter;
      }

      item.classList.toggle('hidden', !(matchSearch && matchFilter));
    });

    // Hide group headings if all items in group are hidden
    groups.forEach(function (group) {
      const visible = group.querySelectorAll('.skill-item:not(.hidden)');
      group.style.display = visible.length === 0 ? 'none' : '';
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', function () {
      activeSearch = this.value.trim();
      applyFilter();
    });
  }

  pills.forEach(function (pill) {
    pill.addEventListener('click', function () {
      pills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeFilter = pill.getAttribute('data-filter');
      applyFilter();
    });
  });

  if (sortSelect) {
    sortSelect.addEventListener('change', function () {
      activeSort = this.value;
      sortSkills(activeSort);
    });
  }

  function sortSkills(mode) {
    document.querySelectorAll('.skill-items').forEach(function (container) {
      const items = Array.from(container.querySelectorAll('.skill-item'));
      items.sort(function (a, b) {
        if (mode === 'alpha') {
          return (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || '');
        }
        if (mode === 'priority') {
          const order = { 'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, '': 3 };
          return (order[a.getAttribute('data-priority')] || 3) - (order[b.getAttribute('data-priority')] || 3);
        }
        // Default 'status' — original DOM order is already status-grouped
        return 0;
      });
      items.forEach(item => container.appendChild(item));
    });
  }
})();

// ── 6. History: auto-submit sort on change ────────────────────────────────────
(function () {
  const form    = document.getElementById('historySearchForm');
  const sortBy  = document.getElementById('historySortBy');
  const orderEl = document.getElementById('historyOrder');
  if (!form) return;
  if (sortBy)  sortBy.addEventListener('change',  () => form.submit());
  if (orderEl) orderEl.addEventListener('change', () => form.submit());
})();
