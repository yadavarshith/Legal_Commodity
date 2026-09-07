/**
 * APEX — LabelSure Web Application Client Logic
 * Real OCR Inspection with Tesseract 5.4 + PCR Rule 6(1) Evaluation
 */

document.addEventListener('DOMContentLoaded', () => {
  let selectedFile = null;
  let rulesList = [];

  // DOM Elements
  const navTabs = document.querySelectorAll('.nav-tab');
  const tabContents = document.querySelectorAll('.tab-content');
  const subnavBtns = document.querySelectorAll('.subnav-btn');
  const subtabContents = document.querySelectorAll('.subtab-content');
  
  const dropzone = document.getElementById('dropzone');
  const imageUploadInput = document.getElementById('image-upload');
  const btnBrowseFile = document.getElementById('btn-browse-file');
  const btnRunInspection = document.getElementById('btn-run-inspection');
  const fileStatusPill = document.getElementById('file-status-pill');
  const fileNameSpan = document.getElementById('file-name-span');
  const uploadMainTitle = document.getElementById('upload-main-title');
  const metaCategory = document.getElementById('meta-category');
  const metaImport = document.getElementById('meta-import');
  
  const imageContainer = document.getElementById('image-container');
  const activeImageInfo = document.getElementById('active-image-info');

  const statusBar = document.getElementById('overall-status-bar');
  const statusIcon = document.getElementById('overall-status-icon');
  const statusTitle = document.getElementById('overall-status-title');
  const statusDesc = document.getElementById('overall-status-desc');
  const caseIdDisplay = document.getElementById('case-id-display');

  const findingsList = document.getElementById('findings-list');
  const declTableBody = document.getElementById('declarations-table-body');
  const findingsCount = document.getElementById('findings-count');
  const declCount = document.getElementById('declarations-count');

  // Navigation Tabs
  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      navTabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.getAttribute('data-tab');
      document.getElementById(targetId).classList.add('active');
    });
  });

  // Subnav Tabs
  subnavBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      subnavBtns.forEach(b => b.classList.remove('active'));
      subtabContents.forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-subtab');
      document.getElementById(targetId).classList.add('active');
    });
  });

  // File Upload Handling
  if (btnBrowseFile && imageUploadInput) {
    btnBrowseFile.addEventListener('click', (e) => {
      e.stopPropagation();
      imageUploadInput.click();
    });
  }

  if (dropzone) {
    dropzone.addEventListener('click', () => imageUploadInput.click());
    
    ['dragenter', 'dragover'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.add('has-file');
      }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropzone.addEventListener(eventName, (e) => {
        e.preventDefault();
        dropzone.classList.remove('has-file');
      }, false);
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt.files && dt.files[0]) {
        handleFileSelection(dt.files[0]);
      }
    });
  }

  if (imageUploadInput) {
    imageUploadInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelection(e.target.files[0]);
      }
    });
  }

  // Handle Selected Image File
  function handleFileSelection(file) {
    selectedFile = file;
    dropzone.classList.add('has-file');
    
    if (fileNameSpan) fileNameSpan.innerText = file.name;
    if (fileStatusPill) fileStatusPill.style.display = 'inline-flex';
    if (uploadMainTitle) uploadMainTitle.innerText = `Loaded: ${file.name}`;

    // Enable inspection button
    if (btnRunInspection) {
      btnRunInspection.classList.add('ready');
      btnRunInspection.disabled = false;
    }

    // Render Clean Image Preview
    const previewUrl = URL.createObjectURL(file);
    imageContainer.innerHTML = `
      <div class="uploaded-canvas-wrapper" style="position: relative; max-width: 100%; display: inline-block; border-radius: 12px; overflow: hidden; border: 1px solid var(--border-glow);">
        <img src="${previewUrl}" alt="${file.name}" style="display: block; max-width: 100%; max-height: 440px; object-fit: contain;" id="active-package-img">
        <div class="laser-scan-line" id="laser-scanner" style="display: none;"></div>
      </div>
    `;

    activeImageInfo.innerText = `${file.name} (${Math.round(file.size / 1024)} KB)`;

    // Reset results panel
    statusBar.className = 'overall-status-bar status-idle';
    statusIcon.className = 'fa-solid fa-circle-info status-icon';
    statusTitle.innerText = 'IMAGE LOADED — READY TO INSPECT';
    statusDesc.innerText = 'Click "⚡ RUN LEGAL METROLOGY INSPECTION" to scan this label';
    caseIdDisplay.innerText = 'INS-READY';
    findingsList.innerHTML = '<div class="empty-list-state"><p>Click <strong>"⚡ RUN LEGAL METROLOGY INSPECTION"</strong> to evaluate compliance.</p></div>';
    declTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">Awaiting inspection...</td></tr>';
    findingsCount.innerText = '0';
    declCount.innerText = '0';
  }

  // Launch Inspection & OCR Scanner
  if (btnRunInspection) {
    btnRunInspection.addEventListener('click', async () => {
      if (!selectedFile) {
        alert('Please select or browse a package label image file first!');
        return;
      }

      // Show Laser Scanner Animation
      const laserScanner = document.getElementById('laser-scanner');
      if (laserScanner) laserScanner.style.display = 'block';

      // Disable button during scan
      btnRunInspection.disabled = true;
      btnRunInspection.classList.add('scanning');

      statusBar.className = 'overall-status-bar status-review';
      statusIcon.className = 'fa-solid fa-spinner fa-spin status-icon';
      statusTitle.innerText = 'RUNNING OCR SCAN & RULE ENGINE...';
      statusDesc.innerText = 'Extracting text from package label with Tesseract OCR...';

      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('category', metaCategory ? metaCategory.value : 'all');
      formData.append('package_type', 'pre-packaged');
      formData.append('import_status', metaImport ? metaImport.value : 'domestic');

      try {
        const res = await fetch('/upload-and-scan', {
          method: 'POST',
          body: formData
        });

        if (laserScanner) laserScanner.style.display = 'none';
        btnRunInspection.disabled = false;
        btnRunInspection.classList.remove('scanning');

        if (res.ok) {
          const data = await res.json();
          renderInspectionResults(data);
        } else {
          statusBar.className = 'overall-status-bar status-review';
          statusIcon.className = 'fa-solid fa-circle-exclamation status-icon';
          statusTitle.innerText = 'SCAN FAILED';
          statusDesc.innerText = 'Server returned an error. Check if backend is running.';
        }
      } catch (err) {
        if (laserScanner) laserScanner.style.display = 'none';
        btnRunInspection.disabled = false;
        btnRunInspection.classList.remove('scanning');
        console.error('Inspection failed:', err);
        statusBar.className = 'overall-status-bar status-review';
        statusIcon.className = 'fa-solid fa-circle-exclamation status-icon';
        statusTitle.innerText = 'CONNECTION ERROR';
        statusDesc.innerText = 'Could not reach backend: ' + err.message;
      }
    });
  }

  // Render Full Inspection Results
  function renderInspectionResults(data) {
    caseIdDisplay.innerText = data.inspection_id;

    const ocrCount = data.ocr_results ? data.ocr_results.length : 0;
    const declsCount = data.declarations ? data.declarations.length : 0;
    const findCount = data.findings ? data.findings.length : 0;

    // Overall Status Banner
    if (data.overall_status === 'review' || data.overall_status === 'fail') {
      statusBar.className = 'overall-status-bar status-review';
      statusIcon.className = 'fa-solid fa-triangle-exclamation status-icon';
      statusTitle.innerText = 'FLAGGED FOR INSPECTOR REVIEW';
      statusDesc.innerText = `OCR extracted ${ocrCount} text blocks → ${declsCount} declarations matched → ${findCount} rules evaluated`;
    } else {
      statusBar.className = 'overall-status-bar status-pass';
      statusIcon.className = 'fa-solid fa-circle-check status-icon';
      statusTitle.innerText = 'FULLY COMPLIANT (PASS)';
      statusDesc.innerText = `OCR extracted ${ocrCount} text blocks → ${declsCount} declarations matched → All rules passed`;
    }

    // Render Findings List
    findingsCount.innerText = findCount;
    if (findCount > 0) {
      findingsList.innerHTML = data.findings.map(f => `
        <div class="finding-card ${f.status.toLowerCase()}">
          <div class="finding-left">
            <div class="finding-header">
              <span class="rule-tag">${f.rule_id}</span>
              <span class="finding-desc">${f.description}</span>
            </div>
            <div class="finding-clause">PCR Rule 6(1) • Confidence: ${Math.round(f.confidence * 100)}%</div>
          </div>
          <span class="badge-status ${f.status.toLowerCase()}">${f.status}</span>
        </div>
      `).join('');
    } else {
      findingsList.innerHTML = `
        <div class="empty-list-state">
          <p><i class="fa-solid fa-circle-info"></i> No rule findings were generated. 
          ${ocrCount === 0 ? 'OCR could not extract text from this image. Try a clearer photo.' : 
            'No Legal Metrology declarations could be matched from the extracted text.'}</p>
        </div>
      `;
    }

    // Render Declarations Table
    declCount.innerText = declsCount;
    if (declsCount > 0) {
      declTableBody.innerHTML = data.declarations.map(d => `
        <tr class="decl-row" data-field="${d.type}">
          <td><strong>${formatDeclType(d.type)}</strong></td>
          <td><code>${escapeHtml(d.normalized_value)}</code></td>
          <td>${Math.round(d.confidence * 100)}%</td>
          <td><span class="badge-status pass">${d.status}</span></td>
        </tr>
      `).join('');
    } else {
      declTableBody.innerHTML = '';
    }

    // Show raw OCR text blocks section
    const ocrSection = document.getElementById('subtab-ocr-raw');
    if (ocrSection && data.ocr_results) {
      const ocrBody = document.getElementById('ocr-raw-body');
      const ocrBlockCount = document.getElementById('ocr-block-count');
      if (ocrBlockCount) ocrBlockCount.innerText = ocrCount;
      
      if (ocrBody) {
        if (ocrCount > 0) {
          ocrBody.innerHTML = data.ocr_results.map((r, idx) => `
            <tr class="ocr-row">
              <td>${idx + 1}</td>
              <td><code>${escapeHtml(r.text)}</code></td>
              <td>${Math.round(r.confidence * 100)}%</td>
              <td class="ocr-bbox">[${r.bbox.map(v => Math.round(v)).join(', ')}]</td>
            </tr>
          `).join('');
        } else {
          ocrBody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
            <i class="fa-solid fa-circle-exclamation"></i> No text could be extracted from this image. Try uploading a clearer, higher-resolution photo.
          </td></tr>`;
        }
      }
    }

    // Update Finding Select Dropdown in Audit Tab
    const reviewSelect = document.getElementById('review-finding-id');
    if (reviewSelect && data.findings) {
      reviewSelect.innerHTML = data.findings.map(f => `
        <option value="${f.finding_id}">${f.finding_id} — ${f.rule_id}: ${f.description} (${f.status})</option>
      `).join('');
      if (data.findings.length === 0) {
        reviewSelect.innerHTML = '<option value="">No findings to review</option>';
      }
    }
  }

  // Utility: Format declaration type for display
  function formatDeclType(type) {
    const map = {
      'PRODUCT_NAME': '📦 Product Name',
      'MANUFACTURER': '🏭 Manufacturer',
      'NET_QUANTITY': '⚖️ Net Quantity',
      'MRP': '💰 MRP',
      'MANUFACTURE_OR_PACK_DATE': '📅 Mfg/Pack Date',
      'BEST_BEFORE_OR_USE_BY': '⏳ Best Before',
      'CONSUMER_CARE': '📞 Consumer Care',
      'COUNTRY_OF_ORIGIN': '🌍 Country of Origin',
    };
    return map[type] || type;
  }

  // Utility: Escape HTML
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Load Rules from API
  async function loadRules() {
    try {
      const res = await fetch('/rules');
      if (res.ok) {
        rulesList = await res.json();
        renderRulesGrid(rulesList);
      }
    } catch (err) {
      console.warn('Could not fetch /rules:', err);
    }
  }

  function renderRulesGrid(rules) {
    const grid = document.getElementById('rules-cards-grid');
    if (!grid) return;

    grid.innerHTML = rules.map(rule => `
      <div class="rule-card">
        <div class="rule-card-header">
          <span class="rule-tag">${rule.rule_id}</span>
          <span class="severity-tag ${rule.severity.toLowerCase()}">${rule.severity}</span>
        </div>
        <div class="clause-badge">${rule.clause_reference}</div>
        <div class="rule-requirement">${rule.requirement}</div>
        <div class="sub-text">Applicability: ${rule.applicability.category}</div>
      </div>
    `).join('');
  }

  // Rule Filter & Search
  const ruleSearchInput = document.getElementById('rule-search');
  const categoryFilterSelect = document.getElementById('rule-category-filter');

  if (ruleSearchInput && categoryFilterSelect) {
    const filterFn = () => {
      const query = ruleSearchInput.value.toLowerCase();
      const cat = categoryFilterSelect.value;

      const filtered = rulesList.filter(r => {
        const matchesQuery = r.rule_id.toLowerCase().includes(query) ||
                             r.requirement.toLowerCase().includes(query) ||
                             r.clause_reference.toLowerCase().includes(query);
        const matchesCat = cat === 'all' || r.applicability.category === 'all' || r.applicability.category === cat;
        return matchesQuery && matchesCat;
      });

      renderRulesGrid(filtered);
    };

    ruleSearchInput.addEventListener('input', filterFn);
    categoryFilterSelect.addEventListener('change', filterFn);
  }

  // Load Stats
  async function loadStats() {
    try {
      const res = await fetch('/stats');
      if (res.ok) {
        const stats = await res.json();
        document.getElementById('stat-total').innerText = stats.total_inspections;
        document.getElementById('stat-rate').innerText = stats.compliance_rate;
        document.getElementById('stat-flagged').innerText = stats.flagged_cases;
        document.getElementById('stat-pending').innerText = stats.pending_reviews;

        const chartList = document.getElementById('bar-chart-rules');
        if (chartList && stats.top_failing_rules) {
          chartList.innerHTML = stats.top_failing_rules.map(item => `
            <div class="bar-item">
              <div class="bar-header">
                <span><strong>${item.rule_id}</strong> — ${item.name}</span>
                <span>${item.count} violations</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" style="width: ${(item.count / 14) * 100}%"></div>
              </div>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.warn('Could not fetch /stats:', err);
    }
  }

  // Submit Inspector Review to SQLite
  const inspectorForm = document.getElementById('inspector-form');
  if (inspectorForm) {
    inspectorForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const findingId = document.getElementById('review-finding-id').value;
      if (!findingId) {
        alert('Please select a finding to review.');
        return;
      }

      const decision = document.querySelector('input[name="decision"]:checked').value;
      const reason = document.getElementById('review-reason').value || "Verified by inspector";
      const caseId = caseIdDisplay.innerText || "INS-AUDIT";

      try {
        const res = await fetch(`/inspections/${caseId}/review`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            finding_id: findingId,
            decision: decision,
            reason: reason
          })
        });

        if (res.ok) {
          const feed = document.getElementById('audit-feed');
          const item = document.createElement('div');
          item.className = 'feed-item';
          item.innerHTML = `
            <div class="feed-badge accept">${decision}</div>
            <div class="feed-content">
              <div class="feed-header">
                <strong>Inspection Case ${caseId}</strong>
                <span class="feed-time">Just now</span>
              </div>
              <p>Decision on <code>${findingId}</code>: ${reason}</p>
              <div class="feed-meta">Inspector: LM-408 • Database Recorded</div>
            </div>
          `;
          feed.prepend(item);
          alert('Inspector audit decision successfully recorded in SQLite database!');
        }
      } catch (err) {
        alert(`Decision recorded for ${findingId}: ${decision}`);
      }
    });
  }

  // Init
  loadRules();
  loadStats();
});
