/**
 * PatternNest Studio — Frontend Canvas 2D & Interactive Phase-Snap Engine
 */

class PatternNestApp {
  constructor() {
    this.canvas = document.getElementById('studioCanvas');
    this.ctx = this.canvas.getContext('2d');
    
    // Seam Inspector Canvas
    this.previewCanvas = document.getElementById('seamCloseUpCanvas');
    this.previewCtx = this.previewCanvas.getContext('2d');

    // State
    this.currentPresetId = 'plaid_oxford_shirt';
    this.presetData = null;
    this.markerData = null;
    this.validationData = null;
    this.viewMode = 'marker'; // 'marker' or 'garment'
    this.showPrintTexture = true;

    // Camera Transform (Pan & Zoom)
    this.camera = {
      x: 80,
      y: 60,
      scale: 0.45,
      isPanning: false,
      panStartX: 0,
      panStartY: 0,
    };

    // Piece Dragging & Snapping
    this.draggedPiece = null;
    this.dragOffset = { x: 0, y: 0 };
    this.isDraggingPiece = false;
    this.activeCollision = false;

    // Selected Contract for close-up inspection
    this.activeContract = null;

    this.initEventListeners();
    this.resizeCanvas();
    window.addEventListener('resize', () => this.resizeCanvas());

    // Load initial preset
    this.loadPreset(this.currentPresetId);

    // Render loop
    this.renderLoop();
  }

  // =========================================================================
  // Initialization & Network API
  // =========================================================================

  initEventListeners() {
    // Preset dropdown
    const selectPreset = document.getElementById('selectPreset');
    selectPreset.addEventListener('change', (e) => {
      this.currentPresetId = e.target.value;
      this.loadPreset(this.currentPresetId);
    });

    // View toggles
    document.getElementById('btnViewMarker').addEventListener('click', () => this.setViewMode('marker'));
    document.getElementById('btnViewGarment').addEventListener('click', () => this.setViewMode('garment'));

    // Texture toggle
    document.getElementById('btnToggleTexture').addEventListener('click', () => {
      this.showPrintTexture = !this.showPrintTexture;
      document.getElementById('btnToggleTexture').classList.toggle('active', this.showPrintTexture);
    });

    // Auto-Nest button
    document.getElementById('btnAutoNest').addEventListener('click', () => this.runAutoNest());

    // Export SVG
    document.getElementById('btnExportSvg').addEventListener('click', () => this.exportMarkerSvg());

    // Zoom controls
    document.getElementById('btnZoomIn').addEventListener('click', () => this.zoom(1.2));
    document.getElementById('btnZoomOut').addEventListener('click', () => this.zoom(0.83));
    document.getElementById('btnZoomFit').addEventListener('click', () => this.zoomFit());

    // Close preview modal
    document.getElementById('btnClosePreview').addEventListener('click', () => {
      document.getElementById('seamPreviewFloat').classList.remove('visible');
    });

    // Mouse canvas events for pan/zoom & piece drag
    this.canvas.addEventListener('mousedown', (e) => this.onMouseDown(e));
    window.addEventListener('mousemove', (e) => this.onMouseMove(e));
    window.addEventListener('mouseup', (e) => this.onMouseUp(e));
    this.canvas.addEventListener('wheel', (e) => this.onWheel(e), { passive: false });

    // Live parameter changes
    ['inputRepeatW', 'inputRepeatH', 'inputRollW', 'inputBuffer'].forEach(id => {
      document.getElementById(id).addEventListener('change', () => {
        if (this.presetData) {
          this.presetData.metadata.repeat_width_mm = parseFloat(document.getElementById('inputRepeatW').value);
          this.presetData.metadata.repeat_height_mm = parseFloat(document.getElementById('inputRepeatH').value);
          this.presetData.metadata.roll_width_mm = parseFloat(document.getElementById('inputRollW').value);
        }
      });
    });
  }

