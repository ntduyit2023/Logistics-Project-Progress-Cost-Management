document.addEventListener("DOMContentLoaded", function() {
  
  // ==========================================
  // 1. ACCORDION LOGIC (RIGHT PANEL)
  // ==========================================
  const accBtns = document.querySelectorAll('.accordion-btn');
  accBtns.forEach(btn => {
    btn.addEventListener('click', function() {
      const content = this.nextElementSibling;
      const span = this.querySelector('span');
      if (content.classList.contains('show')) {
        content.classList.remove('show');
        span.textContent = '+';
      } else {
        // Optional: Close others
        document.querySelectorAll('.accordion-content').forEach(c => c.classList.remove('show'));
        document.querySelectorAll('.accordion-btn span').forEach(s => s.textContent = '+');
        
        content.classList.add('show');
        span.textContent = '-';
      }
    });
  });

  // ==========================================
  // 2. EVM LINE CHART (BOTTOM LEFT)
  // ==========================================
  const ctxEVM = document.getElementById('evmChart').getContext('2d');
  new Chart(ctxEVM, {
    type: 'line',
    data: {
      labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
      datasets: [
        { label: 'Planned Value (PV)', data: [2000, 5000, 12000, 20000, 33600], borderColor: '#c5c6c7', borderDash: [5, 5], tension: 0.4 },
        { label: 'Earned Value (EV)', data: [2000, 4800, 11500, 18000, 25000], borderColor: '#66fcf1', tension: 0.4 },
        { label: 'Actual Cost (AC)', data: [2100, 5200, 13000, 22000, 35000], borderColor: '#ff4b4b', tension: 0.4 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#c5c6c7', boxWidth: 12, font: {size: 11, family: 'Inter'} } } },
      scales: {
        x: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });

  // ==========================================
  // 3. RESOURCE HISTOGRAM (BOTTOM RIGHT)
  // ==========================================
  const ctxRes = document.getElementById('resChart').getContext('2d');
  new Chart(ctxRes, {
    type: 'bar',
    data: {
      labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
      datasets: [
        { label: 'Assigned: Dev_Comp', data: [1, 2, 3, 2, 1, 1, 0], backgroundColor: '#45a29e', borderRadius: 4 },
        { label: 'Capacity Limit (2)', data: [2, 2, 2, 2, 2, 2, 2], type: 'line', borderColor: '#ff4b4b', fill: false, borderWidth: 2, pointRadius: 0 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#c5c6c7', boxWidth: 12, font: {size: 11, family: 'Inter'} } } },
      scales: {
        x: { ticks: { color: '#888' }, grid: { display: false } },
        y: { ticks: { color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' }, min: 0, max: 4 }
      }
    }
  });

  // ==========================================
  // 4. RADAR CHART (RIGHT PANEL)
  // ==========================================
  const ctxRadar = document.getElementById('radarChart').getContext('2d');
  let radarChart = new Chart(ctxRadar, {
    type: 'radar',
    data: {
      labels: ['Time', 'Cost', 'Resources', 'Risk', 'EVM'],
      datasets: [{
        label: 'Feature Score',
        data: [0, 0, 0, 0, 0],
        backgroundColor: 'rgba(102, 252, 241, 0.2)',
        borderColor: '#66fcf1',
        pointBackgroundColor: '#fff',
        borderWidth: 1.5,
        pointRadius: 3
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255,255,255,0.1)' },
          grid: { color: 'rgba(255,255,255,0.1)' },
          pointLabels: { color: '#c5c6c7', font: {size: 10, family: 'Inter'} },
          ticks: { display: false, min: 0, max: 100 }
        }
      },
      plugins: { legend: { display: false } },
      animation: { duration: 600, easing: 'easeOutQuart' }
    }
  });

  // ==========================================
  // 5. CYTOSCAPE GRAPH
  // ==========================================
  if (typeof cytoscapeDagre !== 'undefined') {
    try { cytoscape.use(cytoscapeDagre); } catch(e) {}
  }

  const cy = cytoscape({
    container: document.getElementById('cy'),
    elements: graphElements, // from data.js
    
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#1f2833', 'border-width': 2, 'border-color': '#45a29e',
          'color': '#c5c6c7', 'label': 'data(label)', 'text-valign': 'center', 'text-halign': 'center',
          'font-family': 'Inter', 'font-size': '11px', 'width': '55px', 'height': '55px',
          'text-wrap': 'wrap', 'transition-property': 'background-color, border-color, transform', 'transition-duration': '0.3s'
        }
      },
      {
        selector: 'node:hover',
        style: { 'background-color': '#45a29e', 'color': '#0b0c10', 'cursor': 'pointer', 'transform': 'scale(1.1)' }
      },
      {
        selector: '.critical-node',
        style: {
          'border-color': '#ff4b4b', 'border-width': 4, 'background-color': 'rgba(255, 75, 75, 0.15)',
          'color': '#fff', 'shadow-blur': 25, 'shadow-color': '#ff4b4b', 'shadow-opacity': 0.8
        }
      },
      {
        selector: '.critical-node:hover',
        style: { 'background-color': '#ff4b4b', 'color': '#fff' }
      },
      {
        selector: 'edge',
        style: {
          'width': 2, 'line-color': '#45a29e', 'target-arrow-color': '#45a29e',
          'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'opacity': 0.5
        }
      },
      {
        selector: '.critical-edge',
        style: {
          'width': 4, 'line-color': '#ff4b4b', 'target-arrow-color': '#ff4b4b',
          'opacity': 1, 'shadow-blur': 15, 'shadow-color': '#ff4b4b', 'shadow-opacity': 0.9
        }
      }
    ],
    layout: { name: 'dagre', rankDir: 'LR', nodeSep: 50, edgeSep: 15, rankSep: 80 }
  });

  // ==========================================
  // 6. NODE TAP EVENT (UPDATE PANEL)
  // ==========================================
  const panel = document.getElementById('info-panel');
  const panelBody = document.getElementById('panel-body');
  
  cy.on('tap', 'node', function(evt) {
    const node = evt.target;
    const data = node.data();
    
    // Header
    document.getElementById('node-id').textContent = `Task ${data.id}`;
    document.getElementById('node-name').textContent = data.fullName;
    document.getElementById('node-critical-badge').style.display = data.isCritical ? 'inline-block' : 'none';
    
    // Accordion contents
    document.getElementById('val-duration').textContent = `${data.duration} Days`;
    document.getElementById('val-cost').textContent = (Math.floor(Math.random()*50) + 10) * 100; // Mock cost
    document.getElementById('val-opt').textContent = Math.max(1, data.duration - 2) + " Days";
    document.getElementById('val-pess').textContent = data.duration + 4 + " Days";
    document.getElementById('val-prob').textContent = data.isCritical ? 85 : 20;

    // Render resources
    const resContainer = document.getElementById('node-resources');
    resContainer.innerHTML = '';
    if (data.resources && Object.keys(data.resources).length > 0) {
      for (const [resName, amount] of Object.entries(data.resources)) {
        const span = document.createElement('span');
        span.className = 'resource-tag';
        span.textContent = `${resName}: ${amount}`;
        resContainer.appendChild(span);
      }
    } else {
      resContainer.innerHTML = '<span style="color:#888; font-size:12px;">No specific resources required</span>';
    }
    
    // Update Radar Chart
    const timeScore = Math.min(100, data.duration * 10);
    const resCount = data.resources ? Object.keys(data.resources).length : 0;
    const resScore = Math.min(100, resCount * 30);
    const riskScore = data.isCritical ? 95 : 25;
    const costScore = Math.min(100, 30 + (data.duration * 5));
    const evmScore = 70 + Math.floor(Math.random() * 25);
    
    radarChart.data.datasets[0].data = [timeScore, costScore, resScore, riskScore, evmScore];
    radarChart.data.datasets[0].borderColor = data.isCritical ? '#ff4b4b' : '#66fcf1';
    radarChart.data.datasets[0].backgroundColor = data.isCritical ? 'rgba(255, 75, 75, 0.25)' : 'rgba(102, 252, 241, 0.2)';
    radarChart.update();

    panelBody.style.display = 'block';
    panel.classList.add('active');
  });
  
  // Close panel on background tap
  cy.on('tap', function(evt) {
    if (evt.target === cy) {
      panel.classList.remove('active');
    }
  });

});
