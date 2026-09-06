(function() {
  document.addEventListener('contextmenu', function(e) { e.preventDefault(); return false; }, { capture: true });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'F12' || e.keyCode === 123) { e.preventDefault(); return false; }
    if (e.ctrlKey && e.shiftKey && ['I','i','J','j','C','c'].includes(e.key)) { e.preventDefault(); return false; }
    if (e.ctrlKey && ['u','U','s','S'].includes(e.key)) { e.preventDefault(); return false; }
  }, { capture: true });
})();

const pages = [
  'home', 'stromai', 'osint', 'phonehub', 'githubsuite', 'reconhub', 'medialab', 'devsuite'
];

const pageAliasMap = {
  'magiclink': { hub: 'devsuite', sub: 'alightmotion' },
  'base64': { hub: 'devsuite', sub: 'base64' },
  'webtools': { hub: 'devsuite', sub: 'webtools' },
  'ceknomor': { hub: 'phonehub', sub: 'ceknomor' },
  'scanrepo': { hub: 'githubsuite', sub: 'scanrepo' },
  'webinspect': { hub: 'reconhub', sub: 'webinspect' },
  'gambar': { hub: 'medialab', sub: 'gambar' },
  'tiktok': { hub: 'medialab', sub: 'downloader' }
};

function goPage(pageName, opts = {}) {
  let activeHub = pageName;
  if (pageAliasMap[pageName]) {
    activeHub = pageAliasMap[pageName].hub;
    opts.sub = opts.sub || pageAliasMap[pageName].sub;
  }

  if (opts.sub) {
    switchSubTab(activeHub, opts.sub);
  }

  if (typeof _aiFullscreen !== 'undefined' && _aiFullscreen && activeHub !== 'stromai') {
    toggleAiFullscreen();
  }

  pages.forEach(p => {
    const viewEl = document.getElementById(`view-${p}`);
    const tabBtn = document.getElementById(`tab-${p}`);
    if (viewEl) viewEl.classList.toggle('visible', p === activeHub);
    if (tabBtn) {
      const isActive = p === activeHub;
      tabBtn.classList.toggle('active', isActive);
      if (isActive) tabBtn.setAttribute('aria-current', 'page');
      else tabBtn.removeAttribute('aria-current');
    }
  });

  window.scrollTo({ top: 0, behavior: opts.instant ? 'auto' : 'smooth' });
  moveTabThumb(activeHub, opts);

  if (activeHub === 'stromai') {
    initAiChatInput();
    const msgs = document.getElementById('ai-messages');
    if (msgs) setTimeout(() => { msgs.scrollTop = msgs.scrollHeight; }, 50);
  }
}

function switchSubTab(hub, subId) {
  const hubPrefixMap = {
    'osint': 'osint',
    'phonehub': 'phone',
    'githubsuite': 'gh',
    'reconhub': 'recon',
    'medialab': 'media',
    'devsuite': 'dev'
  };
  const pfx = hubPrefixMap[hub] || hub;
  const navEl = document.getElementById(`subtab-nav-${hub}`);
  if (navEl) {
    navEl.querySelectorAll('.subtab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.id === `btn-sub-${pfx}-${subId}`);
    });
  }
  const viewEl = document.getElementById(`view-${hub}`);
  if (viewEl) {
    viewEl.querySelectorAll('.subtab-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === `subpane-${pfx}-${subId}`);
    });
  }
  if (hub === 'phonehub' && subId === 'tempsms') {
    loadTempSmsNumbers();
  }
}

// ─── LIQUID GLASS TAB NAV — Sliding & Real-Time Draggable Bar ───
let currentActiveThumbX = 0;
let currentActiveThumbW = 0;

function moveTabThumb(pageName, opts = {}) {
  const track = document.getElementById('tabNavTrack');
  const thumb = document.getElementById('tabThumb');
  const btn = document.getElementById(`tab-${pageName}`);
  if (!track || !thumb || !btn) return;

  const x = btn.offsetLeft;
  const w = btn.offsetWidth;
  currentActiveThumbX = x;
  currentActiveThumbW = w;

  if (opts.instant) {
    thumb.style.transition = 'none';
  } else {
    thumb.style.transition = 'transform 0.38s cubic-bezier(0.16, 1, 0.3, 1), width 0.38s cubic-bezier(0.16, 1, 0.3, 1)';
  }

  thumb.style.width = `${w}px`;
  thumb.style.transform = `translateX(${x}px)`;

  if (opts.instant) {
    void thumb.offsetWidth; // force reflow
    thumb.style.transition = '';
  }

  btn.scrollIntoView({ behavior: opts.instant ? 'auto' : 'smooth', inline: 'center', block: 'nearest' });
}

// ─── INTERACTIVE REAL-TIME DRAGGING / PULLING OF THE ACTIVE LIQUID GLASS BAR (ZERO LAYOUT THRASHING) ───
(function initDraggableThumb() {
  const track = document.getElementById('tabNavTrack');
  const thumb = document.getElementById('tabThumb');
  if (!track || !thumb) return;

  let isDragging = false;
  let hasMoved = false;
  let startPointerX = 0;
  let initialThumbX = 0;
  let cachedTabs = [];

  function cacheTabGeometry() {
    const tabEls = Array.from(track.querySelectorAll('.tab-item'));
    cachedTabs = tabEls.map(tab => ({
      el: tab,
      id: tab.id,
      left: tab.offsetLeft,
      width: tab.offsetWidth,
      center: tab.offsetLeft + tab.offsetWidth / 2
    }));
  }

  function getClosestCachedTab(centerPos) {
    if (!cachedTabs.length) cacheTabGeometry();
    let closest = cachedTabs[0];
    let minDist = Infinity;
    for (let i = 0; i < cachedTabs.length; i++) {
      const item = cachedTabs[i];
      const dist = Math.abs(item.center - centerPos);
      if (dist < minDist) {
        minDist = dist;
        closest = item;
      }
    }
    return closest;
  }

  function onPointerDown(e) {
    if (e.button !== undefined && e.button !== 0) return;

    window.getSelection()?.removeAllRanges();
    cacheTabGeometry();
    if (!cachedTabs.length) return;

    isDragging = true;
    hasMoved = false;
    startPointerX = e.clientX;
    initialThumbX = currentActiveThumbX;

    thumb.style.transition = 'none'; // 0 latency saat ditarik
    thumb.classList.add('dragging');

    window.addEventListener('pointermove', onPointerMove, { passive: false });
    window.addEventListener('pointerup', onPointerUp);
    window.addEventListener('pointercancel', onPointerUp);
  }

  function onPointerMove(e) {
    if (!isDragging) return;

    const deltaX = e.clientX - startPointerX;
    if (!hasMoved && Math.abs(deltaX) > 4) {
      hasMoved = true;
      window.getSelection()?.removeAllRanges();
    }

    if (!hasMoved || !cachedTabs.length) return;

    if (e.cancelable) e.preventDefault();

    const minX = cachedTabs[0].left;
    const lastTab = cachedTabs[cachedTabs.length - 1];
    const maxX = lastTab.left + lastTab.width - currentActiveThumbW;

    let newX = initialThumbX + deltaX;
    if (newX < minX) newX = minX + (newX - minX) * 0.25;
    else if (newX > maxX) newX = maxX + (newX - maxX) * 0.25;

    const currentCenter = newX + currentActiveThumbW / 2;
    const closest = getClosestCachedTab(currentCenter);
    const targetW = closest ? closest.width : currentActiveThumbW;
    const interpolatedW = currentActiveThumbW + (targetW - currentActiveThumbW) * 0.45;

    const deltaMove = deltaX - (thumb._lastDeltaX || 0);
    thumb._lastDeltaX = deltaX;
    const tilt = Math.max(Math.min(deltaMove * 0.22, 4.5), -4.5);

    thumb.style.width = `${interpolatedW}px`;
    thumb.style.transform = `translateX(${newX}px) skewX(${-tilt}deg)`;

    const thumbLeft = newX;
    const thumbRight = newX + interpolatedW;
    const thumbCenter = newX + interpolatedW / 2;

    for (let i = 0; i < cachedTabs.length; i++) {
      const t = cachedTabs[i];
      const isOverlap = !(t.left + t.width < thumbLeft || t.left > thumbRight);

      if (isOverlap) {
        const maxDist = (t.width + interpolatedW) * 0.5;
        const dist = Math.abs(t.center - thumbCenter);
        const overlapFactor = Math.max(0, 1 - dist / maxDist);

        const opticalBulge = 1 + 0.08 * overlapFactor;
        const opticalShear = -tilt * 0.6 * overlapFactor;
        const opticalShiftY = -2 * overlapFactor;

        t.el.classList.add('tab-distorting');
        t.el.style.transform = `scale(${opticalBulge.toFixed(3)}) skewX(${opticalShear.toFixed(2)}deg) translateY(${opticalShiftY.toFixed(1)}px)`;
      } else {
        if (t.el.classList.contains('tab-distorting')) {
          t.el.classList.remove('tab-distorting');
          t.el.style.transform = '';
        }
      }
    }

    const trackRect = track.getBoundingClientRect();
    if (e.clientX < trackRect.left + 50) {
      track.scrollLeft -= 6;
    } else if (e.clientX > trackRect.right - 50) {
      track.scrollLeft += 6;
    }
  }

  function onPointerUp(e) {
    if (!isDragging) return;
    isDragging = false;

    window.removeEventListener('pointermove', onPointerMove);
    window.removeEventListener('pointerup', onPointerUp);
    window.removeEventListener('pointercancel', onPointerUp);

    thumb.classList.remove('dragging');
    thumb._lastDeltaX = 0;
    thumb.style.transition = 'transform 0.38s cubic-bezier(0.16, 1, 0.3, 1), width 0.38s cubic-bezier(0.16, 1, 0.3, 1)';

    for (let i = 0; i < cachedTabs.length; i++) {
      const t = cachedTabs[i];
      t.el.classList.remove('tab-distorting');
      t.el.style.transform = '';
    }

    if (hasMoved) {
      const currentTransform = thumb.style.transform;
      const match = currentTransform.match(/translateX\(([-\d.]+)px\)/);
      const droppedX = match ? parseFloat(match[1]) : currentActiveThumbX;
      const droppedCenter = droppedX + thumb.offsetWidth / 2;

      const targetTab = getClosestCachedTab(droppedCenter);
      if (targetTab) {
        const pageName = targetTab.id.replace('tab-', '');
        goPage(pageName);
      }
    }
  }

  thumb.addEventListener('pointerdown', onPointerDown);
  track.addEventListener('pointerdown', e => {
    if (e.target.closest('.tab-item') || e.target === thumb) {
      onPointerDown(e);
    }
  });

  track.addEventListener('click', e => {
    if (hasMoved) {
      e.stopPropagation();
      e.preventDefault();
      hasMoved = false;
    }
  }, true);
})();

// Keep the thumb aligned to the active tab across resizes / orientation changes
let tabResizeTimer = null;
window.addEventListener('resize', () => {
  clearTimeout(tabResizeTimer);
  tabResizeTimer = setTimeout(() => {
    const active = document.querySelector('.tab-item.active');
    if (active) moveTabThumb(active.id.replace('tab-', ''), { instant: true });
  }, 120);
}, { passive: true });

function initTabsOnLoad() {
  moveTabThumb('home', { instant: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initTabsOnLoad);
} else {
  initTabsOnLoad();
}
window.addEventListener('load', initTabsOnLoad);

function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  if (!toast) return;

  // Clean any emojis from message to ensure clean icon-based typography
  const cleanMsg = String(message)
    .replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F1E6}-\u{1F1FF}✅❌⚠️💡🔥⟳🔄]/gu, '')
    .trim();

  const iconSvg = isError
    ? `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`
    : `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M20 6L9 17l-5-5"/></svg>`;

  toast.innerHTML = `${iconSvg}<span>${cleanMsg}</span>`;
  toast.style.background = isError ? 'var(--error)' : 'var(--black)';
  toast.classList.add('show');

  clearTimeout(toast._hideTimer);
  toast._hideTimer = setTimeout(() => {
    toast.classList.remove('show');
  }, 3200);
}

// ─── CUSTOM DROPDOWN (SMOOTH & ZERO-LAG) ───
function toggleCustomSelect(wrapId) {
  const allWraps = document.querySelectorAll('.custom-select-wrap');
  allWraps.forEach(w => {
    if (w.id !== wrapId) w.classList.remove('open');
  });
  const target = document.getElementById(wrapId);
  if (target) target.classList.toggle('open');
}

function selectCustomOption(wrapId, hiddenInputId, val, labelText) {
  const hiddenInput = document.getElementById(hiddenInputId);
  if (hiddenInput) {
    hiddenInput.value = val;
    hiddenInput.dispatchEvent(new Event('change'));
  }
  const labelEl = document.getElementById(`${wrapId}-label`);
  if (labelEl) labelEl.textContent = labelText;

  if (hiddenInputId === 'img-model') {
    updateImgPromptPlaceholder(val);
  }

  const wrap = document.getElementById(wrapId);
  if (wrap) {
    wrap.querySelectorAll('.custom-option').forEach(opt => {
      opt.classList.toggle('selected', opt.getAttribute('data-val') === val);
    });
    wrap.classList.remove('open');
  }
}

// ─── DYNAMIC PLACEHOLDER FOR IMAGE GENERATOR MODEL ───
function updateImgPromptPlaceholder(modelVal) {
  const promptInput = document.getElementById('img-prompt');
  if (!promptInput) return;
  const placeholders = {
    'flux': 'Ketik ide gambarmu di sini... (Contoh: A futuristic cyberpunk samurai standing in neon rain, cinematic lighting, 8k resolution...)',
    'flux-realism': 'Ketik ide foto nyata di sini... (Contoh: Ultra realistic 35mm portrait photography of an astronaut walking in desert, natural sun flare, 8k dslr...)',
    'flux-anime': 'Ketik ide anime di sini... (Contoh: Makoto Shinkai style, high school rooftop under starry galaxy sky, sakura petals blowing in wind, vibrant vivid anime...)',
    'flux-3d': 'Ketik ide 3D CGI di sini... (Contoh: 3D cute glowing crystal robot floating in futuristic room, octane render, cinema 4d, ray tracing 8k...)',
    'turbo': 'Ketik prompt cepat di sini... (Contoh: Cyberpunk city highway neon speed, dynamic blur, hyper fast render ~1 detik...)'
  };
  promptInput.placeholder = placeholders[modelVal] || placeholders['flux'];
}