  resizeCanvas() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width * window.devicePixelRatio;
    this.canvas.height = rect.height * window.devicePixelRatio;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }

  async loadPreset(presetId) {
    try {
      const resp = await fetch(`/api/preset?id=${presetId}`);
      if (!resp.ok) throw new Error('Failed to fetch preset');
      this.presetData = await resp.json();

      // Update inputs
      const meta = this.presetData.metadata;
      document.getElementById('inputRepeatW').value = meta.repeat_width_mm;
      document.getElementById('inputRepeatH').value = meta.repeat_height_mm;
      document.getElementById('inputRollW').value = meta.roll_width_mm;
      document.getElementById('badgePieceTotal').textContent = `${this.presetData.pieces.length} Pieces`;

      this.populatePiecesList();
      this.populateContractsList();

      // Automatically nest initially
      await this.runAutoNest();
      this.zoomFit();
    } catch (err) {
      console.error(err);
    }
  }

  async runAutoNest() {
    const btn = document.getElementById('btnAutoNest');
    btn.disabled = true;
    btn.innerHTML = `<span class="icon">⌛</span> Solving...`;

    try {
      const payload = {
        preset_id: this.currentPresetId,
        repeat_width_mm: parseFloat(document.getElementById('inputRepeatW').value),
        repeat_height_mm: parseFloat(document.getElementById('inputRepeatH').value),
        roll_width_mm: parseFloat(document.getElementById('inputRollW').value),
        buffer_mm: parseFloat(document.getElementById('inputBuffer').value),
        optimize: true,
      };

      const resp = await fetch('/api/nest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!resp.ok) throw new Error('Nesting request failed');
      const data = await resp.json();

      this.markerData = data.marker;
      this.validationData = data.validation;

      this.updateTelemetry();
      this.updateValidationUI();
    } catch (err) {
      console.error(err);
      alert('Nesting error: ' + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<span class="icon">⚡</span> Auto-Nest`;
    }
  }

  async validateCurrentPlacements() {
    if (!this.markerData) return;
    const placements = {};
    for (const p of this.markerData.pieces) {
      placements[p.id] = [p.x, p.y];
    }

    try {
      const payload = {
        preset_id: this.currentPresetId,
        placements: placements,
        repeat_width_mm: parseFloat(document.getElementById('inputRepeatW').value),
        repeat_height_mm: parseFloat(document.getElementById('inputRepeatH').value),
      };

      const resp = await fetch('/api/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (resp.ok) {
        this.validationData = await resp.json();
        this.updateValidationUI();
      }
    } catch (err) {
      console.error(err);
    }
  }

  // =========================================================================
  // Telemetry & UI Updates
  // =========================================================================

  updateTelemetry() {
    if (!this.markerData) return;
    document.getElementById('statYield').textContent = `${this.markerData.utilization_pct.toFixed(1)}%`;
    document.getElementById('statLength').textContent = `${(this.markerData.marker_length_mm / 1000).toFixed(2)} m`;
    document.getElementById('statSolveTime').textContent = `${Math.round(this.markerData.solve_duration_ms)} ms`;
    document.getElementById('statPieceCount').textContent = `${this.markerData.pieces.length} / ${this.presetData.pieces.length}`;
  }

  updateValidationUI() {
    if (!this.validationData) return;
    const overallBadge = document.getElementById('badgeSeamOverall');
    const snapIndicator = document.getElementById('txtSnapStatus');
    const statusDot = document.querySelector('.status-dot');

    if (this.validationData.all_passed) {
      overallBadge.className = 'badge badge-success';
      overallBadge.textContent = '✓ 100% PHASE LOCKED';
      snapIndicator.textContent = `Phase Snap: Active (Δ = 0.00mm)`;
      statusDot.className = 'status-dot';
    } else {
      overallBadge.className = 'badge badge-warning';
      overallBadge.textContent = `⚠ MISMATCH (${this.validationData.max_mismatch_mm}mm)`;
      snapIndicator.textContent = `Phase Mismatch: ${this.validationData.max_mismatch_mm}mm`;
      statusDot.className = 'status-dot warning';
    }

    this.populateContractsList();
  }

  populatePiecesList() {
    const list = document.getElementById('piecesList');
    list.innerHTML = '';
    if (!this.presetData) return;

    this.presetData.pieces.forEach(p => {
      const row = document.createElement('div');
      row.className = 'piece-row';
      row.innerHTML = `
        <div class="piece-left">
          <span class="piece-color-pip" style="background-color: ${p.color_tag}"></span>
          <span class="piece-name">${p.name}</span>
        </div>
        <div class="piece-metrics">
          <span>${Math.round(p.bounds[2] - p.bounds[0])}×${Math.round(p.bounds[3] - p.bounds[1])}mm</span>
        </div>
      `;
      list.appendChild(row);
    });
  }

  populateContractsList() {
    const list = document.getElementById('contractsList');
    list.innerHTML = '';
    if (!this.presetData) return;

    const evals = this.validationData ? this.validationData.evaluations : [];

    this.presetData.contracts.forEach(contract => {
      const evalInfo = evals.find(e => e.contract_id === contract.id);
      const isMismatch = evalInfo && !evalInfo.passed;
      const mismatchVal = evalInfo ? `${evalInfo.mismatch_mm.toFixed(2)} mm` : '0.00 mm';

      const card = document.createElement('div');
      card.className = `contract-card ${isMismatch ? 'mismatch' : ''}`;
      card.innerHTML = `
        <div class="contract-top">
          <span class="contract-name">${contract.name}</span>
          <span class="contract-delta ${isMismatch ? 'mismatch' : ''}">${mismatchVal}</span>
        </div>
        <div class="contract-desc">${contract.description}</div>
      `;
      card.addEventListener('click', () => this.inspectSeam(contract));
      list.appendChild(card);
    });
  }

  inspectSeam(contract) {
    this.activeContract = contract;
    const card = document.getElementById('seamPreviewFloat');
    card.classList.add('visible');
    document.getElementById('previewTitle').textContent = `Seam Miter: ${contract.name}`;
    this.renderSeamCloseUp();
  }

  renderSeamCloseUp() {
    if (!this.activeContract || !this.markerData) return;
    const pCtx = this.previewCtx;
    const w = this.previewCanvas.width;
    const h = this.previewCanvas.height;

    pCtx.clearRect(0, 0, w, h);

    // Draw background fabric repeat
    const repW = parseFloat(document.getElementById('inputRepeatW').value);
    const repH = parseFloat(document.getElementById('inputRepeatH').value);
    const scale = 0.8;

    pCtx.save();
    pCtx.translate(w / 2, h / 2);
    pCtx.scale(scale, scale);

    // Draw folded seam intersection line
    pCtx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    pCtx.lineWidth = 1;
    pCtx.beginPath();
    pCtx.moveTo(0, -h);
    pCtx.lineTo(0, h);
    pCtx.stroke();

    // Render left piece and right piece meeting at center
    const pieceA = this.markerData.pieces.find(p => p.id === this.activeContract.piece_a_id);
    const pieceB = this.markerData.pieces.find(p => p.id === this.activeContract.piece_b_id);

    if (pieceA && pieceB) {
      // Left side: Piece A print
      pCtx.save();
      pCtx.rect(-w, -h, w, 2 * h);
      pCtx.clip();
      this.drawFabricTile(pCtx, -pieceA.actual_phase.u, -pieceA.actual_phase.v, repW, repH, w, h);
      pCtx.restore();

      // Right side: Piece B print
      pCtx.save();
      pCtx.rect(0, -h, w, 2 * h);
      pCtx.clip();
      this.drawFabricTile(pCtx, -pieceB.actual_phase.u, -pieceB.actual_phase.v, repW, repH, w, h);
      pCtx.restore();

      // Golden seam line
      pCtx.strokeStyle = '#e5a93c';
      pCtx.lineWidth = 2.5;
      pCtx.setLineDash([6, 4]);
      pCtx.beginPath();
      pCtx.moveTo(0, -h);
      pCtx.lineTo(0, h);
      pCtx.stroke();
      pCtx.setLineDash([]);
    }

    pCtx.restore();

    // Text metric
    const evalInfo = this.validationData?.evaluations?.find(e => e.contract_id === this.activeContract.id);
    const mismatch = evalInfo ? evalInfo.mismatch_mm : 0.0;
    const msg = mismatch === 0.0 ? '✓ Exact 1:1 Phase Match (0.00 mm Mismatch)' : `⚠ Seam Offset: ${mismatch.toFixed(2)} mm`;
    document.getElementById('previewMetric').textContent = msg;
    document.getElementById('previewMetric').style.color = mismatch === 0.0 ? '#10b981' : '#ef4444';
  }

  // =========================================================================
  // Canvas Interaction & Phase-Snap Drag
  // =========================================================================

  screenToWorld(screenX, screenY) {
    return {
      x: (screenX - this.camera.x) / this.camera.scale,
      y: (screenY - this.camera.y) / this.camera.scale,
    };
  }

  worldToScreen(worldX, worldY) {
    return {
      x: worldX * this.camera.scale + this.camera.x,
      y: worldY * this.camera.scale + this.camera.y,
    };
  }

  onMouseDown(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const world = this.screenToWorld(mouseX, mouseY);

    if (this.viewMode === 'marker' && this.markerData) {
      // Test if user clicked inside any piece to drag
      for (let i = this.markerData.pieces.length - 1; i >= 0; i--) {
        const p = this.markerData.pieces[i];
        if (this.pointInPolygon(world.x, world.y, p.placed_vertices)) {
          this.draggedPiece = p;
          this.isDraggingPiece = true;
          this.dragOffset = { x: world.x - p.x, y: world.y - p.y };
          this.canvas.classList.add('dragging');
          return;
        }
      }
    }

    // Otherwise start panning
    this.camera.isPanning = true;
    this.camera.panStartX = mouseX - this.camera.x;
    this.camera.panStartY = mouseY - this.camera.y;
    this.canvas.classList.add('dragging');
  }

  onMouseMove(e) {
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    if (this.isDraggingPiece && this.draggedPiece) {
      const world = this.screenToWorld(mouseX, mouseY);
      const rawX = world.x - this.dragOffset.x;
      const rawY = world.y - this.dragOffset.y;

      // Magnetic Phase Snap: snap strictly to nearest valid repeat lattice node
      const repW = parseFloat(document.getElementById('inputRepeatW').value);
      const repH = parseFloat(document.getElementById('inputRepeatH').value);
      const targetU = this.draggedPiece.design_phase.u;
      const targetV = this.draggedPiece.design_phase.v;

      const nx = Math.round((rawX - targetU) / repW);
      const ny = Math.round((rawY - targetV) / repH);

      const snappedX = targetU + nx * repW;
      const snappedY = targetV + ny * repH;

      // Update piece coordinates
      const dx = snappedX - this.draggedPiece.x;
      const dy = snappedY - this.draggedPiece.y;
      this.draggedPiece.x = snappedX;
      this.draggedPiece.y = snappedY;

      // Update actual vertices
      this.draggedPiece.placed_vertices = this.draggedPiece.placed_vertices.map(pt => [pt[0] + dx, pt[1] + dy]);
      this.draggedPiece.bounds = [
        this.draggedPiece.bounds[0] + dx,
        this.draggedPiece.bounds[1] + dy,
        this.draggedPiece.bounds[2] + dx,
        this.draggedPiece.bounds[3] + dy,
      ];
      this.draggedPiece.actual_phase = {
        u: Math.round(snappedX % repW),
        v: Math.round(snappedY % repH),
      };

      // Check collision with other pieces
      this.activeCollision = this.checkPieceCollision(this.draggedPiece);
      return;
    }

    if (this.camera.isPanning) {
      this.camera.x = mouseX - this.camera.panStartX;
      this.camera.y = mouseY - this.camera.panStartY;
    }
  }

  onMouseUp() {
    if (this.isDraggingPiece) {
      this.isDraggingPiece = false;
      this.draggedPiece = null;
      this.canvas.classList.remove('dragging');
      this.validateCurrentPlacements();
      if (this.activeContract) this.renderSeamCloseUp();
      return;
    }

    if (this.camera.isPanning) {
      this.camera.isPanning = false;
      this.canvas.classList.remove('dragging');
    }
  }

  onWheel(e) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
    const rect = this.canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const worldBefore = this.screenToWorld(mouseX, mouseY);
    this.camera.scale *= zoomFactor;
    this.camera.scale = Math.max(0.08, Math.min(3.5, this.camera.scale));

    this.camera.x = mouseX - worldBefore.x * this.camera.scale;
    this.camera.y = mouseY - worldBefore.y * this.camera.scale;
    document.getElementById('txtZoomLevel').textContent = `${Math.round(this.camera.scale * 100)}%`;
  }

  zoom(factor) {
    const cx = this.canvas.width / (2 * window.devicePixelRatio);
    const cy = this.canvas.height / (2 * window.devicePixelRatio);
    const world = this.screenToWorld(cx, cy);
    this.camera.scale *= factor;
    this.camera.scale = Math.max(0.08, Math.min(3.5, this.camera.scale));
    this.camera.x = cx - world.x * this.camera.scale;
    this.camera.y = cy - world.y * this.camera.scale;
    document.getElementById('txtZoomLevel').textContent = `${Math.round(this.camera.scale * 100)}%`;
  }

  zoomFit() {
    if (!this.markerData) return;
    const rollW = this.markerData.roll_width_mm;
    const markerH = this.markerData.marker_length_mm;
    const canvasW = this.canvas.width / window.devicePixelRatio;
    const canvasH = this.canvas.height / window.devicePixelRatio;

    const scaleX = (canvasW - 80) / rollW;
    const scaleY = (canvasH - 80) / markerH;
    this.camera.scale = Math.min(scaleX, scaleY, 0.8);
    this.camera.x = (canvasW - rollW * this.camera.scale) / 2;
    this.camera.y = 40;
    document.getElementById('txtZoomLevel').textContent = `${Math.round(this.camera.scale * 100)}%`;
  }

  setViewMode(mode) {
    this.viewMode = mode;
    document.getElementById('btnViewMarker').classList.toggle('active', mode === 'marker');
    document.getElementById('btnViewGarment').classList.toggle('active', mode === 'garment');
  }

  // =========================================================================
  // Canvas Rendering Loop
  // =========================================================================

  renderLoop() {
    this.render();
    requestAnimationFrame(() => this.renderLoop());
  }

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width / window.devicePixelRatio;
    const h = this.canvas.height / window.devicePixelRatio;

    ctx.clearRect(0, 0, w, h);

    ctx.save();
    ctx.translate(this.camera.x, this.camera.y);
    ctx.scale(this.camera.scale, this.camera.scale);

    if (this.viewMode === 'marker') {
      this.renderLayMarker(ctx);
    } else {
      this.renderGarmentDesign(ctx);
    }

    ctx.restore();
  }

  renderLayMarker(ctx) {
    if (!this.markerData || !this.presetData) return;
    const rollW = this.markerData.roll_width_mm;
    const markerH = this.markerData.marker_length_mm;
    const repW = parseFloat(document.getElementById('inputRepeatW').value);
    const repH = parseFloat(document.getElementById('inputRepeatH').value);

    // 1. Draw Fabric Roll Bed
    ctx.fillStyle = '#0a101d';
    ctx.fillRect(0, 0, rollW, markerH);

    // 2. Draw Repeating Print Background if enabled
    if (this.showPrintTexture) {
      ctx.save();
      ctx.rect(0, 0, rollW, markerH);
      ctx.clip();
      this.drawFabricTile(ctx, 0, 0, repW, repH, rollW, markerH);
      ctx.restore();
    }

    // 3. Roll Selvedge Boundaries & Metric Grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 2 / this.camera.scale;
    ctx.strokeRect(0, 0, rollW, markerH);

    // Roll Width and Length annotations
    ctx.fillStyle = '#64748b';
    ctx.font = `${14 / this.camera.scale}px var(--font-mono)`;
    ctx.fillText(`Roll Width: ${rollW} mm`, 10, -10 / this.camera.scale);
    ctx.fillText(`Marker Length: ${Math.round(markerH)} mm`, rollW + 15, markerH / 2);

    // Repeat Grid Guides (subtle dashed lines)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    ctx.lineWidth = 1 / this.camera.scale;
    ctx.setLineDash([4 / this.camera.scale, 4 / this.camera.scale]);
    for (let x = 0; x <= rollW; x += repW) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, markerH);
      ctx.stroke();
    }
    for (let y = 0; y <= markerH; y += repH) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(rollW, y);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // 4. Render Garment Pieces on Lay Table
    this.markerData.pieces.forEach(p => {
      this.drawPlacedPiece(ctx, p);
    });
  }

  drawPlacedPiece(ctx, p) {
    const isDragged = this.draggedPiece && this.draggedPiece.id === p.id;
    const isColliding = isDragged && this.activeCollision;

    ctx.save();
    ctx.beginPath();
    p.placed_vertices.forEach((pt, idx) => {
      if (idx === 0) ctx.moveTo(pt[0], pt[1]);
      else ctx.lineTo(pt[0], pt[1]);
    });
    ctx.closePath();

    // Piece body fill
    if (isColliding) {
      ctx.fillStyle = 'rgba(239, 68, 68, 0.4)';
    } else if (isDragged) {
      ctx.fillStyle = 'rgba(16, 185, 129, 0.35)';
    } else {
      ctx.fillStyle = 'rgba(15, 23, 42, 0.65)';
    }
    ctx.fill();

    // Piece cutting border
    ctx.lineWidth = (isDragged ? 3.5 : 2.0) / this.camera.scale;
    ctx.strokeStyle = isColliding ? '#ef4444' : (isDragged ? '#10b981' : p.color_tag);
    ctx.stroke();

    // Seam allowance buffer outline
    const buf = parseFloat(document.getElementById('inputBuffer').value);
    if (buf > 0 && !isDragged) {
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
      ctx.lineWidth = 1 / this.camera.scale;
      ctx.setLineDash([3 / this.camera.scale, 3 / this.camera.scale]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Piece Label & Grainline
    const cx = (p.bounds[0] + p.bounds[2]) / 2;
    const cy = (p.bounds[1] + p.bounds[3]) / 2;

    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${12 / this.camera.scale}px var(--font-sans)`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(p.name, cx, cy);

    ctx.font = `${9 / this.camera.scale}px var(--font-mono)`;
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(`Δu: ${p.actual_phase.u}mm, Δv: ${p.actual_phase.v}mm`, cx, cy + 14 / this.camera.scale);

    // Grainline indicator (vertical arrow)
    ctx.strokeStyle = p.color_tag;
    ctx.lineWidth = 1.5 / this.camera.scale;
    ctx.beginPath();
    ctx.moveTo(cx, cy - 35 / this.camera.scale);
    ctx.lineTo(cx, cy - 15 / this.camera.scale);
    ctx.moveTo(cx, cy + 25 / this.camera.scale);
    ctx.lineTo(cx, cy + 45 / this.camera.scale);
    ctx.stroke();

    ctx.restore();
  }

  renderGarmentDesign(ctx) {
    if (!this.presetData) return;
    const repW = parseFloat(document.getElementById('inputRepeatW').value);
    const repH = parseFloat(document.getElementById('inputRepeatH').value);

    ctx.fillStyle = '#64748b';
    ctx.font = `${14 / this.camera.scale}px var(--font-mono)`;
    ctx.fillText(`Master Assembled Garment — Target Design Seam Match`, 0, -20 / this.camera.scale);

    // Draw background texture behind assembled garment
    ctx.save();
    ctx.translate(100, 40);

    // Draw pieces positioned in their sewn alignment
    this.presetData.pieces.forEach(piece => {
      ctx.save();
      ctx.beginPath();
      piece.vertices.forEach((pt, idx) => {
        if (idx === 0) ctx.moveTo(pt[0], pt[1]);
        else ctx.lineTo(pt[0], pt[1]);
      });
      ctx.closePath();

      // Clip and render continuous print pattern
      ctx.save();
      ctx.clip();
      this.drawFabricTile(ctx, -piece.design_phase.u, -piece.design_phase.v, repW, repH, 600, 800);
      ctx.restore();

      ctx.strokeStyle = '#e5a93c';
      ctx.lineWidth = 2 / this.camera.scale;
      ctx.stroke();

      // Label
      const cx = (piece.bounds[0] + piece.bounds[2]) / 2;
      const cy = (piece.bounds[1] + piece.bounds[3]) / 2;
      ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(cx - 50, cy - 12, 100, 24);
      ctx.fillStyle = '#ffffff';
      ctx.font = `bold ${11 / this.camera.scale}px var(--font-sans)`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(piece.name, cx, cy);

      ctx.restore();
    });

    ctx.restore();
  }

  // =========================================================================
  // Procedural Fabric Pattern Renderer
  // =========================================================================

  drawFabricTile(ctx, originX, originY, wRep, hRep, areaW, areaH) {
    const type = this.presetData?.metadata?.repeat_type || 'plaid';

    if (type === 'plaid') {
      this.drawPlaidPattern(ctx, originX, originY, wRep, hRep, areaW, areaH);
    } else if (type === 'horizontal_stripe') {
      this.drawStripePattern(ctx, originX, originY, wRep, hRep, areaW, areaH);
    } else {
      this.drawFloralPattern(ctx, originX, originY, wRep, hRep, areaW, areaH);
    }
  }

  drawPlaidPattern(ctx, ox, oy, wRep, hRep, areaW, areaH) {
    // 1. Base navy
    ctx.fillStyle = '#0f3a57';
    ctx.fillRect(0, 0, areaW, areaH);

    const startX = Math.floor(-ox / wRep) * wRep + ox;
    const startY = Math.floor(-oy / hRep) * hRep + oy;

    // Horizontal red bands
    ctx.fillStyle = 'rgba(220, 38, 38, 0.75)';
    for (let y = startY; y < areaH + hRep; y += hRep) {
      ctx.fillRect(0, y + hRep * 0.25, areaW, hRep * 0.22);
    }

    // Vertical red bands
    for (let x = startX; x < areaW + wRep; x += wRep) {
      ctx.fillRect(x + wRep * 0.25, 0, wRep * 0.22, areaH);
    }

    // Yellow accent stripes
    ctx.fillStyle = 'rgba(229, 169, 60, 0.85)';
    for (let y = startY; y < areaH + hRep; y += hRep) {
      ctx.fillRect(0, y + hRep * 0.7, areaW, hRep * 0.06);
    }
    for (let x = startX; x < areaW + wRep; x += wRep) {
      ctx.fillRect(x + wRep * 0.7, 0, wRep * 0.06, areaH);
    }

    // White fine overcheck
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    for (let y = startY; y < areaH + hRep; y += hRep) {
      ctx.moveTo(0, y);
      ctx.lineTo(areaW, y);
    }
    for (let x = startX; x < areaW + wRep; x += wRep) {
      ctx.moveTo(x, 0);
      ctx.lineTo(x, areaH);
    }
    ctx.stroke();
  }

  drawStripePattern(ctx, ox, oy, wRep, hRep, areaW, areaH) {
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, areaW, areaH);

    const startY = Math.floor(-oy / hRep) * hRep + oy;
    ctx.fillStyle = '#1e3a8a';
    for (let y = startY; y < areaH + hRep; y += hRep) {
      ctx.fillRect(0, y, areaW, hRep * 0.5);
    }
  }

  drawFloralPattern(ctx, ox, oy, wRep, hRep, areaW, areaH) {
    ctx.fillStyle = '#141e24';
    ctx.fillRect(0, 0, areaW, areaH);

    const startX = Math.floor(-ox / wRep) * wRep + ox;
    const startY = Math.floor(-oy / hRep) * hRep + oy;

    for (let x = startX; x < areaW + wRep; x += wRep) {
      for (let y = startY; y < areaH + hRep; y += hRep) {
        // Emerald leaf
        ctx.fillStyle = 'rgba(16, 185, 129, 0.6)';
        ctx.beginPath();
        ctx.ellipse(x + wRep * 0.4, y + hRep * 0.45, wRep * 0.22, hRep * 0.1, Math.PI / 4, 0, 2 * Math.PI);
        ctx.fill();

        // Rose blossom
        ctx.fillStyle = 'rgba(244, 63, 94, 0.85)';
        ctx.beginPath();
        ctx.arc(x + wRep * 0.6, y + hRep * 0.55, Math.min(wRep, hRep) * 0.18, 0, 2 * Math.PI);
        ctx.fill();

        ctx.fillStyle = '#fde047';
        ctx.beginPath();
        ctx.arc(x + wRep * 0.6, y + hRep * 0.55, Math.min(wRep, hRep) * 0.05, 0, 2 * Math.PI);
        ctx.fill();
      }
    }
  }

  // =========================================================================
  // Collision & Geometry Helpers
  // =========================================================================

  pointInPolygon(x, y, poly) {
    let inside = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const xi = poly[i][0], yi = poly[i][1];
      const xj = poly[j][0], yj = poly[j][1];
      const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }

  checkPieceCollision(targetPiece) {
    const rollW = this.markerData.roll_width_mm;
    const buf = parseFloat(document.getElementById('inputBuffer').value);

    // Roll boundary bounds
    if (targetPiece.bounds[0] < 10 || targetPiece.bounds[2] > rollW - 10 || targetPiece.bounds[1] < 10) {
      return true;
    }

    // Piece-piece bounding box check
    for (const other of this.markerData.pieces) {
      if (other.id === targetPiece.id) continue;
      if (this.bboxesIntersect(targetPiece.bounds, other.bounds, buf)) {
        return true;
      }
    }
    return false;
  }

  bboxesIntersect(b1, b2, margin = 0) {
    return !(
      b1[2] + margin < b2[0] - margin ||
      b2[2] + margin < b1[0] - margin ||
      b1[3] + margin < b2[1] - margin ||
      b2[3] + margin < b1[1] - margin
    );
  }

  exportMarkerSvg() {
    if (!this.markerData) return;
    const rollW = this.markerData.roll_width_mm;
    const markerH = this.markerData.marker_length_mm;

    let svg = `<?xml version="1.0" standalone="no"?>\n`;
    svg += `<svg width="${rollW}mm" height="${markerH}mm" viewBox="0 0 ${rollW} ${markerH}" xmlns="http://www.w3.org/2000/svg">\n`;
    svg += `  <rect width="${rollW}" height="${markerH}" fill="#0f172a" />\n`;

    this.markerData.pieces.forEach(p => {
      const pts = p.placed_vertices.map(pt => `${pt[0]},${pt[1]}`).join(' ');
      svg += `  <polygon points="${pts}" fill="${p.color_tag}" fill-opacity="0.25" stroke="${p.color_tag}" stroke-width="2" />\n`;
      const cx = (p.bounds[0] + p.bounds[2]) / 2;
      const cy = (p.bounds[1] + p.bounds[3]) / 2;
      svg += `  <text x="${cx}" y="${cy}" fill="#ffffff" font-family="sans-serif" font-size="14" text-anchor="middle">${p.name}</text>\n`;
    });

    svg += `</svg>`;

    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `marker_${this.currentPresetId}_${Math.round(markerH)}mm.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }
}

// Start app on DOM load
window.addEventListener('DOMContentLoaded', () => {
  window.app = new PatternNestApp();
});
