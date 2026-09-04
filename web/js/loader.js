/* ═══════════════════════════════════════════════════════════
   PROJECT-XVOID — loader.js
   Dynamic Fluctuating Progress · Random Direction Entrance · Curved Typewriter
   ═══════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  const loader = document.getElementById('xvoidLoader');
  if (!loader) return;

  const loaderBox = document.getElementById('xvLoaderBox');
  const introBox = document.getElementById('xvIntroBox');
  const introPill = document.getElementById('xvIntroPill');
  const introSub = document.getElementById('xvIntroSub');
  const typewriterText = document.getElementById('xvTypewriterText');
  const cursor = document.getElementById('xvCursor');

  const bar = document.getElementById('xvProgressBar');
  const pct = document.getElementById('xvProgressPct');
  const status = document.getElementById('xvStatus');

  let isCompleted = false;
  let currentPct = 0;

  /* ─────────────────────────────────────────────────────────────
     1. DYNAMIC PROGRESS RHYTHM (Fluctuating Speed as Requested)
     - Patah pertama agak lama (~1100ms pause)
     - Kedua pelan-pelan (~1250ms slow crawl)
     - Terus cepat (~220ms sudden rapid burst)
     - Terus pelan (~1100ms slow crawl)
     - Final snap to 100%
  ───────────────────────────────────────────────────────────── */

  const PHASES = [
    // Phase 1: Quick jump to 16%, then "patah pertama agak lama" (1100ms hold)
    { type: 'jump', targetPct: 16, durationMs: 260, holdMs: 1100, text: 'CORE.KERNEL.INIT' },

    // Phase 2: "Kedua pelan-pelan" (Slow incremental crawl from 16% to 38%)
    { type: 'crawl', targetPct: 38, durationMs: 1250, holdMs: 250, text: 'RUNTIME.SUBSYSTEMS' },

    // Phase 3: "Terus cepat" (Sudden rapid burst from 38% to 76%)
    { type: 'jump', targetPct: 76, durationMs: 220, holdMs: 450, text: 'LIQUID.SHADERS.COMPILE' },

    // Phase 4: "Terus pelan" (Slow creeping progression from 76% to 91%)
    { type: 'crawl', targetPct: 91, durationMs: 1150, holdMs: 550, text: 'TELEMETRY.SYNC.READY' },

    // Phase 5: Final burst to 100% and brief completion hold
    { type: 'jump', targetPct: 100, durationMs: 240, holdMs: 450, text: 'SYSTEM.READY' }
  ];

  // Micro crossfade for terminal status text
  function updateStatus(newText) {
    if (!status || !newText || status.textContent === newText) return;
    status.classList.add('xv-swap');
    setTimeout(() => {
      status.textContent = newText;
      status.classList.remove('xv-swap');
    }, 120);
  }

  // Smooth continuous number and bar animation (used for crawls and jumps)
  function animateProgress(fromVal, toVal, durationMs, isCrawl, onDone) {
    const start = performance.now();

    function step(now) {
      if (isCompleted) return;
      const elapsed = now - start;
      const t = Math.min(1, elapsed / durationMs);

      // Curve: linear/smooth for slow crawl, snappy ease-out for fast jump
      const eased = isCrawl
        ? t
        : 1 - Math.pow(1 - t, 3);

      const val = Math.min(100, Math.round(fromVal + (toVal - fromVal) * eased));

      if (bar) bar.style.width = val + '%';
      if (pct) pct.textContent = val + '%';
      currentPct = val;

      if (t < 1) {
        requestAnimationFrame(step);
      } else {
        if (bar) bar.style.width = toVal + '%';
        if (pct) pct.textContent = toVal + '%';
        currentPct = toVal;
        if (onDone) onDone();
      }
    }

    requestAnimationFrame(step);
  }

  // Execute each phase in sequence
  function runPhase(index) {
    if (isCompleted || index >= PHASES.length) {
      triggerIntroTransition();
      return;
    }

    const p = PHASES[index];
    updateStatus(p.text);

    const isCrawl = p.type === 'crawl';
    animateProgress(currentPct, p.targetPct, p.durationMs, isCrawl, () => {
      // Pause at checkpoint
      setTimeout(() => {
        if (isCompleted) return;
        if (index + 1 < PHASES.length) {
          runPhase(index + 1);
        } else {
          triggerIntroTransition();
        }
      }, p.holdMs);
    });
  }

  /* ─────────────────────────────────────────────────────────────
     2. RANDOM DIRECTION ENTRANCE WITH SMOOTH CURVE
     Picks a randomized 3D vector for the intro box & child elements
  ───────────────────────────────────────────────────────────── */

  function applyRandomEntranceVectors() {
    if (!introBox) return;

    // 6 Distinct organic trajectory angles
    const trajectories = [
      { x: -50, y: -35, rot: -3.0, pillX: 30, pillY: -20, subX: -30, subY: 25 },
      { x: 50, y: -35, rot: 3.0, pillX: -30, pillY: -20, subX: 30, subY: 25 },
      { x: -45, y: 40, rot: 2.5, pillX: -25, pillY: 20, subX: 30, subY: -20 },
      { x: 45, y: 40, rot: -2.5, pillX: 25, pillY: 20, subX: -30, subY: -20 },
      { x: 0, y: 55, rot: 1.5, pillX: -20, pillY: -20, subX: 20, subY: 25 },
      { x: -55, y: 0, rot: -2.0, pillX: 25, pillY: -20, subX: -25, subY: 20 }
    ];

    const pick = trajectories[Math.floor(Math.random() * trajectories.length)];

    // On mobile devices (<=480px), scale down offset so it never overflows screen edge
    const isMobile = window.innerWidth <= 480;
    const scale = isMobile ? 0.35 : 1.0;
    const rotScale = isMobile ? 0.4 : 1.0;

    introBox.style.setProperty('--rand-x', (pick.x * scale).toFixed(1) + 'px');
    introBox.style.setProperty('--rand-y', (pick.y * scale).toFixed(1) + 'px');
    introBox.style.setProperty('--rand-rot', (pick.rot * rotScale).toFixed(1) + 'deg');

    if (introPill) {
      introPill.style.setProperty('--pill-x', (pick.pillX * scale).toFixed(1) + 'px');
      introPill.style.setProperty('--pill-y', (pick.pillY * scale).toFixed(1) + 'px');
    }
    if (introSub) {
      introSub.style.setProperty('--sub-x', (pick.subX * scale).toFixed(1) + 'px');
      introSub.style.setProperty('--sub-y', (pick.subY * scale).toFixed(1) + 'px');
    }
  }

  /* ─────────────────────────────────────────────────────────────
     3. CURVED TYPEWRITER ANIMATION
     Types characters with dynamic keystroke curve and popping spans
  ───────────────────────────────────────────────────────────── */

  function runCurvedTypewriter(onComplete) {
    if (!typewriterText) {
      if (onComplete) onComplete();
      return;
    }

    typewriterText.innerHTML = '';

    const prefixSpan = document.createElement('span');
    const brandSpan = document.createElement('span');
    brandSpan.className = 'xv-intro-brand';

    typewriterText.appendChild(prefixSpan);
    typewriterText.appendChild(brandSpan);

    const fullText = 'Welcome to Project XVoid';
    const brandStartIndex = 'Welcome to '.length; // 11
    let charIndex = 0;

    function typeNext() {
      if (isCompleted) return;

      if (charIndex >= fullText.length) {
        if (onComplete) onComplete();
        return;
      }

      const ch = fullText[charIndex];
      const span = document.createElement('span');
      span.className = 'xv-char';
      span.textContent = ch;

      if (charIndex < brandStartIndex) {
        prefixSpan.appendChild(span);
      } else {
        brandSpan.appendChild(span);
      }

      charIndex++;

      // Curved keystroke delay: gentle curve with realistic micro-rhythm
      const progressRatio = charIndex / fullText.length;
      const baseDelay = ch === ' ' ? 80 : (38 + Math.sin(progressRatio * Math.PI) * 20);
      const delay = baseDelay + (Math.random() * 14 - 7);

      setTimeout(typeNext, Math.max(22, delay));
    }

    // Start typing after intro card starts settling
    setTimeout(typeNext, 220);
  }

  /* ─────────────────────────────────────────────────────────────
     4. INTRO OVERLAY TRANSITION ORCHESTRATION
  ───────────────────────────────────────────────────────────── */

  function triggerIntroTransition() {
    if (isCompleted) return;

    if (bar) bar.style.width = '100%';
    if (pct) pct.textContent = '100%';

    // Smoothly fade out progress box
    if (loaderBox) {
      loaderBox.classList.add('xv-box-hide');
    }

    // Set random entrance vectors before revealing intro
    applyRandomEntranceVectors();

    // Smoothly reveal Intro Box from random vector
    setTimeout(() => {
      if (isCompleted) return;
      if (introBox) {
        introBox.classList.add('xv-intro-active');
      }

      // Run curved typewriter animation
      runCurvedTypewriter(() => {
        // Hold for ~1600ms after typing finishes so user can comfortably read it
        setTimeout(() => {
          finishSequence();
        }, 1600);
      });
    }, 240);
  }

  // Smooth final fade-out of the intro overlay into the main dashboard
  function finishSequence() {
    if (isCompleted) return;
    isCompleted = true;

    // Fade out intro box and the full screen loader overlay
    if (introBox) {
      introBox.classList.add('xv-intro-fadeout');
    }
    loader.classList.add('xv-done');

    // Notify dashboard components
    window.dispatchEvent(new CustomEvent('xvoidLoaderDone'));

    // Remove from DOM after transition completes
    setTimeout(() => {
      if (loader && loader.parentNode) {
        loader.parentNode.removeChild(loader);
      }
    }, 900);
  }

  // Safety fallback after 10.5s to guarantee entry even if backgrounded
  const safetyTimeout = setTimeout(() => {
    if (!isCompleted) finishSequence();
  }, 10500);

  // Kick off phase 0
  runPhase(0);

  // Expose global controller
  window.XVoidLoader = {
    finish: () => {
      clearTimeout(safetyTimeout);
      finishSequence();
    },
    isDone: () => isCompleted
  };
})();