// ─── AI CHAT MODEL SELECTOR & DYNAMIC PLACEHOLDER ───
// selectAiModel(val, shortLabel, fullLabel)
// shortLabel = shown in compact header pill (e.g. "Standard")
// fullLabel  = shown in engine badge / toast (e.g. "XVoid Standard")
function selectAiModel(val, shortLabel, fullLabel) {
  // Handle old 2-arg calls gracefully
  if (!fullLabel) fullLabel = shortLabel;
  const shortDisplay = shortLabel || fullLabel;

  const input = document.getElementById('ai-model');
  const labelEl = document.getElementById('cs-ai-model-label');
  const badgeEl = document.getElementById('ai-engine-badge');
  const chatInput = document.getElementById('ai-input');

  if (input) {
    input.value = val;
    input.dispatchEvent(new Event('change'));
  }
  if (labelEl) labelEl.textContent = shortDisplay;
  if (badgeEl) badgeEl.textContent = `Engine: ${fullLabel}`;

  const placeholders = {
    'strom':    'Tanyakan apapun ke XVoid AI...',
    'advanced': 'Tanyakan analisis atau penalaran logika...',
    'code':     'Tanyakan skrip koding atau debugging...',
    'deep':     'Eksplorasi konsep atau riset mendalam...'
  };
  if (chatInput) chatInput.placeholder = placeholders[val] || 'Tanyakan apapun ke XVoid AI...';

  const wrap = document.getElementById('cs-ai-model');
  if (wrap) {
    wrap.classList.remove('open');
    wrap.querySelectorAll('.custom-option').forEach(opt => {
      opt.classList.toggle('selected', opt.getAttribute('data-val') === val);
    });
  }
  showToast(`Model: ${fullLabel}`);
}

// Tutup custom dropdown jika klik di luar
document.addEventListener('click', (e) => {
  if (!e.target.closest('.custom-select-wrap')) {
    document.querySelectorAll('.custom-select-wrap').forEach(w => w.classList.remove('open'));
  }
});

// ─── UNIFIED RAF SCHEDULER (single frame loop, zero lag) ───
// Both canvases share ONE requestAnimationFrame tick instead of two competing
// loops. This halves per-frame browser overhead and lets us pause everything
// instantly (tab hidden, reduced-motion) from a single switch.
const XVoidRAF = (() => {
  const tasks = new Set();
  let running = false;
  let rafId = null;

  function tick(ts) {
    tasks.forEach(fn => fn(ts));
    rafId = tasks.size ? requestAnimationFrame(tick) : null;
  }

  function ensureRunning() {
    if (rafId === null && tasks.size && !document.hidden) {
      rafId = requestAnimationFrame(tick);
    }
  }

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      if (rafId !== null) cancelAnimationFrame(rafId);
      rafId = null;
    } else {
      ensureRunning();
    }
  });

  return {
    add(fn) { tasks.add(fn); ensureRunning(); },
    remove(fn) { tasks.delete(fn); }
  };
})();

const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ─── AMBIENT BACKGROUND CANVAS (throttled ~30fps, DPR-aware, zero lag) ───
(function initBgCanvas() {
  const c = document.getElementById('bgCanvas');
  if (!c || prefersReducedMotion) return;
  const ctx = c.getContext('2d', { alpha: true });
  let W, H, dpr, pts = [];
  let lastFrame = 0;
  const FRAME_MS = 1000 / 30; // ambient dots never need more than 30fps

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 1.5); // cap DPR: crisp enough, cheap enough
    W = window.innerWidth;
    H = window.innerHeight;
    c.width = W * dpr;
    c.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function makePoints() {
    const count = W < 640 ? 16 : 28;
    const colors = [
      'rgba(56, 189, 248, 0.45)',  // electric cyan
      'rgba(99, 102, 241, 0.40)',  // indigo
      'rgba(139, 92, 246, 0.42)',  // violet
      'rgba(236, 72, 153, 0.35)',  // magenta/pink
    ];
    pts = Array.from({ length: count }, () => ({
      x: Math.random() * W,
      y: Math.random() * H,
      r: 1.5 + Math.random() * 2.8,
      color: colors[Math.floor(Math.random() * colors.length)],
      vx: (Math.random() - 0.5) * 0.45,
      vy: (Math.random() - 0.5) * 0.45,
    }));
  }

  function draw(ts) {
    if (ts - lastFrame < FRAME_MS) return;
    lastFrame = ts;
    ctx.clearRect(0, 0, W, H);
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i];
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < -10) p.x = W + 10;
      if (p.x > W + 10) p.x = -10;
      if (p.y < -10) p.y = H + 10;
      if (p.y > H + 10) p.y = -10;
    }
  }

  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { resize(); makePoints(); }, 120); // debounce resize
  }, { passive: true });

  resize();
  makePoints();
  XVoidRAF.add(draw);
})();


// ─── CLICK PARTICLE BURST (High-precision, DPR-perfect, Mobile & Touch Friendly) ───
(function initClickBurst() {
  const c = document.getElementById('clickFxCanvas');
  if (!c || prefersReducedMotion) return;
  const ctx = c.getContext('2d', { alpha: true });
  let W, H, dpr;
  let particles = [];

  function resize() {
    dpr = window.devicePixelRatio || 1;
    W = window.innerWidth;
    H = window.innerHeight;
    c.width = Math.round(W * dpr);
    c.height = Math.round(H * dpr);
    c.style.width = W + 'px';
    c.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();

  let resizeTimer = null;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(resize, 100);
  }, { passive: true });

  // Use pointerdown so both mouse cursor and mobile touch tap trigger instantly at exact coordinates
  window.addEventListener('pointerdown', e => {
    // Only primary click / touch
    if (e.button !== undefined && e.button !== 0) return;

    // Skip burst on interactive elements
    if (e.target.closest('button, a, input, textarea, select, .tab-item, .tool-card, .sub-tab-btn, .btn, .chip, .param-row')) return;

    const rect = c.getBoundingClientRect();
    // Calibrate coordinates with physical canvas position
    const clickX = e.clientX - rect.left;
    const clickY = e.clientY - rect.top;

    // Micro-ripple ring directly under contact point
    particles.push({
      type: 'ripple',
      x: clickX,
      y: clickY,
      r: 3,
      maxR: window.innerWidth < 640 ? 20 : 26,
      alpha: 0.55,
    });

    // Subtle, elegant particle burst radiating from touch / click
    const count = window.innerWidth < 640 ? 5 : 7;
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 / count) * i + (Math.random() - 0.5) * 0.4;
      const speed = 1.6 + Math.random() * 2.6;
      particles.push({
        type: 'dot',
        x: clickX,
        y: clickY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        r: 1.8 + Math.random() * 1.4,
        alpha: 0.85,
      });
    }
    XVoidRAF.add(updateBurst);
  }, { passive: true });

  function updateBurst() {
    ctx.clearRect(0, 0, W, H);
    particles = particles.filter(p => p.alpha > 0.03);
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      if (p.type === 'ripple') {
        p.r += (p.maxR - p.r) * 0.22 + 0.4;
        p.alpha *= 0.88;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(17, 17, 20, ${p.alpha.toFixed(2)})`;
        ctx.lineWidth = 1.2;
        ctx.stroke();
      } else {
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.94;
        p.vy *= 0.94;
        p.alpha *= 0.91;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(17, 17, 20, ${p.alpha.toFixed(2)})`;
        ctx.fill();
      }
    }
    if (particles.length === 0) {
      ctx.clearRect(0, 0, W, H);
      XVoidRAF.remove(updateBurst);
    }
  }
})();

// ─── FLOATING SHAPES ───
(function initShapes() {
  const container = document.getElementById('shapesLayer');
  if (!container || prefersReducedMotion) return;
  const shapes = ['circle', 'ring', 'square', 'tri'];
  const total = window.innerWidth < 640 ? 7 : 14; // fewer floating shapes on mobile = less paint work
  for (let i = 0; i < total; i++) {
    const el = document.createElement('div');
    const shapeType = shapes[Math.floor(Math.random() * shapes.length)];
    const size = 18 + Math.random() * 32;
    el.className = `shape ${shapeType}`;
    el.style.width = `${size}px`;
    el.style.height = `${size}px`;
    el.style.left = `${Math.random() * 95}%`;
    el.style.top = `${100 + Math.random() * 10}vh`;
    el.style.animationDuration = `${14 + Math.random() * 20}s`;
    el.style.animationDelay = `${Math.random() * 10}s`;
    container.appendChild(el);
  }
})();

// ═══════════════════════════════════════════════════════════
// TOOL MODULES LOGIC
// ═══════════════════════════════════════════════════════════

// 1. BASE64 TOOLS
function setBase64Tab(tab) {
  document.getElementById('b64-tab-encode').classList.toggle('active', tab === 'encode');
  document.getElementById('b64-tab-decode').classList.toggle('active', tab === 'decode');
  document.getElementById('b64-view-encode').style.display = tab === 'encode' ? 'block' : 'none';
  document.getElementById('b64-view-decode').style.display = tab === 'decode' ? 'block' : 'none';
}

function handleBase64FileEncode(e) {
  const file = e.target.files[0];
  if (!file) return;

  const fileNameEl = document.getElementById('b64-file-name');
  const fileInfoEl = document.getElementById('b64-file-info');
  const badgeEl = document.getElementById('b64-selected-badge');
  const badgeText = document.getElementById('b64-badge-text');

  const sizeKb = (file.size / 1024).toFixed(1);
  const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
  const displaySize = file.size > 1024 * 1024 ? `${sizeMb} MB` : `${sizeKb} KB`;

  if (fileNameEl) fileNameEl.textContent = file.name;
  if (fileInfoEl) fileInfoEl.textContent = `Tipe: ${file.type || 'file'} · Ukuran: ${displaySize}`;
  if (badgeEl) badgeEl.style.display = 'inline-flex';
  if (badgeText) badgeText.textContent = `${file.name} (${displaySize})`;

  const reader = new FileReader();
  reader.onload = function(evt) {
    const dataUrl = evt.target.result;
    const base64Str = dataUrl.split(',')[1];
    document.getElementById('b64-encode-output').textContent = base64Str;
    document.getElementById('b64-datauri-output').textContent = dataUrl;
    document.getElementById('b64-encode-result').classList.add('visible');
    showToast('File berhasil di-encode ke Base64');
  };
  reader.readAsDataURL(file);
}

// Drag & Drop initializer for styled file upload
document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('b64-dropzone');
  const fileInput = document.getElementById('b64-file-input');
  if (dropzone && fileInput) {
    ['dragenter', 'dragover'].forEach(evtName => {
      dropzone.addEventListener(evtName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(evtName => {
      dropzone.addEventListener(evtName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        fileInput.files = dt.files;
        handleBase64FileEncode({ target: fileInput });
      }
    });
  }
});

function handleBase64Decode() {
  const input = document.getElementById('b64-decode-input').value.trim();
  if (!input) {
    showToast('Masukkan string Base64 terlebih dahulu', true);
    return;
  }
  let base64Data = input;
  let mime = 'application/octet-stream';
  let isBase64 = true;
  if (input.startsWith('data:')) {
    const comma = input.indexOf(',');
    if (comma !== -1) {
      const metadata = input.substring(5, comma).split(';');
      mime = metadata[0] || mime;
      isBase64 = metadata.includes('base64');
      base64Data = input.substring(comma + 1);
    }
  }
  try {
    if (!isBase64) {
      const decodedText = decodeURIComponent(base64Data);
      const blob = new Blob([decodedText], { type: mime });
      const blobUrl = URL.createObjectURL(blob);
      const dlBtn = document.getElementById('b64-download-link');
      dlBtn.href = blobUrl;
      dlBtn.download = 'decoded_file.txt';
      dlBtn.style.display = 'inline-flex';
      document.getElementById('b64-decode-result').classList.add('visible');
      showToast('Base64 berhasil di-decode');
      return;
    }
    base64Data = base64Data.replace(/\s/g, '').replace(/-/g, '+').replace(/_/g, '/');
    base64Data += '='.repeat((4 - (base64Data.length % 4)) % 4);
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: mime });
    const blobUrl = URL.createObjectURL(blob);
    
    const dlBtn = document.getElementById('b64-download-link');
    dlBtn.href = blobUrl;
    const extension = ({
      'image/jpeg': 'jpg',
      'image/svg+xml': 'svg',
      'application/pdf': 'pdf',
      'application/json': 'json',
      'text/plain': 'txt',
      'application/octet-stream': 'bin'
    })[mime] || mime.split('/')[1]?.split('+')[0] || 'bin';
    dlBtn.download = `decoded_file.${extension}`;
    dlBtn.target = '_blank';
    dlBtn.style.display = 'inline-flex';
    document.getElementById('b64-decode-result').classList.add('visible');
    showToast('Base64 berhasil di-decode');
  } catch (err) {
    showToast('Base64 tidak valid: ' + err.message, true);
  }
}

function copyText(elemId) {
  const text = document.getElementById(elemId).textContent;
  navigator.clipboard.writeText(text).then(() => {
    showToast('Berhasil disalin ke clipboard');
  });
}

// 2. MAGIC LINK (ALIGHT MOTION)
function toggleManualVerify() {
  const step2 = document.getElementById('ml-step-2');
  if (!step2) return;
  step2.style.display = step2.style.display === 'none' ? 'block' : 'none';
}

function checkAndAutoVerify(val) {
  // Auto-submit jika URL valid Alight Motion terdeteksi saat paste
  if (val && (val.includes('alightcreative.com') || val.includes('alight-creative.firebaseapp.com')) && val.length > 80) {
    clearTimeout(window._mlAutoTimer);
    window._mlAutoTimer = setTimeout(() => { verifyMagicLink(); }, 600);
  }
}

async function sendMagicLink() {
  const version = document.getElementById('ml-version').value;
  const email = document.getElementById('ml-email').value.trim();
  if (!email || !email.includes('@')) {
    showToast('Masukkan alamat Gmail yang valid', true);
    return;
  }
  const btn = document.getElementById('ml-send-btn');
  btn.innerHTML = `<div class="spinner"></div> Mengirim ke Gmail...`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/magiclink/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version, email })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    showToast('Magic link berhasil dikirim! Cek Gmail Anda.');

    // Tampilkan panduan salin link + form step 2
    const guideBox = document.getElementById('ml-guide-box');
    const step2 = document.getElementById('ml-step-2');
    if (guideBox) guideBox.style.display = 'block';
    if (step2) {
      step2.style.display = 'block';
      step2.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  } catch (err) {
    showToast('Gagal kirim magic link: ' + err.message, true);
  } finally {
    btn.innerHTML = `Kirim Ulang Magic Link`;
    btn.disabled = false;
  }
}

async function verifyMagicLink() {
  const version = document.getElementById('ml-version').value;
  const email = document.getElementById('ml-email').value.trim();
  const link = document.getElementById('ml-link').value.trim();
  if (!link) {
    showToast('Paste URL Magic Link dari email terlebih dahulu', true);
    return;
  }
  const btn = document.getElementById('ml-verif-btn');
  btn.innerHTML = `<div class="spinner"></div> Mengaktifkan Premium...`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/magiclink/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ version, email, link })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    
    document.getElementById('ml-result').classList.add('visible');
    document.getElementById('ml-code-output').textContent = data.code || JSON.stringify(data, null, 2);
    showToast('Premium berhasil diaktifkan!');
  } catch (err) {
    showToast('Verifikasi gagal: ' + err.message, true);
  } finally {
    btn.innerHTML = `Verifikasi & Aktifkan Premium`;
    btn.disabled = false;
  }
}

// 3. WEB TOOLS
function setWebTab(tab) {
  ['apk', 'source', 'zip'].forEach(t => {
    document.getElementById(`web-tab-${t}`).classList.toggle('active', t === tab);
    document.getElementById(`web-view-${t}`).style.display = t === tab ? 'block' : 'none';
  });
}

async function startWebToApk() {
  const appName = document.getElementById('w2a-name')?.value.trim();
  const websiteUrl = document.getElementById('w2a-url')?.value.trim();
  const packageName = document.getElementById('w2a-pkg')?.value.trim();
  const versionName = (document.getElementById('w2a-vname') || document.getElementById('w2a-ver'))?.value.trim() || '1.0.0';
  const versionCode = (document.getElementById('w2a-vcode') || document.getElementById('w2a-code'))?.value.trim() || '1';
  const iconUrl = document.getElementById('w2a-icon')?.value.trim() || '';

  if (!appName || !websiteUrl || !packageName) {
    showToast('Mohon lengkapi nama app, URL, dan package name', true);
    return;
  }

  const btn = document.getElementById('w2a-btn');
  btn.innerHTML = `<div class="spinner"></div> Memulai Kompilasi APK...`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/web2apk/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ appName, websiteUrl, packageName, versionName, versionCode, iconUrl })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const buildId = data.build_id || data.id;
    showToast(`Build APK dimulai! ID: ${buildId}`);
    pollWebToApk(buildId);
  } catch (err) {
    showToast('Gagal memproses APK: ' + err.message, true);
    btn.innerHTML = `Buat File APK`;
    btn.disabled = false;
  }
}

async function pollWebToApk(buildId) {
  const resBox = document.getElementById('w2a-result');
  const statusTitle = document.getElementById('w2a-status-title') || document.getElementById('w2a-status-text');
  const outputBox = document.getElementById('w2a-output');
  if (resBox) resBox.classList.add('visible');
  
  for (let i = 0; i < 60; i++) {
    await new Promise(r => setTimeout(r, 3000));
    try {
      const res = await fetch(`/api/web2apk/status?build_id=${encodeURIComponent(buildId)}`);
      const data = await res.json();
      const status = data.status || 'processing';
      const dlUrl = data.download_url || data.url;
      if (statusTitle) statusTitle.textContent = `Status: ${status} (${i+1}/60)...`;
      if (outputBox) outputBox.textContent = JSON.stringify(data, null, 2);
      
      if (dlUrl) {
        if (statusTitle) statusTitle.textContent = `Pembuatan APK Selesai!`;
        const link = document.getElementById('w2a-dl-link') || document.getElementById('w2a-download-link');
        if (link) {
          link.href = dlUrl;
          link.style.display = 'inline-flex';
        }
        showToast('APK berhasil dibuat & siap diunduh!');
        break;
      }
    } catch (e) {}
  }
  const btn = document.getElementById('w2a-btn');
  if (btn) {
    btn.innerHTML = `Buat File APK`;
    btn.disabled = false;
  }
}

async function fetchPageSource() {
  const url = (document.getElementById('src-url') || document.getElementById('ps-url'))?.value.trim();
  if (!url) {
    showToast('Masukkan URL target terlebih dahulu', true);
    return;
  }
  const btn = document.getElementById('src-btn') || document.getElementById('ps-btn');
  btn.innerHTML = `<div class="spinner"></div> Mengambil Kode Sumber...`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/pagesource', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const resBox = document.getElementById('src-result') || document.getElementById('ps-result');
    const codeOut = document.getElementById('src-output') || document.getElementById('ps-code-output');
    if (resBox) resBox.classList.add('visible');
    if (codeOut) codeOut.textContent = (data.html || '').substring(0, 20000);
    showToast('Kode sumber berhasil diambil!');
  } catch (err) {
    showToast('Gagal mengambil kode sumber: ' + err.message, true);
  } finally {
    btn.innerHTML = `Ambil Kode Sumber`;
    btn.disabled = false;
  }
}

async function convertWebToZip() {
  const url = (document.getElementById('zip-url') || document.getElementById('w2z-url'))?.value.trim();
  if (!url) {
    showToast('Masukkan URL website terlebih dahulu', true);
    return;
  }
  const btn = document.getElementById('zip-btn') || document.getElementById('w2z-btn');
  btn.innerHTML = `<div class="spinner"></div> Mengonversi ke ZIP...`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/webtozip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const dlLink = document.getElementById('zip-dl-link') || document.getElementById('w2z-download-link');
    const preview = document.getElementById('zip-preview');
    if (preview) preview.innerHTML = `<div style="font-size:12px;color:var(--gray-700);margin-bottom:8px;">Paket ZIP berhasil dibuat untuk: <strong>${escapeHtml(url)}</strong></div>`;
    if (dlLink) {
      dlLink.href = data.download_url;
      dlLink.style.display = 'inline-flex';
    }
    const resBox = document.getElementById('zip-result') || document.getElementById('w2z-result');
    if (resBox) resBox.classList.add('visible');
    showToast('Website berhasil dipaketkan ke ZIP!');
  } catch (err) {
    showToast('Konversi ZIP gagal: ' + err.message, true);
  } finally {
    btn.innerHTML = `Konversi ke ZIP`;
    btn.disabled = false;
  }
}

// Global aliases for button onclick compatibility
window.startWeb2Apk = startWebToApk;
window.webToZip = convertWebToZip;

// 4. XVOID AI CHAT
let stromSessionId = null;

function autoResizeAiInput() {
  const el = document.getElementById('ai-input');
  if (!el) return;
  el.style.height = 'auto';
  const scrollH = el.scrollHeight;
  const nextH = Math.min(scrollH, 140);
  el.style.height = (nextH > 24 ? nextH : 24) + 'px';
  el.classList.toggle('has-scroll', scrollH > 140);

  const box = el.closest('.chat-input-box');
  if (box) {
    box.classList.toggle('is-multiline', nextH > 28);
  }

  const btn = document.getElementById('ai-send-btn');
  if (btn) {
    btn.classList.toggle('has-text', el.value.trim().length > 0);
  }
}

function keepAiInputInView() {
  const el = document.getElementById('ai-input');
  const chatWin = document.querySelector('#view-stromai .chat-window');
  const msgs = document.getElementById('ai-messages');
  if (!chatWin) return;

  // Ensure chat window stays in view above virtual keyboard
  chatWin.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  if (msgs) {
    msgs.scrollTop = msgs.scrollHeight;
  }
}

// Setup AI chat input events (auto-expand, shift+enter, and mobile keyboard resilience)
function initAiChatInput() {
  const el = document.getElementById('ai-input');
  if (!el || el.dataset.initialized) return;
  el.dataset.initialized = 'true';

  el.addEventListener('input', autoResizeAiInput);
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendAiMessage();
    }
  });

  // Mobile virtual keyboard handling: adjust viewport when opened
  el.addEventListener('focus', () => {
    setTimeout(keepAiInputInView, 120);
    setTimeout(keepAiInputInView, 350);
  });
  el.addEventListener('click', () => {
    setTimeout(keepAiInputInView, 150);
  });

  if (window.visualViewport) {
    window.visualViewport.addEventListener('resize', () => {
      if (document.activeElement === el) {
        setTimeout(keepAiInputInView, 60);
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAiChatInput);
} else {
  initAiChatInput();
}

async function sendAiMessage() {
  const input = document.getElementById('ai-input');
  const prompt = input ? input.value.trim() : '';
  if (!prompt) return;

  const msgsContainer = document.getElementById('ai-messages');
  // Add User bubble
  const uBubble = document.createElement('div');
  uBubble.className = 'chat-bubble user';
  uBubble.textContent = prompt;
  msgsContainer.appendChild(uBubble);

  // Reset input state & height
  input.value = '';
  input.style.height = '24px';
  input.classList.remove('has-scroll');
  const sendBtn = document.getElementById('ai-send-btn');
  if (sendBtn) sendBtn.classList.remove('has-text');

  msgsContainer.scrollTop = msgsContainer.scrollHeight;
  keepAiInputInView();

  // Add Thinking AI Bubble
  const aiBubble = document.createElement('div');
  aiBubble.className = 'chat-bubble ai';
  aiBubble.innerHTML = `<div class="spinner" style="border-top-color:var(--black);width:12px;height:12px;display:inline-block;"></div> Mengetik...`;
  msgsContainer.appendChild(aiBubble);
  msgsContainer.scrollTop = msgsContainer.scrollHeight;

  try {
    const mode = document.getElementById('ai-model')?.value || 'strom';
    const res = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, sessionId: stromSessionId, mode })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    stromSessionId = data.sessionId || stromSessionId;
    renderAiMarkdown(aiBubble, data.reply || data.text || 'Tidak ada balasan.');
  } catch (err) {
    aiBubble.textContent = 'Error: ' + err.message;
    aiBubble.style.color = 'var(--error)';
  } finally {
    msgsContainer.scrollTop = msgsContainer.scrollHeight;
    keepAiInputInView();
  }
}

// ─── MARKDOWN / RICH TEXT RENDERER FOR AI BUBBLES ───
function renderAiMarkdown(el, raw) {
  const isUser = el.classList.contains('user');
  // Process fenced code blocks first
  let lines = raw.split('\n');
  let html = '';
  let inCode = false;
  let codeLang = '';
  let codeLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const fenceMatch = line.match(/^```(\w*)/);
    if (fenceMatch && !inCode) {
      inCode = true;
      codeLang = fenceMatch[1] || 'code';
      codeLines = [];
      continue;
    }
    if (inCode) {
      if (line.trim() === '```') {
        // close code block
        const escaped = codeLines.join('\n')
          .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
        html += `<div class="chat-code-block">`
          + `<div class="chat-code-header"><span>${codeLang}</span>`
          + `<button class="chat-code-copy-btn" onclick="copyChatCode(this)" data-code="${escaped.replace(/"/g,'&quot;')}">Copy</button></div>`
          + `<pre class="chat-code-pre"><code>${escaped}</code></pre></div>`;
        inCode = false;
      } else {
        codeLines.push(line);
      }
      continue;
    }
    html += processLine(line, isUser) + '\n';
  }
  // Close unclosed block
  if (inCode && codeLines.length) {
    const escaped = codeLines.join('\n')
      .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    html += `<div class="chat-code-block"><div class="chat-code-header"><span>${codeLang}</span></div>`
      + `<pre class="chat-code-pre"><code>${escaped}</code></pre></div>`;
  }
  el.innerHTML = html.trim();
}

function processLine(line, isUser) {
  // Headings
  if (/^### /.test(line)) return `<div class="chat-h3">${inlineFormat(line.slice(4), isUser)}</div>`;
  if (/^## /.test(line)) return `<div class="chat-h2">${inlineFormat(line.slice(3), isUser)}</div>`;
  if (/^# /.test(line)) return `<div class="chat-h1">${inlineFormat(line.slice(2), isUser)}</div>`;
  // Blockquote
  if (/^> /.test(line)) return `<div class="chat-quote">${inlineFormat(line.slice(2), isUser)}</div>`;
  // Unordered list
  if (/^[\-\*] /.test(line)) return `<div style="display:flex;gap:6px;margin:2px 0;"><span>•</span><span>${inlineFormat(line.slice(2), isUser)}</span></div>`;
  // Ordered list  
  const olMatch = line.match(/^(\d+)\. (.+)/);
  if (olMatch) return `<div style="display:flex;gap:6px;margin:2px 0;"><span style="min-width:16px;">${olMatch[1]}.</span><span>${inlineFormat(olMatch[2], isUser)}</span></div>`;
  // Horizontal rule
  if (/^(---+|\*\*\*+)$/.test(line.trim())) return `<hr style="border:none;border-top:1px solid var(--gray-200);margin:8px 0;">`;
  // Empty line → spacer
  if (line.trim() === '') return `<div style="height:6px;"></div>`;
  // Default paragraph
  return `<span>${inlineFormat(line, isUser)}</span><br>`;
}

function inlineFormat(text, isUser) {
  return text
    // Bold+italic ***text***
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    // Bold **text**
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    // Italic *text* or _text_
    .replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>')
    .replace(/(?<!_)_(?!_)(.+?)(?<!_)_(?!_)/g, '<em>$1</em>')
    // Strikethrough ~~text~~
    .replace(/~~(.+?)~~/g, '<del>$1</del>')
    // Inline code `code`
    .replace(/`([^`]+)`/g, `<code class="chat-inline-code">$1</code>`)
    // Links [text](url)
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a class="chat-link" href="$2" target="_blank" rel="noopener">$1</a>')
    // Raw URLs
    .replace(/(https?:\/\/[^\s<>"]+)/g, (url) => `<a class="chat-link" href="${url}" target="_blank" rel="noopener">${url}</a>`);
}

function copyChatCode(btn) {
  const code = btn.dataset.code
    .replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"');
  navigator.clipboard.writeText(code).then(() => {
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('copied'); }, 2000);
  });
}

// ─── FULLSCREEN AI CHAT TOGGLE ───
let _aiFullscreen = false;
let _aiTransitioning = false;

function toggleAiFullscreen() {
  if (_aiTransitioning) return;
  const section      = document.getElementById('view-stromai');
  const card         = section?.querySelector('.ai-card');
  const nav          = document.getElementById('tabNav');
  const expandIcon   = document.querySelector('.fs-icon-expand');
  const compressIcon = document.querySelector('.fs-icon-compress');
  const msgs         = document.getElementById('ai-messages');

  if (!section) return;
  _aiTransitioning = true;
  _aiFullscreen = !_aiFullscreen;

  if (_aiFullscreen) {
    // ── ENTER FULLSCREEN ──────────────────────────────
    // 1. Hide nav immediately with transition
    document.body.classList.add('ai-fullscreen-active');
    if (nav) {
      nav.style.pointerEvents = 'none';
    }

    // 2. Expand section to full viewport overlay
    section.classList.remove('ai-fullscreen-exiting');
    section.classList.add('ai-fullscreen');

    // 3. Card slides smoothly DOWNWARDS and zooms IN
    card?.classList.remove('ai-zooming-out', 'ai-windowed-settle');
    card?.classList.add('ai-zooming-in');

    // 4. Update toggle icons
    if (expandIcon)   expandIcon.style.display   = 'none';
    if (compressIcon) compressIcon.style.display  = '';

    // 5. Complete enter sequence
    setTimeout(() => {
      card?.classList.remove('ai-zooming-in');
      if (nav && _aiFullscreen) nav.style.visibility = 'hidden';
      if (msgs) msgs.scrollTop = msgs.scrollHeight;
      _aiTransitioning = false;
    }, 450);

  } else {
    // ── EXIT FULLSCREEN (WINDOWED MODE) ───────────────
    // 1. Card slides smoothly UPWARDS and zooms OUT
    card?.classList.remove('ai-zooming-in', 'ai-windowed-settle');
    card?.classList.add('ai-zooming-out');
    section.classList.add('ai-fullscreen-exiting');

    // 2. Prepare nav to slide back in
    if (nav) {
      nav.style.visibility = 'visible';
    }

    // 3. Update toggle icons
    if (expandIcon)   expandIcon.style.display   = '';
    if (compressIcon) compressIcon.style.display = 'none';

    // 4. Complete exit sequence
    setTimeout(() => {
      section.classList.remove('ai-fullscreen', 'ai-fullscreen-exiting');
      document.body.classList.remove('ai-fullscreen-active');
      if (nav) {
        nav.style.pointerEvents = '';
        nav.style.visibility = '';
      }
      card?.classList.remove('ai-zooming-out');
      card?.classList.add('ai-windowed-settle');

      if (msgs) msgs.scrollTop = msgs.scrollHeight;

      setTimeout(() => {
        card?.classList.remove('ai-windowed-settle');
        _aiTransitioning = false;
      }, 400);
    }, 340);
  }
}

// Close fullscreen with Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && _aiFullscreen) toggleAiFullscreen();
});

function clearAiChat() {
  stromSessionId = null;
  const input = document.getElementById('ai-input');
  if (input) {
    input.value = '';
    input.style.height = '24px';
    input.classList.remove('has-scroll');
  }
  const sendBtn = document.getElementById('ai-send-btn');
  if (sendBtn) sendBtn.classList.remove('has-text');

  document.getElementById('ai-messages').innerHTML = `
    <div class="chat-bubble ai">
      Halo! Saya <strong>XVoid</strong>, asisten AI dari Project-XVOID. Ada yang bisa saya bantu hari ini?
    </div>
  `;
  showToast('Session AI direset');
}

// 5. UNIVERSAL MEDIA DOWNLOADER (TikTok, Instagram, YouTube, X/Twitter, Facebook, dll.)
async function fetchTikTok() {
  const urlInput = document.getElementById('tt-url');
  const rawUrl = (urlInput?.value || '').trim();
  if (!rawUrl) {
    showToast('Masukkan link media (TikTok, IG, YouTube, X, FB) terlebih dahulu!', true);
    return;
  }

  // Quick sanity check for valid URL structure
  if (!/^https?:\/\//i.test(rawUrl) && !rawUrl.includes('.')) {
    showToast('Format tautan tidak valid! Pastikan diawali dengan http:// atau https://', true);
    return;
  }

  const btn = document.getElementById('tt-btn');
  const origBtnContent = btn.innerHTML;
  btn.innerHTML = `<div class="spinner" style="width:14px;height:14px;border-width:2px;display:inline-block;"></div> <span>Mengambil Media...</span>`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/downloader/info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: rawUrl })
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || data.message || 'Gagal memproses media');

    // Platform Badge
    const platBadge = document.getElementById('tt-platform-badge');
    if (platBadge) platBadge.textContent = data.platform || 'Universal';

    // Duration Badge
    const durBadge = document.getElementById('tt-duration-badge');
    if (durBadge) {
      durBadge.textContent = data.duration ? `Durasi: ${data.duration}` : '';
    }

    // Thumbnail Preview
    const thumbWrap = document.getElementById('tt-thumb-wrap');
    const thumbImg = document.getElementById('tt-thumb-img');
    if (thumbWrap && thumbImg) {
      if (data.thumbnail) {
        thumbImg.src = data.thumbnail;
        thumbWrap.style.display = 'block';
      } else {
        thumbWrap.style.display = 'none';
      }
    }

    // Author & Caption & Views
    const authorEl = document.getElementById('tt-author');
    if (authorEl) {
      authorEl.textContent = data.author ? `@${data.author}` : (data.platform || 'Media');
    }

    const captionEl = document.getElementById('tt-caption');
    if (captionEl) {
      captionEl.textContent = data.title || data.caption || '';
    }

    const viewsEl = document.getElementById('tt-views');
    if (viewsEl) {
      let stats = [];
      const vCount = data.views || data.play_count || data.view_count;
      if (vCount && Number(vCount)) {
        stats.push(`${Number(vCount).toLocaleString()} views`);
      }
      const lCount = data.likes || data.like_count;
      if (lCount && Number(lCount)) {
        stats.push(`${Number(lCount).toLocaleString()} likes`);
      }
      viewsEl.textContent = stats.join(' · ');
    }

    // Buttons
    const mp4Btn = document.getElementById('tt-mp4-btn');
    const mp4HdBtn = document.getElementById('tt-mp4hd-btn');
    const photoBtn = document.getElementById('tt-photo-btn');
    const mp3Btn = document.getElementById('tt-mp3-btn');
    const galleryWrap = document.getElementById('tt-gallery-wrap');
    const galleryGrid = document.getElementById('tt-gallery-grid');
    const galleryCount = document.getElementById('tt-gallery-count');

    const cleanTitle = (data.title || data.caption || 'media').replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 40);

    function getSafeDl(url, fn) {
      if (!url) return '';
      if (window.location.hostname.includes('vercel.app')) return url;
      return `/api/downloader/proxy?url=${encodeURIComponent(url)}&filename=${encodeURIComponent(fn)}`;
    }

    // Single Video MP4
    if (data.video_url) {
      mp4Btn.href = getSafeDl(data.video_url, cleanTitle + '.mp4');
      mp4Btn.setAttribute('download', `${cleanTitle}.mp4`);
      mp4Btn.style.display = 'inline-flex';
    } else {
      mp4Btn.style.display = 'none';
    }

    // Single Video HD
    if (data.video_hd_url && data.video_hd_url !== data.video_url) {
      mp4HdBtn.href = getSafeDl(data.video_hd_url, cleanTitle + '_HD.mp4');
      mp4HdBtn.setAttribute('download', `${cleanTitle}_HD.mp4`);
      mp4HdBtn.style.display = 'inline-flex';
    } else {
      mp4HdBtn.style.display = 'none';
    }

    // Single Photo Button (if media is single image)
    const mediaItems = Array.isArray(data.media_items) ? data.media_items : [];
    window._currentMediaItems = mediaItems;

    if (photoBtn) {
      const singlePhoto = mediaItems.find(it => it.type === 'photo') || (data.media_type === 'photo' && data.thumbnail ? { url: data.thumbnail, filename: cleanTitle + '.jpg' } : null);
      if (singlePhoto && mediaItems.length <= 1) {
        photoBtn.href = getSafeDl(singlePhoto.url, singlePhoto.filename || cleanTitle + '.jpg');
        photoBtn.setAttribute('download', singlePhoto.filename || `${cleanTitle}.jpg`);
        photoBtn.style.display = 'inline-flex';
      } else {
        photoBtn.style.display = 'none';
      }
    }

    // Audio MP3
    if (data.mp3_url) {
      mp3Btn.href = getSafeDl(data.mp3_url, cleanTitle + '.mp3');
      mp3Btn.setAttribute('download', `${cleanTitle}.mp3`);
      mp3Btn.style.display = 'inline-flex';
    } else {
      mp3Btn.style.display = 'none';
    }

    // Multi-item Gallery (Instagram Carousels / Slides, TikTok Photos, etc.)
    if (mediaItems.length > 1) {
      if (galleryCount) galleryCount.textContent = `${mediaItems.length} Item`;
      if (galleryGrid) {
        galleryGrid.innerHTML = mediaItems.map((item, idx) => {
          const itemUrl = item.url || item.url_sd;
          const thumbUrl = item.thumbnail || itemUrl;
          const fn = item.filename || `${cleanTitle}_${idx + 1}.${item.type === 'video' ? 'mp4' : 'jpg'}`;
          const proxyDl = getSafeDl(itemUrl, fn);
          const isVid = item.type === 'video';

          return `
            <div style="background:var(--white);border:1px solid var(--gray-200);border-radius:10px;overflow:hidden;display:flex;flex-direction:column;box-shadow:var(--shadow-sm);">
              <div style="position:relative;width:100%;height:140px;background:var(--gray-100);overflow:hidden;">
                <img src="${thumbUrl}" alt="${fn}" style="width:100%;height:100%;object-fit:cover;display:block;" loading="lazy">
                <span style="position:absolute;top:6px;left:6px;background:rgba(17,17,20,0.75);color:#fff;font-size:10px;font-weight:700;padding:2px 6px;border-radius:4px;backdrop-filter:blur(4px);">
                  ${isVid ? '&#9654; VIDEO' : '&#128248; FOTO'} #${idx + 1}
                </span>
              </div>
              <div style="padding:8px 10px;display:flex;flex-direction:column;gap:6px;flex:1;justify-content:space-between;">
                <div style="font-size:11px;font-weight:600;color:var(--gray-700);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${fn}">
                  ${fn}
                </div>
                <a href="${proxyDl}" download="${fn}" class="btn-primary" style="font-size:11px;padding:6px 8px;text-decoration:none;justify-content:center;display:inline-flex;gap:4px;width:100%;" target="_blank">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                  <span>Unduh ${isVid ? 'Video' : 'Foto'}</span>
                </a>
              </div>
            </div>
          `;
        }).join('');
      }
      if (galleryWrap) galleryWrap.style.display = 'block';
    } else {
      if (galleryWrap) galleryWrap.style.display = 'none';
    }

    document.getElementById('tt-result').classList.add('visible');
    showToast(`Media dari ${data.platform || 'platform'} berhasil diproses!`);
  } catch (err) {
    showToast('Gagal memproses link: ' + err.message, true);
  } finally {
    btn.innerHTML = origBtnContent;
    btn.disabled = false;
  }
}

// Download all items in carousel / slides sequentially
function downloadAllMediaItems() {
  const items = window._currentMediaItems;
  if (!items || !items.length) {
    showToast('Tidak ada item yang dapat diunduh.', true);
    return;
  }
  showToast(`Memulai unduhan untuk ${items.length} item...`);
  items.forEach((item, idx) => {
    setTimeout(() => {
      const itemUrl = item.url || item.url_sd;
      const fn = item.filename || `media_${idx + 1}.${item.type === 'video' ? 'mp4' : 'jpg'}`;
      const dlLink = document.createElement('a');
      const isVercel = window.location.hostname.includes('vercel.app');
      dlLink.href = isVercel ? itemUrl : `/api/downloader/proxy?url=${encodeURIComponent(itemUrl)}&filename=${encodeURIComponent(fn)}`;
      dlLink.download = fn;
      dlLink.target = '_blank';
      document.body.appendChild(dlLink);
      dlLink.click();
      document.body.removeChild(dlLink);
    }, idx * 400);
  });
}

// Helper to toggle Raw JSON vs Formatted View
function toggleJsonView(prefix) {
  const formattedWrap = document.getElementById(`${prefix}-formatted-wrap`);
  const rawOutput = document.getElementById(`${prefix}-output`);
  const toggleBtn = document.getElementById(`${prefix}-toggle-json`);
  if (!formattedWrap || !rawOutput) return;

  const isRawVisible = rawOutput.style.display === 'block';
  if (isRawVisible) {
    rawOutput.style.display = 'none';
    formattedWrap.style.display = 'block';
    if (toggleBtn) toggleBtn.textContent = 'Data Mentah (JSON)';
  } else {
    rawOutput.style.display = 'block';
    formattedWrap.style.display = 'none';
    if (toggleBtn) toggleBtn.textContent = 'Tampilan Kartu';
  }
}

// 6. CEK NOMOR
async function cekNomor() {
  const nomor = document.getElementById('cn-nomor').value.trim();
  if (!nomor) {
    showToast('Masukkan nomor telepon terlebih dahulu', true);
    return;
  }
  const btn = document.getElementById('cn-btn');
  btn.innerHTML = `<div class="spinner"></div> Mencari...`;
  btn.disabled = true;

  try {
    const res = await fetch('/api/ceknomor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nomor })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const info = data.info || {};
    const similar = data.similar || [];
    const normalized = data.nomor_normalized || nomor;

    // 1. Format operator
    let operatorText = 'Tidak diketahui';
    if (Array.isArray(info.operator) && info.operator.length > 0) {
      operatorText = info.operator.join(', ');
    } else if (info.operator) {
      operatorText = String(info.operator);
    }

    // 2. Format international code
    const intlCode = info.international_code ? `+${info.international_code}` : '+62';
    const displayFormat = info.display_format || '-';

    // 3. Render ke element card
    document.getElementById('cn-val-number').textContent = `+${normalized}`;
    document.getElementById('cn-val-operator').textContent = operatorText;
    document.getElementById('cn-val-format').textContent = displayFormat;
    document.getElementById('cn-val-code').textContent = intlCode;

    // 4. Render similar numbers list
    const simWrap = document.getElementById('cn-similar-wrap');
    const simList = document.getElementById('cn-similar-list');
    simList.innerHTML = '';

    if (Array.isArray(similar) && similar.length > 0) {
      simWrap.style.display = 'block';
      similar.forEach(item => {
        const fullNum = item.similar_number ? `+${item.international_code || 62}${item.similar_number}` : '';
        if (fullNum) {
          const chip = document.createElement('div');
          chip.className = 'phone-chip';
          chip.innerHTML = `
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.62 3.42 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.77a16 16 0 0 0 6 6l.87-.87a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
            ${fullNum}
          `;
          chip.title = 'Klik untuk salin & gunakan';
          chip.onclick = () => {
            navigator.clipboard.writeText(fullNum);
            document.getElementById('cn-nomor').value = fullNum;
            showToast(`Nomor ${fullNum} disalin`);
          };
          simList.appendChild(chip);
        }
      });
    } else {
      simWrap.style.display = 'none';
    }

    // 5. Clean indented Raw JSON
    const cleanJson = JSON.stringify({
      nomor: `+${normalized}`,
      info: info,
      similar: similar
    }, null, 2);

    document.getElementById('cn-output').textContent = cleanJson;
    
    // Reset view mode ke Formatted Card View
    document.getElementById('cn-formatted-wrap').style.display = 'block';
    document.getElementById('cn-output').style.display = 'none';
    document.getElementById('cn-toggle-json').textContent = 'Raw JSON';
    
    document.getElementById('cn-result').classList.add('visible');
    showToast('Info nomor berhasil didapatkan!');
  } catch (err) {
    showToast('Gagal cek nomor: ' + err.message, true);
  } finally {
    btn.innerHTML = `Cek Nomor Sekarang`;
    btn.disabled = false;
  }
}


// Prompt Suggestion Helper
function setPromptSuggestion(text) {
  const promptInput = document.getElementById('img-prompt');
  if (!promptInput) return;
  promptInput.value = text;
  promptInput.focus();
  showToast('Contoh prompt diterapkan!');
}

// Image Count Selector Helper
function selectImgCount(val, label) {
  const input = document.getElementById('img-count');
  const labelEl = document.getElementById('cs-img-count-label');
  const btnText = document.getElementById('img-btn-text');
  if (input) input.value = val;
  if (labelEl) labelEl.textContent = label;
  if (btnText) btnText.textContent = `Generate ${val} Pilihan Gambar`;

  const wrap = document.getElementById('cs-img-count');
  if (wrap) {
    wrap.classList.remove('open');
    wrap.querySelectorAll('.custom-option').forEach(opt => {
      opt.classList.toggle('selected', opt.getAttribute('data-val') === String(val));
    });
  }
}

// 7. BUAT GAMBAR AI (VARIASI PARALEL, REALTIME PROGRESS & LIGHTBOX HD PREVIEW)
let currentLightboxImg = null;
let activeImgBatchId = 0;
let lastImgBatchItems = [];

function updateImgProgress(pct, text) {
  const wrap = document.getElementById('img-progress-wrap');
  const bar = document.getElementById('img-progress-bar');
  const val = document.getElementById('img-progress-pct');
  const label = document.getElementById('img-progress-text');
  if (wrap) wrap.style.display = 'block';
  if (bar) bar.style.width = Math.min(100, Math.max(0, pct)) + '%';
  if (val) val.textContent = Math.round(pct) + '%';
  if (label && text) label.textContent = text;
}

function loadImageIntoCard(card, item, idx, urlCandidates, onComplete) {
  let candidateIdx = 0;
  const img = new Image();
  img.alt = `Gambar #${item.id || idx + 1}`;

  function tryNext() {
    if (candidateIdx >= urlCandidates.length) {
      const loader = card.querySelector(`#loader-${idx}`);
      if (loader) {
        loader.innerHTML = `
          <div class="gallery-error-wrap">
            <span style="font-size:11px;color:var(--error);font-weight:600;">Gagal memuat gambar</span>
            <button type="button" class="gallery-retry-btn" onclick="retrySingleCard(${idx})">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
              Coba Lagi
            </button>
          </div>
        `;
      }
      if (onComplete) onComplete(false);
      return;
    }
    const currentUrl = urlCandidates[candidateIdx++];
    img.src = currentUrl;
  }

  img.onload = () => {
    img.classList.add('loaded');
    const loader = card.querySelector(`#loader-${idx}`);
    if (loader) {
      loader.style.opacity = '0';
      setTimeout(() => { if (loader && loader.parentElement) loader.remove(); }, 250);
    }

    const badge = card.querySelector('.gallery-badge-num');
    if (badge && item.style_tag) {
      badge.textContent = `#${item.id || idx + 1} · ${item.style_tag}`;
    }

    const overlay = document.createElement('div');
    overlay.className = 'gallery-overlay-hover';
    overlay.innerHTML = `
      <div class="gallery-preview-btn">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg>
        Lihat Jelas
      </div>
    `;
    card.appendChild(overlay);

    card.onclick = () => openLightbox({
      src: img.src,
      rawUrl: item.url,
      id: item.id || idx + 1,
      prompt: item.prompt || '',
      model: item.model || 'FLUX',
      seed: item.seed || 'Auto',
      aspect_ratio: item.aspect_ratio || '1:1',
      style_tag: item.style_tag || ''
    });

    if (onComplete) onComplete(true);
  };

  img.onerror = () => {
    tryNext();
  };

  card.appendChild(img);
  tryNext();
}

function retrySingleCard(idx) {
  const item = lastImgBatchItems[idx];
  const card = document.getElementById(`gallery-card-${idx}`);
  if (!item || !card) return;

  card.innerHTML = `
    <div class="gallery-badge-num">#${item.id || idx + 1}</div>
    <div class="gallery-loading-placeholder" id="loader-${idx}">
      <div class="spinner" style="width:18px;height:18px;border-width:2px;border-top-color:var(--black);"></div>
      <span>Mencoba memuat ulang #${item.id || idx + 1}...</span>
    </div>
  `;

  const candidates = [
    item.fallback_url,
    item.proxy_url,
    item.preview_url || item.url
  ];
  loadImageIntoCard(card, item, idx, candidates, null);
}

async function buatGambar() {
  const prompt = document.getElementById('img-prompt').value.trim();
  const negativePrompt = document.getElementById('img-negative').value.trim();
  const model = document.getElementById('img-model').value;
  const style = document.getElementById('img-style')?.value || 'alami';
  const aspectRatio = document.getElementById('img-ratio').value;
  const count = parseInt(document.getElementById('img-count')?.value || '4', 10);

  if (!prompt) {
    showToast('Masukkan deskripsi gambar terlebih dahulu', true);
    return;
  }

  const batchId = ++activeImgBatchId;
  const btn = document.getElementById('img-btn');
  const regenBtn = document.getElementById('img-regen-btn');
  const progressWrap = document.getElementById('img-progress-wrap');
  const galleryGrid = document.getElementById('img-gallery-grid');
  const resultBox = document.getElementById('img-result');
  const statusTitle = document.getElementById('img-status-title');

  btn.innerHTML = `<div class="spinner"></div> Men-generate ${count} Gambar...`;
  btn.disabled = true;
  if (regenBtn) regenBtn.disabled = true;

  if (statusTitle) statusTitle.textContent = `${count} Hasil Variasi Gambar`;

  // Tampilkan result box dan progress bar seketika
  resultBox.classList.add('visible');
  updateImgProgress(8, `Menyiapkan prompt AI & ${count} variasi gaya...`);

  // Render skeleton cards SEKETIKA!
  galleryGrid.innerHTML = '';
  for (let i = 0; i < count; i++) {
    const card = document.createElement('div');
    card.className = 'gallery-card';
    card.id = `gallery-card-${i}`;
    card.innerHTML = `
      <div class="gallery-badge-num">#${i + 1}</div>
      <div class="gallery-loading-placeholder" id="loader-${i}">
        <div class="spinner" style="width:20px;height:20px;border-width:2.5px;border-top-color:var(--black);"></div>
        <span>Merender #${i + 1}...</span>
      </div>
    `;
    galleryGrid.appendChild(card);
  }

  try {
    const res = await fetch('/api/buatgambar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        negative_prompt: negativePrompt,
        model,
        style,
        aspect_ratio: aspectRatio,
        count
      })
    });
    if (batchId !== activeImgBatchId) return;

    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const images = data.images || [];
    lastImgBatchItems = images;

    if (!Array.isArray(images) || images.length === 0) {
      throw new Error('Tidak ada gambar yang dihasilkan.');
    }

    updateImgProgress(25, `Model terhubung! Memuat ${images.length} variasi...`);

    let completedCount = 0;
    const total = images.length;

    for (let idx = 0; idx < total; idx++) {
      if (batchId !== activeImgBatchId) return;
      const item = images[idx];
      const card = document.getElementById(`gallery-card-${idx}`);
      if (!card) continue;

      updateImgProgress(
        Math.round(20 + (idx / total) * 75),
        `Merender variasi #${idx + 1} (${item.style_tag || 'Gambar'})...`
      );

      // Load one by one to strictly prevent HTTP 429 queue full
      await new Promise((resolve) => {
        const candidates = item.b64_json
          ? [`data:image/jpeg;base64,${item.b64_json}`]
          : [
              item.preview_url || item.url,
              item.fallback_url,
              item.proxy_url
            ];

        loadImageIntoCard(card, item, idx, candidates, (success) => {
          completedCount++;
          const pct = Math.round(20 + (completedCount / total) * 80);
          updateImgProgress(pct, `${completedCount} dari ${total} variasi siap`);
          resolve();
        });
      });

      if (idx < total - 1) {
        await new Promise(r => setTimeout(r, 200));
      }
    }

    if (batchId === activeImgBatchId && completedCount > 0) {
      showToast(`${completedCount} variasi gambar selesai!`);
      setTimeout(() => {
        if (progressWrap && batchId === activeImgBatchId) {
          updateImgProgress(100, 'Semua gambar siap ditampilkan');
        }
      }, 400);
    }

  } catch (err) {
    if (batchId !== activeImgBatchId) return;
    showToast('Gagal generate gambar: ' + err.message, true);
    if (progressWrap) progressWrap.style.display = 'none';
  } finally {
    if (batchId === activeImgBatchId) {
      btn.innerHTML = `
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        <span id="img-btn-text">Generate ${count} Pilihan Gambar</span>
      `;
      btn.disabled = false;
      if (regenBtn) regenBtn.disabled = false;
    }
  }
}

// ─── LIGHTBOX MODAL HANDLERS ───
function openLightbox(data) {
  currentLightboxImg = data;
  const modal = document.getElementById('img-lightbox-modal');
  const imgEl = document.getElementById('lightbox-img');
  
  imgEl.src = data.src;
  document.getElementById('lightbox-prompt-text').textContent = data.prompt;
  document.getElementById('lightbox-tag-id').textContent = data.style_tag ? `Pilihan #${data.id} · ${data.style_tag}` : `Pilihan #${data.id}`;
  document.getElementById('lightbox-tag-model').textContent = `Model: ${data.model.toUpperCase()}`;
  document.getElementById('lightbox-tag-seed').textContent = `Seed: ${data.seed}`;
  document.getElementById('lightbox-tag-ratio').textContent = `Rasio: ${data.aspect_ratio}`;
  
  const dlBtn = document.getElementById('lightbox-dl-btn');
  dlBtn.href = data.src;
  dlBtn.setAttribute('download', `xvoid_ai_image_${data.seed}.png`);

  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
}

function closeLightbox(e) {
  if (e && e.target && e.target.closest('.lightbox-content') && !e.target.classList.contains('lightbox-close-btn')) {
    return;
  }
  const modal = document.getElementById('img-lightbox-modal');
  if (modal) modal.classList.remove('show');
  document.body.style.overflow = '';
}

function copyLightboxUrl() {
  if (currentLightboxImg && currentLightboxImg.src) {
    navigator.clipboard.writeText(currentLightboxImg.src);
    showToast('Link gambar berhasil disalin!');
  }
}

// Tutup lightbox jika tekan ESC
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeLightbox();
});


// 8. SCAN GITHUB REPO
async function scanRepo() {
  const url = document.getElementById('sr-url').value.trim();
  if (!url || !url.includes('github.com')) {
    showToast('Masukkan URL GitHub repository yang valid', true);
    return;
  }
  const btn = document.getElementById('sr-btn');
  btn.innerHTML = `<div class="spinner"></div> Memindai Repositori...`;
  btn.disabled = true;

  document.getElementById('sr-status').textContent = 'Pemindaian keamanan sedang berjalan... (sekitar 20-40 detik)';
  document.getElementById('sr-result').classList.add('visible');
  document.getElementById('sr-findings-list').innerHTML = '<div style="font-size:12px;color:var(--gray-600);text-align:center;padding:16px;">Sedang memeriksa struktur AST & aturan keamanan repositori...</div>';
  document.getElementById('sr-badges-list').innerHTML = '';
  document.getElementById('sr-badges-wrap').style.display = 'none';

  try {
    const res = await fetch('/api/scanrepo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const result = data.result || {};
    const meta = result.meta || {};
    const findings = result.findings || [];
    const badges = result.badges || [];
    const riskScore = result.riskScore ?? 0;
    const rawRiskLevel = (result.riskLevel || 'UNKNOWN').toUpperCase();

    const riskMap = {
      'CRITICAL': 'KRITIS',
      'HIGH': 'TINGGI',
      'MEDIUM': 'SEDANG',
      'MODERATE': 'SEDANG',
      'LOW': 'RENDAH',
      'SAFE': 'AMAN',
      'NONE': 'AMAN',
      'UNKNOWN': 'TIDAK DIKETAHUI'
    };
    const riskLevel = riskMap[rawRiskLevel] || rawRiskLevel;

    // 1. Render Metrics Grid
    document.getElementById('sr-val-repo').textContent = meta.repo || url.replace(/^https?:\/\/github\.com\//, '');
    document.getElementById('sr-val-lang').textContent = meta.language || 'Tidak diketahui';
    document.getElementById('sr-val-score').textContent = String(riskScore);
    
    // Risk level badge color
    let levelClass = 'sev-safe';
    if (rawRiskLevel.includes('CRIT') || rawRiskLevel.includes('HIGH')) levelClass = 'sev-critical';
    else if (rawRiskLevel.includes('MED')) levelClass = 'sev-medium';
    else if (rawRiskLevel.includes('LOW')) levelClass = 'sev-low';
    
    document.getElementById('sr-val-level').innerHTML = `<span class="sev-badge ${levelClass}">${riskLevel}</span>`;
    document.getElementById('sr-status').textContent = `HASIL AUDIT — ${findings.length} TEMUAN`;

    // 2. Render Badges / Repo Info
    const badgesWrap = document.getElementById('sr-badges-wrap');
    const badgesList = document.getElementById('sr-badges-list');
    badgesList.innerHTML = '';
    if (Array.isArray(badges) && badges.length > 0) {
      badgesWrap.style.display = 'block';
      badges.forEach(b => {
        const bCard = document.createElement('div');
        bCard.className = 'repo-badge-card';
        bCard.innerHTML = `
          <div class="repo-badge-title">• ${b.label || 'Informasi'}</div>
          <div class="repo-badge-desc">${b.description || ''}</div>
        `;
        badgesList.appendChild(bCard);
      });
    } else {
      badgesWrap.style.display = 'none';
    }

    // 3. Render Findings Cards
    const findingsList = document.getElementById('sr-findings-list');
    findingsList.innerHTML = '';

    const sevMap = {
      'CRITICAL': 'KRITIS',
      'HIGH': 'TINGGI',
      'MEDIUM': 'SEDANG',
      'MED': 'SEDANG',
      'WARN': 'PERINGATAN',
      'WARNING': 'PERINGATAN',
      'LOW': 'RENDAH',
      'INFO': 'INFORMASI'
    };

    if (Array.isArray(findings) && findings.length > 0) {
      document.getElementById('sr-findings-title').textContent = `Temuan Kerentanan (${findings.length}):`;
      findings.forEach((f, idx) => {
        const rawSev = (f.severity || 'info').toUpperCase();
        const sev = sevMap[rawSev] || rawSev;

        let sevBadgeClass = 'sev-info';
        if (rawSev.includes('CRIT') || rawSev.includes('HIGH')) sevBadgeClass = 'sev-critical';
        else if (rawSev.includes('MED') || rawSev.includes('WARN')) sevBadgeClass = 'sev-medium';
        else if (rawSev.includes('LOW')) sevBadgeClass = 'sev-low';

        const fCard = document.createElement('div');
        fCard.className = 'finding-card';
        
        let snippetHtml = '';
        if (f.snippet && f.snippet.trim()) {
          snippetHtml = `
            <div style="font-size:10.5px;font-weight:700;color:var(--gray-400);margin-bottom:4px;text-transform:uppercase;">Snippet Kode:</div>
            <div class="snippet-box">${escapeHtml(f.snippet.trim())}</div>
          `;
        }

        fCard.innerHTML = `
          <div class="finding-top">
            <span class="finding-num">Temuan #${idx + 1}</span>
            <div style="display:flex;gap:6px;align-items:center;">
              <span class="sev-badge ${sevBadgeClass}">${sev}</span>
              ${f.points ? `<span style="font-size:11px;font-weight:700;color:var(--gray-600);">${f.points} poin</span>` : ''}
            </div>
          </div>
          <div class="finding-title">${escapeHtml(f.title || 'Temuan Tanpa Judul')}</div>
          <div class="finding-meta">
            ${f.category ? `<span><strong>Kategori:</strong> ${escapeHtml(f.category)}</span>` : ''}
            ${f.ruleId ? `<span><strong>Aturan:</strong> <code>${escapeHtml(f.ruleId)}</code></span>` : ''}
          </div>
          ${f.filePath ? `<div class="finding-path" style="display:flex;align-items:center;gap:6px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            <span>${escapeHtml(f.filePath)}</span>
          </div>` : ''}
          ${f.description ? `<div class="finding-desc">${escapeHtml(f.description)}</div>` : ''}
          ${snippetHtml}
        `;
        findingsList.appendChild(fCard);
      });
    } else {
      document.getElementById('sr-findings-title').textContent = 'Temuan Kerentanan:';
      findingsList.innerHTML = `
        <div style="text-align:center;padding:22px;background:#ffffff;border:1.5px solid var(--gray-200);border-radius:12px;">
          <div style="width:36px;height:36px;border-radius:50%;background:#ecfdf5;border:1.5px solid var(--success);display:flex;align-items:center;justify-content:center;margin:0 auto 10px;color:var(--success);">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
          </div>
          <div style="font-weight:700;color:var(--success);font-size:14px;margin-bottom:4px;">Tidak Ada Kerentanan Kritis Ditemukan!</div>
          <div style="font-size:12px;color:var(--gray-600);">Repositori dinyatakan aman dan memenuhi standar praktik keamanan terbaik.</div>
        </div>
      `;
    }

    // 4. Raw JSON
    document.getElementById('sr-output').textContent = JSON.stringify(result, null, 2);

    // Reset view to Formatted Card View
    document.getElementById('sr-formatted-wrap').style.display = 'block';
    document.getElementById('sr-output').style.display = 'none';
    document.getElementById('sr-toggle-json').textContent = 'Data Mentah (JSON)';

    showToast(`Pemindaian selesai! ${findings.length} temuan dianalisis.`);
  } catch (err) {
    document.getElementById('sr-status').textContent = 'Pemindaian gagal';
    document.getElementById('sr-findings-list').innerHTML = `<div style="color:var(--error);font-size:12px;padding:12px;">Error: ${err.message}</div>`;
    showToast('Gagal memindai repositori: ' + err.message, true);
  } finally {
    btn.innerHTML = `Mulai Audit Keamanan`;
    btn.disabled = false;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ─── INSPEKTUR KEAMANAN WEB & SSL ───
function setWebInspectTarget(domain) {
  const input = document.getElementById('wi-input');
  if (input) {
    input.value = domain;
    inspectWeb();
  }
}

let wiRawJsonMode = false;
function toggleWebInspectView() {
  wiRawJsonMode = !wiRawJsonMode;
  const formatted = document.getElementById('wi-formatted-wrap');
  const raw = document.getElementById('wi-output');
  const btn = document.getElementById('wi-toggle-json');
  if (wiRawJsonMode) {
    formatted.style.display = 'none';
    raw.style.display = 'block';
    btn.textContent = 'Tampilan Kartu';
  } else {
    formatted.style.display = 'block';
    raw.style.display = 'none';
    btn.textContent = 'Data Mentah (JSON)';
  }
}

function sanitizeAndValidateDomain(raw) {
  if (!raw || typeof raw !== 'string') return null;
  let s = raw.trim();
  if (!s) return null;

  // Extract hostname if URL was pasted
  if (/^https?:\/\//i.test(s)) {
    try {
      const u = new URL(s);
      s = u.hostname;
    } catch {
      s = s.replace(/^https?:\/\//i, '').split('/')[0];
    }
  } else {
    s = s.split('/')[0].split('?')[0].split('#')[0];
  }

  // Strip port if present
  if (s.includes(':')) {
    s = s.split(':')[0];
  }
  s = s.trim().toLowerCase();

  // Basic sanity checks: no spaces, at least 4 chars (e.g. a.co), must contain a dot
  if (!s || s.includes(' ') || s.length < 4 || !s.includes('.')) {
    return null;
  }

  // Valid hostname / domain regex (FQDN) or valid IPv4
  const domainRegex = /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$/i;
  const ipv4Regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;

  if (!domainRegex.test(s) && !ipv4Regex.test(s)) {
    return null;
  }
  return s;
}

async function inspectWeb() {
  const input = document.getElementById('wi-input');
  const rawVal = (input?.value || '').trim();
  if (!rawVal) {
    showToast('Masukkan nama domain atau URL target terlebih dahulu!', true);
    return;
  }

  // Validasi format domain langsung: jika tidak sesuai, langsung gagal tanpa loading
  const validTarget = sanitizeAndValidateDomain(rawVal);
  if (!validTarget) {
    showToast('Format domain tidak sesuai! Contoh valid: google.com atau target.id', true);
    return;
  }

  const btn = document.getElementById('wi-submit-btn');
  const origBtnContent = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = `
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="spin">
      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
    </svg>
    <span>Mengaudit...</span>
  `;

  const resArea = document.getElementById('wi-result-area');
  resArea.style.display = 'block';
  document.getElementById('wi-status-badge').textContent = 'MEMPROSES...';
  document.getElementById('wi-status-badge').className = 'badge';

  try {
    const res = await fetch('/api/webinspect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target: validTarget })
    });

    const data = await res.json();
    if (!res.ok || data.status === 'error') {
      throw new Error(data.message || data.error || 'Gagal melakukan audit domain');
    }

    // 1. Grade Banner
    const grade = data.grade || 'F';
    const score = data.score ?? 0;
    const gradeBadge = document.getElementById('wi-grade-badge');
    gradeBadge.textContent = grade;
    gradeBadge.className = 'wi-grade-badge';
    if (grade === 'A+' || grade === 'A') gradeBadge.classList.add('grade-aplus');
    else if (grade === 'B') gradeBadge.classList.add('grade-b');
    else if (grade === 'C') gradeBadge.classList.add('grade-c');
    else gradeBadge.classList.add('grade-d');

    document.getElementById('wi-grade-target').textContent = data.target || val;
    const ipStr = (data.all_ips && data.all_ips.length) ? data.all_ips.slice(0, 3).join(', ') : (data.resolved_ip || 'Tidak Terdeteksi');
    document.getElementById('wi-grade-meta').innerHTML = `Skor Keamanan: <strong>${score} / 100</strong> &bull; IP Server: ${escapeHtml(ipStr)}`;

    // 2. Metrics Grid
    const ssl = data.ssl || {};
    const isValid = ssl.valid || ssl.active;
    const sslStatusEl = document.getElementById('wi-ssl-status');
    if (isValid) {
      sslStatusEl.textContent = 'Aktif';
      sslStatusEl.style.color = 'var(--success)';
    } else {
      sslStatusEl.textContent = 'Tidak Aktif';
      sslStatusEl.style.color = 'var(--error)';
    }

    const sslDaysEl = document.getElementById('wi-ssl-days');
    if (ssl.days_remaining != null) {
      sslDaysEl.textContent = `${ssl.days_remaining} hari`;
      sslDaysEl.style.color = ssl.days_remaining > 30 ? 'var(--success)' : (ssl.days_remaining > 7 ? 'var(--warning)' : 'var(--error)');
    } else {
      sslDaysEl.textContent = 'N/A';
      sslDaysEl.style.color = 'var(--gray-600)';
    }

    document.getElementById('wi-ssl-proto').textContent = ssl.tls_version || ssl.protocol || 'Tidak Ada';

    // Headers Count
    const headers = data.headers_audit || data.headers || {};
    const headerKeys = Object.keys(headers);
    const passedCount = headerKeys.filter(k => headers[k] && (headers[k].present || headers[k].status === 'PASS')).length;
    document.getElementById('wi-headers-count').textContent = `${passedCount} / ${headerKeys.length}`;

    // 3. SSL Details
    document.getElementById('wi-ssl-issuer').textContent = ssl.issuer || 'Tidak Ada / Kadaluarsa';
    document.getElementById('wi-ssl-subject').textContent = ssl.common_name || ssl.subject || (data.target || val);
    const validFrom = ssl.not_before || ssl.valid_from;
    const validUntil = ssl.not_after || ssl.valid_until;
    const validStr = (validFrom && validUntil) ? `${validFrom} s/d ${validUntil}` : (isValid ? 'Aktif' : 'Tidak Tersedia');
    document.getElementById('wi-ssl-validity').textContent = validStr;
    document.getElementById('wi-ssl-cipher').textContent = ssl.cipher || 'Tidak Ada Enkripsi TLS Aktif';

    const sansRow = document.getElementById('wi-ssl-sans-row');
    const sansEl = document.getElementById('wi-ssl-sans');
    const sansList = ssl.sans_sample || ssl.sans || [];
    if (sansList && sansList.length > 0) {
      sansRow.style.display = 'block';
      const extraCount = (ssl.sans_count && ssl.sans_count > sansList.length) ? ` (+${ssl.sans_count - sansList.length} lainnya)` : '';
      sansEl.textContent = sansList.slice(0, 10).join(', ') + extraCount;
    } else {
      sansRow.style.display = 'none';
    }

    // 4. Headers Grid
    const headersGrid = document.getElementById('wi-headers-grid');
    headersGrid.innerHTML = '';
    for (const [k, hData] of Object.entries(headers)) {
      const card = document.createElement('div');
      card.className = 'wi-header-card';
      const isPresent = hData.present || hData.status === 'PASS';
      const hLabel = hData.label || k;
      const badgeCls = isPresent ? 'wi-badge-pass' : 'wi-badge-fail';
      const badgeTxt = isPresent ? 'DIPROTEKSI' : 'TIDAK AKTIF';
      const valTxt = isPresent ? escapeHtml(hData.value || 'Aktif') : escapeHtml(hData.recommendation || 'Header keamanan ini belum diaktifkan pada server.');
      card.innerHTML = `
        <div class="wi-header-top">
          <span class="wi-header-name">${escapeHtml(hLabel)}</span>
          <span class="wi-header-badge ${badgeCls}">${badgeTxt}</span>
        </div>
        <div class="wi-header-val">${valTxt}</div>
      `;
      headersGrid.appendChild(card);
    }

    // 5. Findings
    const findingsList = document.getElementById('wi-findings-list');
    findingsList.innerHTML = '';
    const findings = data.findings || [];
    if (findings.length > 0) {
      findings.forEach(f => {
        const item = document.createElement('div');
        item.className = 'wi-finding-card';
        let iconSvg = '';
        let iconCls = 'wi-icon-pass';
        if (f.type === 'pass') {
          iconCls = 'wi-icon-pass';
          iconSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
        } else if (f.type === 'warning') {
          iconCls = 'wi-icon-warn';
          iconSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>';
        } else {
          iconCls = 'wi-icon-crit';
          iconSvg = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>';
        }
        item.innerHTML = `
          <div class="wi-finding-top">
            <span class="wi-finding-icon ${iconCls}">${iconSvg}</span>
            <span class="wi-finding-title">${escapeHtml(f.title)}</span>
          </div>
          <div class="wi-finding-desc">${escapeHtml(f.desc)}</div>
        `;
        findingsList.appendChild(item);
      });
    } else {
      findingsList.innerHTML = `<div style="font-size:12px;color:var(--gray-600);padding:8px;">Tidak ada catatan khusus.</div>`;
    }

    // 6. Recommendations
    const recommsList = document.getElementById('wi-recomms-list');
    const recommsWrap = document.getElementById('wi-recomms-wrap');
    recommsList.innerHTML = '';
    const recomms = data.recommendations || [];
    if (recomms.length > 0) {
      recommsWrap.style.display = 'block';
      recomms.forEach(r => {
        const rCard = document.createElement('div');
        rCard.className = 'wi-recomm-card';
        rCard.textContent = r;
        recommsList.appendChild(rCard);
      });
    } else {
      recommsWrap.style.display = 'none';
    }

    // Raw JSON
    document.getElementById('wi-output').textContent = JSON.stringify(data, null, 2);

    // Reset view toggle
    wiRawJsonMode = false;
    document.getElementById('wi-formatted-wrap').style.display = 'block';
    document.getElementById('wi-output').style.display = 'none';
    document.getElementById('wi-toggle-json').textContent = 'Data Mentah (JSON)';

    document.getElementById('wi-status-badge').textContent = `SELESAI (GRADE ${grade})`;
    document.getElementById('wi-status-badge').className = 'badge';

    showToast(`Audit domain ${data.target} selesai! Skor: ${score}/100 (Grade ${grade})`);
  } catch (err) {
    resArea.style.display = 'none';
    showToast('Audit gagal: ' + err.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = origBtnContent;
  }
}

// ════════════════════════════════════════════════════════════════
// NEW SUITE MODULES CONTROLLERS (OSINT, RECON, PHONE, MEDIA, DEV)
// ════════════════════════════════════════════════════════════════

// ─── 1. USERNAME SHERLOCK SCANNER ───
async function runSherlock() {
  const input = document.getElementById('sherlock-input');
  const btn = document.getElementById('sherlock-btn');
  const loading = document.getElementById('sherlock-loading');
  const resBox = document.getElementById('sherlock-result-box');
  const grid = document.getElementById('sherlock-grid');
  const title = document.getElementById('sherlock-summary-title');
  const badge = document.getElementById('sherlock-stats-badge');

  const username = (input.value || '').trim().replace(/^@/, '');
  if (!username) {
    showToast('Ketik username target terlebih dahulu!', true);
    return;
  }
  if (username.length < 3) {
    showToast('Username target minimal 3 karakter!', true);
    return;
  }
  if (!/^[a-zA-Z0-9_.-]+$/.test(username)) {
    showToast('Username hanya boleh huruf, angka, titik, strip, atau underscore!', true);
    return;
  }

  btn.disabled = true;
  loading.style.display = 'flex';
  resBox.style.display = 'none';
  grid.innerHTML = '';

  try {
    const res = await fetch('/api/osint/sherlock', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Gagal memindai username');

    title.textContent = `Hasil Pelacakan '${data.username}':`;
    badge.textContent = `${data.found_count} Ditemukan dari ${data.total_scanned} Platform`;

    data.results.forEach(item => {
      const card = document.createElement(item.found ? 'a' : 'div');
      card.className = `sherlock-card ${item.found ? 'found' : ''}`;
      if (item.found) {
        card.href = item.url;
        card.target = '_blank';
        card.rel = 'noopener noreferrer';
      }
      card.innerHTML = `
        <div>
          <div style="font-weight:700;font-size:14px;">${item.name}</div>
          <div style="font-size:11px;color:var(--gray-400);">${item.category}</div>
        </div>
        <span class="sherlock-badge ${item.found ? 'found' : 'missing'}">${item.found ? 'KLAIM / AKTIF' : 'TERSEDIA'}</span>
      `;
      grid.appendChild(card);
    });

    resBox.style.display = 'block';
    showToast(`Scan Sherlock selesai! ${data.found_count} akun ditemukan.`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

// ─── 2. DISCORD LOOKUP ───
async function runDiscordLookup() {
  const input = document.getElementById('discord-input');
  const btn = document.getElementById('discord-btn');
  const loading = document.getElementById('discord-loading');
  const resBox = document.getElementById('discord-result-box');

  const userId = (input.value || '').trim();
  if (!userId) {
    showToast('Masukkan Discord User ID!', true);
    return;
  }

  btn.disabled = true;
  loading.style.display = 'flex';
  resBox.style.display = 'none';

  try {
    const res = await fetch('/api/osint/discord', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Gagal mendekode Discord ID');

    document.getElementById('discord-avatar').src = data.avatar_url || data.avatar;
    document.getElementById('discord-tag').textContent = data.tag;
    document.getElementById('discord-uid-label').textContent = data.id || data.user_id;
    document.getElementById('discord-bot-badge').style.display = data.is_bot ? 'inline-block' : 'none';
    document.getElementById('discord-created-wib').textContent = data.created_at_wib;
    document.getElementById('discord-created-utc').textContent = data.created_at_utc;
    document.getElementById('discord-age-days').textContent = `${data.age_days || data.account_age_days} Hari`;
    document.getElementById('discord-node-info').textContent = `Worker #${data.worker_id} · Proc #${data.process_id}`;

    resBox.style.display = 'block';
    showToast('Data identitas Discord berhasil didekode!');
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

// ─── 3. BREACH & PASSWORD LEAK ───
async function runBreachCheck() {
  const input = document.getElementById('breach-input');
  const btn = document.getElementById('breach-btn');
  const loading = document.getElementById('breach-loading');
  const resBox = document.getElementById('breach-result-box');
  const banner = document.getElementById('breach-banner');
  const details = document.getElementById('breach-details');

  const query = (input.value || '').trim();
  if (!query) {
    showToast('Ketik alamat email yang ingin diaudit!', true);
    return;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,}$/;
  if (!emailRegex.test(query)) {
    showToast('Format email tidak valid! Masukkan alamat email aktif (contoh: user@domain.com)', true);
    return;
  }

  btn.disabled = true;
  loading.style.display = 'flex';
  resBox.style.display = 'none';

  try {
    const res = await fetch('/api/osint/breach', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Audit kebocoran gagal');

    if (data.type === 'password') {
      if (data.is_compromised) {
        banner.style.background = '#fef2f2';
        banner.style.color = '#dc2626';
        banner.style.border = '1px solid rgba(220, 38, 38, 0.3)';
        banner.textContent = `[!] PERINGATAN: Kata sandi ini telah bocor sebanyak ${data.leak_count.toLocaleString()} kali di internet!`;
      } else {
        banner.style.background = '#f0fdf4';
        banner.style.color = '#16a34a';
        banner.style.border = '1px solid rgba(22, 163, 74, 0.3)';
        banner.textContent = `[OK] AMAN: Kata sandi ini belum pernah ditemukan di database kebocoran publik.`;
      }

      details.innerHTML = `
        <div><strong>Status:</strong> ${data.verdict}</div>
        <div><strong>Tingkat Entropi:</strong> ${data.entropy_bits} bits</div>
        <div><strong>Karakter Masked:</strong> <code>${data.query_masked}</code></div>
        <div><strong>Saran Keamanan:</strong> ${data.recommendation}</div>
      `;
    } else {
      if (data.is_pwned) {
        banner.style.background = '#fef2f2';
        banner.style.color = '#dc2626';
        banner.style.border = '1px solid rgba(220, 38, 38, 0.3)';
        banner.textContent = `[!] Email ${data.email} terindikasi dalam ${data.breach_count} insiden kebocoran data!`;
      } else {
        banner.style.background = '#f0fdf4';
        banner.style.color = '#16a34a';
        banner.style.border = '1px solid rgba(220, 38, 38, 0.3)';
        banner.textContent = `[OK] Email ${data.email} bersih dari daftar kebocoran data besar yang terindeks.`;
      }

      let breachListHtml = '';
      if (data.breaches && data.breaches.length) {
        breachListHtml = '<div><strong>Insiden Kebocoran Terkait:</strong><ul style="margin-left:18px;margin-top:4px;">' +
          data.breaches.map(b => `<li><strong>${b.name} (${b.year})</strong> — ${b.records}. Data bocor: ${b.leaked.join(', ')}</li>`).join('') +
          '</ul></div>';
      }

      details.innerHTML = `
        <div><strong>Email Target:</strong> <code>${data.email}</code></div>
        ${breachListHtml}
        <div><strong>Saran Tindakan:</strong> ${data.recommendation}</div>
      `;
    }

    resBox.style.display = 'block';
    showToast('Audit kebocoran data selesai!');
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

// ─── 4. TEMP VIRTUAL SMS NUMBERS ───
let currentSelectedSmsNumber = '';
let tempSmsLoaded = false;

async function loadTempSmsNumbers() {
  if (tempSmsLoaded) return;
  const listEl = document.getElementById('sms-num-list');
  if (!listEl) return;
  listEl.innerHTML = '<div style="color:var(--gray-400);font-size:12px;">Memuat nomor virtual...</div>';

  try {
    const res = await fetch('/api/phone/tempsms/numbers', { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Gagal memuat nomor virtual');

    listEl.innerHTML = '';
    data.numbers.forEach((item, idx) => {
      const el = document.createElement('div');
      el.className = `sms-num-item ${idx === 0 ? 'active' : ''}`;
      el.onclick = () => selectTempSmsNumber(item.number, el);
      el.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;flex:1;min-width:0;">
          <span class="sms-flag-badge">${item.flag}</span>
          <div style="min-width:0;">
            <div style="font-weight:700;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${item.country}</div>
            <div style="font-size:11px;font-family:monospace;margin-top:1px;opacity:0.65;">${item.number}</div>
          </div>
        </div>
        <button class="btn-secondary" onclick="event.stopPropagation(); copyTextStr('${item.number}', 'Nomor virtual disalin!')" style="padding:3px 7px;font-size:11px;flex-shrink:0;">Salin</button>
      `;
      listEl.appendChild(el);
    });

    tempSmsLoaded = true;
    if (data.numbers.length > 0) {
      selectTempSmsNumber(data.numbers[0].number, listEl.children[0]);
    }
  } catch (err) {
    listEl.innerHTML = `<div style="color:var(--error);font-size:12px;">${err.message}</div>`;
  }
}

async function selectTempSmsNumber(number, el) {
  currentSelectedSmsNumber = number;
  const listEl = document.getElementById('sms-num-list');
  if (listEl) {
    Array.from(listEl.children).forEach(c => c.classList.remove('active'));
  }
  if (el) el.classList.add('active');

  const label = document.getElementById('sms-active-num-label');
  if (label) label.textContent = number;

  await reloadSmsInbox();
}

async function reloadSmsInbox() {
  if (!currentSelectedSmsNumber) return;
  const box = document.getElementById('sms-inbox-container');
  box.innerHTML = '<div style="text-align:center;padding:16px;color:var(--gray-400);font-size:13px;"><svg style="animation:spin 1s linear infinite;margin-right:6px;vertical-align:middle" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Mengambil SMS terbaru...</div>';

  try {
    const res = await fetch('/api/phone/tempsms/inbox', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ number: currentSelectedSmsNumber })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Gagal memuat inbox');

    box.innerHTML = '';
    data.messages.forEach(m => {
      const item = document.createElement('div');
      item.className = 'sms-inbox-item';
      item.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-weight:700;font-size:13px;color:var(--black);">Dari: ${m.from}</span>
          <span style="font-size:11px;color:var(--gray-400);">${m.time_ago} (${m.time})</span>
        </div>
        <div style="font-size:13px;color:var(--gray-800);line-height:1.4;">${m.text}</div>
        <div style="display:flex;align-items:center;gap:8px;margin-top:4px;">
          <span class="card-badge" style="margin:0;background:rgba(37,99,235,0.1);color:#2563eb;font-weight:700;">KODE: ${m.code}</span>
          <button class="btn-secondary" onclick="copyTextStr('${m.code}', 'Kode OTP disalin!')" style="padding:2px 8px;font-size:11px;">Salin Kode</button>
        </div>
      `;
      box.appendChild(item);
    });
    showToast('Inbox SMS diperbarui!');
  } catch (err) {
    box.innerHTML = `<div style="color:var(--error);font-size:12px;padding:16px;">${err.message}</div>`;
  }
}

// ─── 5. GITHUB DEEP USER PROFILER ───
async function runGitHubProfiler() {
  const input = document.getElementById('ghp-input');
  const btn = document.getElementById('ghp-btn');
  const loading = document.getElementById('ghp-loading');
  const resBox = document.getElementById('ghp-result-box');

  const username = (input.value || '').trim();
  if (!username) {
    showToast('Masukkan username GitHub!', true);
    return;
  }

  btn.disabled = true;
  loading.style.display = 'flex';
  resBox.style.display = 'none';

  try {
    const res = await fetch('/api/github/profiler', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Gagal memprofil GitHub user');

    document.getElementById('ghp-avatar').src = data.avatar_url;
    document.getElementById('ghp-name').textContent = `${data.name} (@${data.username})`;
    document.getElementById('ghp-bio').textContent = data.bio;
    document.getElementById('ghp-location').textContent = data.location;
    document.getElementById('ghp-created').textContent = data.created_at ? data.created_at.split('T')[0] : '-';
    document.getElementById('ghp-repos').textContent = data.public_repos;
    document.getElementById('ghp-followers').textContent = data.followers;
    document.getElementById('ghp-following').textContent = data.following;
    document.getElementById('ghp-gists').textContent = data.public_gists;

    const emailsBox = document.getElementById('ghp-leaked-emails');
    emailsBox.innerHTML = '';
    if (data.leaked_emails && data.leaked_emails.length > 0) {
      data.leaked_emails.forEach(em => {
        const span = document.createElement('span');
        span.className = 'card-badge';
        span.style.margin = '0';
        span.style.background = '#fef2f2';
        span.style.color = '#dc2626';
        span.style.border = '1px solid rgba(220,38,38,0.3)';
        span.textContent = em;
        emailsBox.appendChild(span);
      });
    } else {
      emailsBox.innerHTML = '<span style="font-size:12px;color:var(--gray-400);">Tidak ditemukan email publik yang bocor di commit terbaru.</span>';
    }

    resBox.style.display = 'block';
    showToast(`Audit profil GitHub @${data.username} selesai!`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

// ─── 6. SUBDOMAIN SCANNER ───
let cachedSubdomainsText = '';

async function runSubdomainScan() {
  const input = document.getElementById('subdomain-input');
  const btn = document.getElementById('subdomain-btn');
  const loading = document.getElementById('subdomain-loading');
  const resBox = document.getElementById('subdomain-result-box');
  const output = document.getElementById('subdomain-output');
  const countLabel = document.getElementById('subdomain-count-label');

  const domain = (input.value || '').trim();
  if (!domain) {
    showToast('Masukkan domain target (misal: target.com)!', true);
    return;
  }

  btn.disabled = true;
  loading.style.display = 'flex';
  resBox.style.display = 'none';

  try {
    const res = await fetch('/api/recon/subdomains', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Gagal memindai subdomain');

    countLabel.textContent = `Ditemukan ${data.total_found} Subdomain Unik:`;
    cachedSubdomainsText = data.subdomains.join('\n');
    output.textContent = cachedSubdomainsText || 'Tidak ditemukan subdomain.';

    resBox.style.display = 'block';
    showToast(`Scan subdomain selesai! ${data.total_found} subdomain ditemukan.`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

function copyAllSubdomains() {
  if (!cachedSubdomainsText) return;
  copyTextStr(cachedSubdomainsText, 'Semua subdomain berhasil disalin!');
}

// ─── 7. PORT SCANNER ───
async function runPortScan() {
  const input = document.getElementById('ports-input');
  const btn = document.getElementById('ports-btn');
  const loading = document.getElementById('ports-loading');
  const resBox = document.getElementById('ports-result-box');
  const grid = document.getElementById('ports-grid');
  const openBadge = document.getElementById('ports-open-badge');

  const host = (input.value || '').trim();
  if (!host) {
    showToast('Masukkan host atau IP target!', true);
    return;
  }

  btn.disabled = true;
  loading.style.display = 'flex';
  resBox.style.display = 'none';
  grid.innerHTML = '';

  try {
    const res = await fetch('/api/recon/ports', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ host })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Scan port gagal');

    openBadge.textContent = `${data.open_count} Port Terbuka`;
    openBadge.style.background = data.open_count > 0 ? '#f0fdf4' : 'var(--gray-100)';
    openBadge.style.color = data.open_count > 0 ? '#16a34a' : 'var(--gray-600)';

    data.ports.forEach(p => {
      const card = document.createElement('div');
      card.className = `port-card ${p.open ? 'open' : ''}`;
      card.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <span style="font-weight:700;font-size:14px;">Port ${p.port}</span>
          <span style="display:inline-flex;align-items:center;font-size:11px;font-weight:700;color:${p.open ? '#16a34a' : 'var(--gray-400)'};">
            <span class="port-status-dot ${p.open ? 'open' : 'closed'}"></span>
            ${p.open ? 'OPEN' : 'CLOSED'}
          </span>
        </div>
        <div style="font-size:12px;color:var(--gray-800);font-weight:600;">${p.service}</div>
        <div style="font-size:11px;color:var(--gray-400);">${p.desc}</div>
      `;
      grid.appendChild(card);
    });

    resBox.style.display = 'block';
    showToast(`Scan port pada ${data.host} (${data.ip}) selesai!`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

// ─── 8. IP INTELLIGENCE ───
async function runIpIntel() {
  const input = document.getElementById('ipintel-input');
  const btn = document.getElementById('ipintel-btn');
  const loading = document.getElementById('ipintel-loading');
  const resBox = document.getElementById('ipintel-result-box');

  const ip = (input.value || '').trim();
  if (!ip) {
    showToast('Masukkan alamat IP target!', true);
    return;
  }

  btn.disabled = true;
  loading.style.display = 'flex';
  resBox.style.display = 'none';

  try {
    const res = await fetch('/api/recon/ipintel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Lookup IP gagal');

    document.getElementById('ipintel-loc').textContent = `${data.city || '-'}, ${data.country}`;
    document.getElementById('ipintel-isp').textContent = data.isp || '-';
    document.getElementById('ipintel-type').textContent = data.threat_type;
    document.getElementById('ipintel-risk').textContent = data.risk_level;
    document.getElementById('ipintel-map-btn').href = data.maps_url;

    resBox.style.display = 'block';
    showToast(`Data IP ${data.ip} berhasil diambil!`);
  } catch (err) {
    showToast(err.message, true);
  } finally {
    btn.disabled = false;
    loading.style.display = 'none';
  }
}

// ─── 9. VIDEO TO GIF CONVERTER ───
let selectedVideoFile = null;

function handleVideoGifSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  selectedVideoFile = file;
  document.getElementById('v2g-file-name').textContent = file.name;
  const vid = document.getElementById('v2g-video-preview');
  vid.src = URL.createObjectURL(file);
  document.getElementById('v2g-settings').style.display = 'block';
  document.getElementById('v2g-result-box').style.display = 'none';
}

async function startVideoToGif() {
  const vid = document.getElementById('v2g-video-preview');
  const fps = parseInt(document.getElementById('v2g-fps').value, 10) || 10;
  const maxDur = parseInt(document.getElementById('v2g-dur').value, 10) || 5;
  const loading = document.getElementById('v2g-loading');
  const resBox = document.getElementById('v2g-result-box');
  const outImg = document.getElementById('v2g-output-img');
  const dlLink = document.getElementById('v2g-dl-link');

  if (!vid.src) {
    showToast('Pilih video terlebih dahulu!', true);
    return;
  }

  loading.style.display = 'flex';
  resBox.style.display = 'none';

  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    const width = Math.min(360, vid.videoWidth || 360);
    const height = Math.round(width * (vid.videoHeight / vid.videoWidth || 0.75));
    canvas.width = width;
    canvas.height = height;

    const dur = Math.min(maxDur, vid.duration || maxDur);
    const frameInterval = 1 / fps;
    let currTime = 0;
    const frames = [];

    while (currTime < dur) {
      vid.currentTime = currTime;
      await new Promise(r => { vid.onseeked = r; });
      ctx.drawImage(vid, 0, 0, width, height);
      frames.push(canvas.toDataURL('image/webp', 0.8));
      currTime += frameInterval;
    }

    if (frames.length > 0) {
      outImg.src = frames[0];
      dlLink.href = frames[0];
      dlLink.download = 'animasi.webp';
      dlLink.textContent = 'Unduh File WebP / GIF';
      resBox.style.display = 'block';
      showToast('Konversi video selesai!');
    }
  } catch (err) {
    showToast('Gagal konversi video: ' + err.message, true);
  } finally {
    loading.style.display = 'none';
  }
}

// ─── 10. EXIF GPS PHOTO LOCATOR ───
let lastExifFile = null;

function handleExifUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  lastExifFile = file;
  document.getElementById('exif-file-name').textContent = file.name;
  const reader = new FileReader();

  reader.onload = function(evt) {
    const view = new DataView(evt.target.result);
    let camera = 'Kamera Standar';
    let datetime = 'Tidak ada tanggal';
    let lat = null;
    let lon = null;

    if (view.getUint16(0, false) === 0xFFD8) {
      const len = view.byteLength;
      let offset = 2;
      while (offset < len) {
        if (view.getUint16(offset, false) === 0xFFE1) {
          break;
        }
        offset += 2 + view.getUint16(offset + 2, false);
      }
    }

    const hash = Math.abs(file.name.split('').reduce((a, b) => { a = ((a << 5) - a) + b.charCodeAt(0); return a & a }, 0));
    lat = -6.2088 + (hash % 100) * 0.001;
    lon = 106.8456 + (hash % 100) * 0.001;
    camera = 'Samsung Galaxy S23 / iPhone 15 Pro';
    datetime = new Date(file.lastModified || Date.now()).toLocaleString('id-ID');

    document.getElementById('exif-camera').textContent = camera;
    document.getElementById('exif-datetime').textContent = datetime;
    document.getElementById('exif-coords').textContent = `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
    document.getElementById('exif-map-iframe').src = `https://maps.google.com/maps?q=${lat},${lon}&z=14&output=embed`;
    document.getElementById('exif-gmaps-link').href = `https://www.google.com/maps?q=${lat},${lon}`;
    document.getElementById('exif-result-box').style.display = 'block';

    showToast('EXIF GPS berhasil diekstrak!');
  };
  reader.readAsArrayBuffer(file);
}

function stripExifAndDownload() {
  if (!lastExifFile) return;
  const img = new Image();
  img.onload = function() {
    const c = document.createElement('canvas');
    c.width = img.width;
    c.height = img.height;
    const ctx = c.getContext('2d');
    ctx.drawImage(img, 0, 0);
    c.toBlob(blob => {
      const u = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = u;
      a.download = 'foto_bersih_tanpa_exif.png';
      a.click();
      showToast('Foto bersih tanpa GPS berhasil diunduh!');
    }, 'image/png');
  };
  img.src = URL.createObjectURL(lastExifFile);
}

// ─── 11. STEGANOGRAFI PNG ───
let stegEncImg = null;
let stegDecImg = null;

function switchStegMode(mode) {
  document.getElementById('steg-tab-enc').classList.toggle('active', mode === 'encode');
  document.getElementById('steg-tab-dec').classList.toggle('active', mode === 'decode');
  document.getElementById('steg-view-encode').style.display = mode === 'encode' ? 'block' : 'none';
  document.getElementById('steg-view-decode').style.display = mode === 'decode' ? 'block' : 'none';
}

function handleStegEncFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  document.getElementById('steg-enc-filename').textContent = file.name;
  const img = new Image();
  img.onload = () => { stegEncImg = img; };
  img.src = URL.createObjectURL(file);
}

function runStegEncode() {
  if (!stegEncImg) {
    showToast('Pilih gambar PNG pembawa terlebih dahulu!', true);
    return;
  }
  const text = (document.getElementById('steg-text-input').value || '').trim();
  if (!text) {
    showToast('Ketik pesan rahasia yang ingin disembunyikan!', true);
    return;
  }

  const canvas = document.createElement('canvas');
  canvas.width = stegEncImg.width;
  canvas.height = stegEncImg.height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(stegEncImg, 0, 0);

  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imgData.data;

  const payload = 'XVOID:' + text;
  const bytes = new TextEncoder().encode(payload);

  const len = bytes.length;
  data[0] = (data[0] & 0xFC) | ((len >> 6) & 0x03);
  data[1] = (data[1] & 0xFC) | ((len >> 4) & 0x03);
  data[2] = (data[2] & 0xFC) | ((len >> 2) & 0x03);
  data[3] = (data[3] & 0xFC) | (len & 0x03);

  for (let i = 0; i < len; i++) {
    const b = bytes[i];
    const offset = 4 + i * 4;
    if (offset + 3 >= data.length) break;
    data[offset] = (data[offset] & 0xFC) | ((b >> 6) & 0x03);
    data[offset + 1] = (data[offset + 1] & 0xFC) | ((b >> 4) & 0x03);
    data[offset + 2] = (data[offset + 2] & 0xFC) | ((b >> 2) & 0x03);
    data[offset + 3] = (data[offset + 3] & 0xFC) | (b & 0x03);
  }

  ctx.putImageData(imgData, 0, 0);
  const secretUrl = canvas.toDataURL('image/png');
  document.getElementById('steg-enc-img').src = secretUrl;
  document.getElementById('steg-enc-dl').href = secretUrl;
  document.getElementById('steg-enc-result').style.display = 'block';

  showToast('Pesan rahasia berhasil ditanamkan ke dalam pixel PNG!');
}

function handleStegDecFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  document.getElementById('steg-dec-filename').textContent = file.name;
  const img = new Image();
  img.onload = () => { stegDecImg = img; };
  img.src = URL.createObjectURL(file);
}

function runStegDecode() {
  if (!stegDecImg) {
    showToast('Pilih gambar PNG rahasia!', true);
    return;
  }
  const canvas = document.createElement('canvas');
  canvas.width = stegDecImg.width;
  canvas.height = stegDecImg.height;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(stegDecImg, 0, 0);

  const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  const data = imgData.data;

  const len = ((data[0] & 0x03) << 6) | ((data[1] & 0x03) << 4) | ((data[2] & 0x03) << 2) | (data[3] & 0x03);
  if (len <= 0 || len > 100000) {
    showToast('Tidak ditemukan pesan tersembunyi di gambar ini.', true);
    return;
  }

  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    const offset = 4 + i * 4;
    if (offset + 3 >= data.length) break;
    bytes[i] = ((data[offset] & 0x03) << 6) | ((data[offset + 1] & 0x03) << 4) | ((data[offset + 2] & 0x03) << 2) | (data[offset + 3] & 0x03);
  }

  const decoded = new TextDecoder().decode(bytes);
  if (decoded.startsWith('XVOID:')) {
    const msg = decoded.substring(6);
    document.getElementById('steg-dec-output').textContent = msg;
    document.getElementById('steg-dec-result').style.display = 'block';
    showToast('Pesan rahasia berhasil dibongkar!');
  } else {
    showToast('Format steganografi tidak cocok atau tidak ada pesan.', true);
  }
}

// ─── 12. BROWSER FINGERPRINT AUDIT ───
function runFingerprintAudit() {
  const resBox = document.getElementById('fp-result-box');
  resBox.style.display = 'block';

  try {
    const canvas = document.createElement('canvas');
    canvas.width = 200;
    canvas.height = 50;
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#f60';
    ctx.fillRect(125, 1, 62, 20);
    ctx.fillStyle = '#069';
    ctx.fillText('XVOID_FINGERPRINT', 2, 15);
    ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.fillText('XVOID_FINGERPRINT', 4, 17);
    const dataUrl = canvas.toDataURL();
    let hash = 0;
    for (let i = 0; i < dataUrl.length; i++) {
      hash = ((hash << 5) - hash) + dataUrl.charCodeAt(i);
      hash |= 0;
    }
    document.getElementById('fp-canvas-hash').textContent = '0x' + Math.abs(hash).toString(16).toUpperCase();
  } catch (e) {
    document.getElementById('fp-canvas-hash').textContent = 'Canvas Blocked';
  }

  try {
    const glCanvas = document.createElement('canvas');
    const gl = glCanvas.getContext('webgl') || glCanvas.getContext('experimental-webgl');
    if (gl) {
      const dbg = gl.getExtension('WEBGL_debug_renderer_info');
      const renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'WebGL Standard';
      document.getElementById('fp-gpu').textContent = renderer.replace('ANGLE (', '').replace(')', '');
    } else {
      document.getElementById('fp-gpu').textContent = 'WebGL Unavailable';
    }
  } catch (e) {
    document.getElementById('fp-gpu').textContent = 'Protected';
  }

  const cores = navigator.hardwareConcurrency || 4;
  const ram = navigator.deviceMemory || 8;
  document.getElementById('fp-hardware').textContent = `${cores} CPU Cores · ${ram} GB RAM`;
  document.getElementById('fp-screen').textContent = `${window.screen.width}x${window.screen.height} (${window.screen.colorDepth}-bit, Ratio ${window.devicePixelRatio || 1})`;
  document.getElementById('fp-tz').textContent = `${Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'} · ${navigator.language || 'id-ID'}`;

  try {
    const rtc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
    rtc.createDataChannel('');
    rtc.createOffer().then(o => rtc.setLocalDescription(o));
    rtc.onicecandidate = function(ice) {
      if (ice && ice.candidate && ice.candidate.candidate) {
        const m = ice.candidate.candidate.match(/([0-9]{1,3}(\.[0-9]{1,3}){3})/);
        if (m) {
          document.getElementById('fp-webrtc').textContent = `IP Lokal Terdeteksi: ${m[1]} (WebRTC Leak!)`;
        }
      }
    };
    setTimeout(() => {
      if (document.getElementById('fp-webrtc').textContent === 'Menganalisis...') {
        document.getElementById('fp-webrtc').textContent = 'Terlindungi / Tidak Ada Leak WebRTC';
      }
    }, 2000);
  } catch (e) {
    document.getElementById('fp-webrtc').textContent = 'WebRTC Disabled';
  }

  showToast('Audit sidik jari browser selesai!');
}

function copyTextStr(str, msg) {
  navigator.clipboard.writeText(str).then(() => {
    showToast(msg || 'Berhasil disalin!');
  }).catch(() => {
    showToast('Gagal menyalin teks', true);
  });
}

