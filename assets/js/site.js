/* Swatantra Dhara: site interactions.
   Vanilla JS, no dependencies. Each feature only runs when its markup is on
   the page, and every animation respects prefers-reduced-motion. */
(() => {
  "use strict";

  const doc = document;
  const root = doc.documentElement;
  const $ = (s, c = doc) => c.querySelector(s);
  const $$ = (s, c = doc) => Array.from(c.querySelectorAll(s));
  const reduceMQ = matchMedia("(prefers-reduced-motion: reduce)");
  const reduced = () => reduceMQ.matches;
  const finePointer = matchMedia("(hover: hover) and (pointer: fine)").matches;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const EASE = "cubic-bezier(.16,1,.3,1)";
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* storage unavailable */ } },
  };
  const onScroll = (fn) => {
    let ticking = false;
    const run = () => { ticking = false; fn(); };
    addEventListener("scroll", () => { if (!ticking) { ticking = true; requestAnimationFrame(run); } }, { passive: true });
    addEventListener("resize", run, { passive: true });
    doc.addEventListener("layoutchange", run);
    run();
  };

  window.__siteReady = true;
  root.classList.remove("no-js");

  /* Theme: light/dark with a circular reveal, remembered, follows the system */
  function initTheme() {
    const btn = $("[data-theme-toggle]");
    const sys = matchMedia("(prefers-color-scheme: dark)");
    const meta = $('meta[name="theme-color"]');
    const current = () => (root.dataset.theme === "dark" ? "dark" : "light");
    const sync = () => {
      if (btn) btn.setAttribute("aria-label", `Switch to ${current() === "dark" ? "light" : "dark"} theme`);
      if (meta) meta.setAttribute("content", getComputedStyle(root).getPropertyValue("--paper").trim());
    };
    const apply = (t) => { root.dataset.theme = t; sync(); };
    sync();
    sys.addEventListener("change", (e) => { if (!store.get("theme")) apply(e.matches ? "dark" : "light"); });
    if (!btn) return;
    btn.addEventListener("click", () => {
      const next = current() === "dark" ? "light" : "dark";
      store.set("theme", next);
      if (!doc.startViewTransition || reduced()) { apply(next); return; }
      const r = btn.getBoundingClientRect();
      const x = r.left + r.width / 2;
      const y = r.top + r.height / 2;
      root.style.setProperty("--vt-x", `${x}px`);
      root.style.setProperty("--vt-y", `${y}px`);
      root.style.setProperty("--vt-r", `${Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))}px`);
      root.classList.add("vt-theme");
      const t = doc.startViewTransition(() => apply(next));
      t.finished.finally(() => root.classList.remove("vt-theme"));
    });
  }

  /* Header state, scroll-progress fallback, hero parallax */
  function initScroll() {
    const bar = $(".scroll-progress");
    const cssProgress = window.CSS && CSS.supports("animation-timeline: scroll()");
    const media = $("[data-parallax]");
    const cover = $(".hero-cover");
    onScroll(() => {
      const y = scrollY;
      root.classList.toggle("is-scrolled", y > 8);
      if (bar && !cssProgress) {
        const max = root.scrollHeight - innerHeight;
        bar.style.setProperty("--progress", max > 0 ? (y / max).toFixed(4) : "0");
      }
      if (media && cover && !reduced()) {
        const h = cover.offsetHeight;
        if (y < h * 1.2) media.style.setProperty("--parallax", `${Math.min(y * 0.2, h * 0.13).toFixed(1)}px`);
      }
    });
    const avatar = $(".hero-avatar");
    if (avatar && "IntersectionObserver" in window) {
      new IntersectionObserver(([e]) => root.classList.toggle("hero-passed", !e.isIntersecting),
        { rootMargin: "-64px 0px 0px 0px" }).observe(avatar);
    }
  }

  /* Mobile menu */
  function initMenu() {
    const btn = $("[data-menu-toggle]");
    const panel = $("#mobile-menu");
    if (!btn || !panel) return;
    $$("li", panel).forEach((li, i) => li.style.setProperty("--i", i));
    let open = false;
    const set = (v) => {
      open = v;
      btn.setAttribute("aria-expanded", String(v));
      btn.setAttribute("aria-label", v ? "Close menu" : "Open menu");
      root.classList.toggle("nav-open", v);
      if (v) {
        panel.hidden = false;
        requestAnimationFrame(() => requestAnimationFrame(() => panel.classList.add("is-open")));
      } else {
        panel.classList.remove("is-open");
        setTimeout(() => { if (!open) panel.hidden = true; }, reduced() ? 0 : 320);
      }
    };
    btn.addEventListener("click", () => set(!open));
    panel.addEventListener("click", (e) => { if (e.target.closest("a")) set(false); });
    doc.addEventListener("keydown", (e) => { if (e.key === "Escape" && open) { set(false); btn.focus(); } });
    matchMedia("(min-width: 1320px)").addEventListener("change", (e) => { if (e.matches && open) set(false); });
  }

  /* Scroll reveal with staggered children */
  function initReveal() {
    $$("[data-stagger]").forEach((c) => Array.from(c.children).forEach((el, i) => el.style.setProperty("--i", Math.min(i, 8))));
    const els = $$("[data-reveal], [data-stagger]");
    const show = (el) => {
      el.classList.add("is-in");
      if (el.hasAttribute("data-stagger")) setTimeout(() => el.classList.add("is-done"), 1500);
    };
    if (!("IntersectionObserver" in window)) { els.forEach(show); return; }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { show(e.target); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.06 });
    els.forEach((el) => io.observe(el));
  }

  /* Timelines: the line draws itself as you scroll; nodes light up as it passes */
  function initTimelines() {
    const lines = $$("[data-timeline]");
    if (!lines.length) return;
    onScroll(() => {
      const vh = innerHeight;
      lines.forEach((tl) => {
        const r = tl.getBoundingClientRect();
        if (!r.height) return;
        const p = reduced() ? 1 : clamp((vh * 0.72 - r.top) / r.height, 0, 1);
        tl.style.setProperty("--draw", p.toFixed(4));
        const reach = r.top + p * r.height;
        $$(":scope > .tl-item", tl).forEach((item) => {
          const node = $(".tl-node", item);
          if (!node) return;
          const nr = node.getBoundingClientRect();
          item.classList.toggle("is-reached", nr.height > 0 && nr.top + nr.height / 2 <= reach + 4);
        });
      });
    });
  }

  /* 3D tilt and cursor glow on cards (fine pointers only) */
  function initTilt() {
    if (!finePointer) return;
    $$(".tilt").forEach((el) => {
      let raf = 0;
      el.addEventListener("pointermove", (e) => {
        if (reduced()) return;
        const r = el.getBoundingClientRect();
        const px = (e.clientX - r.left) / r.width;
        const py = (e.clientY - r.top) / r.height;
        cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          el.style.transitionDuration = ".12s";
          el.style.setProperty("--ry", `${((px - 0.5) * 7).toFixed(2)}deg`);
          el.style.setProperty("--rx", `${((0.5 - py) * 7).toFixed(2)}deg`);
          el.style.setProperty("--gx", `${(px * 100).toFixed(1)}%`);
          el.style.setProperty("--gy", `${(py * 100).toFixed(1)}%`);
        });
      });
      el.addEventListener("pointerleave", () => {
        cancelAnimationFrame(raf);
        el.style.transitionDuration = "";
        el.style.setProperty("--rx", "0deg");
        el.style.setProperty("--ry", "0deg");
      });
    });
  }

  /* Magnetic hover on primary buttons */
  function initMagnetic() {
    if (!finePointer) return;
    $$(".btn-magnetic").forEach((b) => {
      b.addEventListener("pointermove", (e) => {
        if (reduced()) return;
        const r = b.getBoundingClientRect();
        b.style.setProperty("--mx", `${((e.clientX - r.left - r.width / 2) * 0.22).toFixed(1)}px`);
        b.style.setProperty("--my", `${((e.clientY - r.top - r.height / 2) * 0.32).toFixed(1)}px`);
      });
      b.addEventListener("pointerleave", () => { b.style.setProperty("--mx", "0px"); b.style.setProperty("--my", "0px"); });
    });
  }

  /* Count-up numbers */
  function initCountUp() {
    const els = $$("[data-count]");
    if (!els.length || reduced() || !("IntersectionObserver" in window)) return;
    const run = (el) => {
      const target = Number(el.dataset.count);
      const suffix = el.dataset.suffix || "";
      const t0 = performance.now();
      const tick = (now) => {
        const p = Math.min(1, (now - t0) / 1400);
        el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3))) + suffix;
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
    };
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { io.unobserve(e.target); run(e.target); } });
    }, { threshold: 0.6 });
    els.forEach((el) => { el.textContent = `0${el.dataset.suffix || ""}`; io.observe(el); });
  }

  /* Typed identity line in the hero */
  function initTyped() {
    const el = $("[data-typed]");
    if (!el || reduced()) return;
    let words;
    try { words = JSON.parse(el.dataset.typed); } catch (e) { return; }
    if (!Array.isArray(words) || words.length < 2) return;
    let wi = 0;
    let ci = words[0].length;
    let deleting = true;
    let visible = true;
    const step = () => {
      if (!visible || doc.hidden) { setTimeout(step, 500); return; }
      if (deleting) {
        ci -= 1;
        el.textContent = words[wi].slice(0, ci);
        if (ci <= 0) { deleting = false; wi = (wi + 1) % words.length; setTimeout(step, 350); return; }
        setTimeout(step, 26);
      } else {
        ci += 1;
        el.textContent = words[wi].slice(0, ci);
        if (ci >= words[wi].length) { deleting = true; setTimeout(step, 2600); return; }
        setTimeout(step, 50 + Math.random() * 45);
      }
    };
    setTimeout(step, 3000);
    if ("IntersectionObserver" in window) new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(el);
  }

  /* Hero network: faint nodes and edges that lean towards the cursor */
  function initHeroNet() {
    const canvas = $(".hero-net");
    if (!canvas || !canvas.getContext) return;
    const host = canvas.closest(".hero-cover");
    const ctx = canvas.getContext("2d");
    const ACCENT = "242,154,98";
    const RADIUS = 170;
    const mouse = { x: 0, y: 0, on: false };
    let w = 0;
    let h = 0;
    let nodes = [];
    let raf = 0;
    let running = false;
    let inView = true;

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = r.width;
      h = r.height;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const n = Math.round(clamp((w * h) / 14000, 26, 95));
      nodes = Array.from({ length: n }, () => {
        const a = Math.random() * Math.PI * 2;
        const s = 0.08 + Math.random() * 0.18;
        return { x: Math.random() * w, y: Math.random() * h, vx: Math.cos(a) * s, vy: Math.sin(a) * s,
          bx: Math.cos(a) * s, by: Math.sin(a) * s, r: 0.7 + Math.random() * 1.3, hub: Math.random() < 0.1 };
      });
      draw();
    };
    const near = (x, y) => (mouse.on ? Math.max(0, 1 - Math.hypot(x - mouse.x, y - mouse.y) / RADIUS) : 0);
    const draw = () => {
      ctx.clearRect(0, 0, w, h);
      const link = clamp(w / 9, 90, 150);
      const link2 = link * link;
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const d2 = dx * dx + dy * dy;
          if (d2 > link2) continue;
          const t = 1 - Math.sqrt(d2) / link;
          const m = near((a.x + b.x) / 2, (a.y + b.y) / 2);
          ctx.strokeStyle = m > 0.05 ? `rgba(${ACCENT},${(t * (0.16 + 0.55 * m)).toFixed(3)})` : `rgba(255,255,255,${(t * 0.16).toFixed(3)})`;
          ctx.lineWidth = m > 0.05 ? 1 : 0.8;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
      for (const n of nodes) {
        const m = near(n.x, n.y);
        ctx.fillStyle = n.hub || m > 0.3 ? `rgba(${ACCENT},${(0.55 + m * 0.4).toFixed(3)})` : `rgba(255,255,255,${(0.36 + m * 0.4).toFixed(3)})`;
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r + (n.hub ? 1 : 0) + m * 1.2, 0, Math.PI * 2);
        ctx.fill();
      }
    };
    const step = () => {
      for (const n of nodes) {
        if (mouse.on) {
          const dx = mouse.x - n.x;
          const dy = mouse.y - n.y;
          const d = Math.hypot(dx, dy);
          if (d < RADIUS && d > 1) {
            const f = (1 - d / RADIUS) * 0.012;
            n.vx += (dx / d) * f;
            n.vy += (dy / d) * f;
          }
        }
        n.vx += (n.bx - n.vx) * 0.015;
        n.vy += (n.by - n.vy) * 0.015;
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < -20) n.x = w + 20; else if (n.x > w + 20) n.x = -20;
        if (n.y < -20) n.y = h + 20; else if (n.y > h + 20) n.y = -20;
      }
      draw();
      raf = requestAnimationFrame(step);
    };
    const sync = () => {
      const should = inView && !doc.hidden && !reduced();
      if (should && !running) { running = true; raf = requestAnimationFrame(step); }
      if (!should && running) { running = false; cancelAnimationFrame(raf); }
    };
    if ("IntersectionObserver" in window) new IntersectionObserver(([e]) => { inView = e.isIntersecting; sync(); }).observe(canvas);
    doc.addEventListener("visibilitychange", sync);
    reduceMQ.addEventListener("change", () => { sync(); draw(); });
    host.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      mouse.x = e.clientX - r.left;
      mouse.y = e.clientY - r.top;
      mouse.on = true;
    });
    host.addEventListener("pointerleave", () => { mouse.on = false; });
    let rt = 0;
    let lastW = 0;
    if ("ResizeObserver" in window) {
      new ResizeObserver(() => {
        const cw = canvas.getBoundingClientRect().width;
        if (Math.abs(cw - lastW) < 1) return;
        lastW = cw;
        clearTimeout(rt);
        rt = setTimeout(resize, 120);
      }).observe(canvas);
    }
    resize();
    lastW = w;
    sync();
  }

  /* FLIP helper: animate items from their old to their new positions */
  function flip(container, mutate) {
    const items = Array.from(container.children);
    const first = new Map(items.map((el) => [el, el.getBoundingClientRect()]));
    mutate();
    doc.dispatchEvent(new Event("layoutchange"));
    if (reduced() || !Element.prototype.animate) return;
    items.forEach((el) => {
      if (el.classList.contains("is-filtered-out")) return;
      const a = first.get(el);
      const b = el.getBoundingClientRect();
      if (!a.width && !a.height) {
        el.animate([{ opacity: 0, transform: "scale(.94)" }, { opacity: 1, transform: "none" }], { duration: 450, easing: EASE });
        return;
      }
      const dx = a.left - b.left;
      const dy = a.top - b.top;
      if (Math.abs(dx) > 0.5 || Math.abs(dy) > 0.5) {
        el.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "none" }], { duration: 560, easing: EASE });
      }
    });
  }

  /* Category filters (research, photography, experience) */
  function initFilters() {
    $$("[data-filter-group]").forEach((group) => {
      const name = group.dataset.filterGroup;
      const container = $(`[data-filter-items="${name}"]`);
      const status = $(`[data-filter-status="${name}"]`);
      if (!container) return;
      const buttons = $$("[data-filter]", group);
      buttons.forEach((btn) => btn.addEventListener("click", () => {
        const f = btn.dataset.filter;
        buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
        let shown = 0;
        flip(container, () => {
          Array.from(container.children).forEach((el) => {
            const ok = f === "all" || (el.dataset.tags || "").split(" ").includes(f);
            el.classList.toggle("is-filtered-out", !ok);
            if (ok) shown += 1;
          });
          container.dispatchEvent(new CustomEvent("filtered"));
        });
        if (status) status.textContent = `Showing ${shown} ${shown === 1 ? "item" : "items"}`;
      }));
    });
  }

  /* Blog: tag filter + search */
  function initBlog() {
    const grid = $("[data-posts]");
    if (!grid) return;
    const input = $("[data-post-search]");
    const buttons = $$("[data-tag]");
    const empty = $("[data-posts-empty]");
    const status = $("[data-posts-status]");
    let tag = "all";
    let query = "";
    const apply = () => {
      let n = 0;
      flip(grid, () => {
        Array.from(grid.children).forEach((el) => {
          const tags = (el.dataset.tags || "").split("|");
          const ok = (tag === "all" || tags.includes(tag)) && (!query || (el.dataset.search || "").includes(query));
          el.classList.toggle("is-filtered-out", !ok);
          if (ok) n += 1;
        });
      });
      if (empty) empty.hidden = n > 0;
      if (status) status.textContent = `${n} ${n === 1 ? "post" : "posts"} shown`;
    };
    const select = (t) => {
      const btn = buttons.find((b) => b.dataset.tag === t) || buttons[0];
      tag = btn ? btn.dataset.tag : "all";
      buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    };
    buttons.forEach((b) => b.addEventListener("click", () => { select(b.dataset.tag); apply(); }));
    let t = 0;
    if (input) input.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => { query = input.value.trim().toLowerCase(); apply(); }, 120);
    });
    const fromUrl = new URLSearchParams(location.search).get("tag");
    if (fromUrl) { select(fromUrl); apply(); }
  }

  /* Research project modal */
  function initModal() {
    const dialog = $("#project-modal");
    if (!dialog || typeof dialog.showModal !== "function") return;
    const content = $("[data-modal-content]", dialog);
    const panel = $(".modal-panel", dialog);
    let trigger = null;
    let closing = false;
    const open = (tpl, from) => {
      content.replaceChildren(tpl.content.cloneNode(true));
      trigger = from;
      dialog.showModal();
      panel.scrollTop = 0;
      requestAnimationFrame(() => dialog.classList.add("is-open"));
    };
    const close = () => {
      if (closing || !dialog.open) return;
      closing = true;
      dialog.classList.remove("is-open");
      setTimeout(() => {
        dialog.close();
        closing = false;
        if (trigger) trigger.focus({ preventScroll: true });
      }, reduced() ? 0 : 300);
    };
    $$("[data-modal]").forEach((a) => a.addEventListener("click", (e) => {
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const tpl = doc.getElementById(a.dataset.modal);
      if (!tpl) return;
      e.preventDefault();
      open(tpl, a);
    }));
    dialog.addEventListener("cancel", (e) => { e.preventDefault(); close(); });
    dialog.addEventListener("click", (e) => { if (e.target === dialog || e.target.closest("[data-modal-close]")) close(); });
  }

  /* Gallery: masonry layout */
  function initMasonry() {
    const g = $("[data-gallery]");
    if (!g) return;
    const ROW = 8;
    const GAP = 16;
    let lastW = 0;
    const layout = () => {
      g.classList.add("is-masonry");
      $$(".gallery-item", g).forEach((it) => {
        if (it.classList.contains("is-filtered-out")) return;
        const w = it.getBoundingClientRect().width;
        const ar = parseFloat(it.dataset.ar) || 1;
        it.style.gridRowEnd = `span ${Math.ceil((w / ar + GAP) / ROW)}`;
      });
    };
    layout();
    g.addEventListener("filtered", layout);
    if ("ResizeObserver" in window) {
      new ResizeObserver(() => {
        const w = g.getBoundingClientRect().width;
        if (Math.abs(w - lastW) > 0.5) { lastW = w; layout(); }
      }).observe(g);
    }
  }

  /* Gallery: lightbox with keyboard and swipe */
  function initLightbox() {
    const gallery = $("[data-gallery]");
    const lb = $("#lightbox");
    if (!gallery || !lb || typeof lb.showModal !== "function") return;
    const img = $(".lb-figure img", lb);
    const title = $(".lb-caption .ttl", lb);
    const cap = $(".lb-caption .cap", lb);
    const draft = $(".lb-caption .draft", lb);
    const counter = $(".lb-counter", lb);
    const prev = $(".lb-prev", lb);
    const next = $(".lb-next", lb);
    let links = [];
    let idx = 0;
    let trigger = null;
    let closing = false;

    const show = (i) => {
      links = $$(".gallery-item:not(.is-filtered-out) .gallery-link", gallery);
      if (!links.length) return;
      idx = (i + links.length) % links.length;
      const a = links[idx];
      img.classList.remove("is-loaded");
      img.onload = () => img.classList.add("is-loaded");
      img.width = Number(a.dataset.w);
      img.height = Number(a.dataset.h);
      img.alt = a.dataset.alt || "";
      img.src = a.href;
      if (img.complete && img.naturalWidth) img.classList.add("is-loaded");
      title.textContent = a.dataset.title || "";
      cap.textContent = a.dataset.caption || "";
      draft.hidden = a.dataset.draft !== "true";
      counter.textContent = `${idx + 1} / ${links.length}`;
      prev.hidden = next.hidden = links.length < 2;
      [idx + 1, idx - 1].forEach((j) => { const n = links[(j + links.length) % links.length]; if (n) new Image().src = n.href; });
    };
    const close = () => {
      if (closing || !lb.open) return;
      closing = true;
      lb.classList.remove("is-open");
      setTimeout(() => { lb.close(); closing = false; if (trigger) trigger.focus({ preventScroll: true }); }, reduced() ? 0 : 300);
    };
    gallery.addEventListener("click", (e) => {
      const a = e.target.closest(".gallery-link");
      if (!a || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      trigger = a;
      const visible = $$(".gallery-item:not(.is-filtered-out) .gallery-link", gallery);
      lb.showModal();
      show(visible.indexOf(a));
      requestAnimationFrame(() => lb.classList.add("is-open"));
    });
    prev.addEventListener("click", () => show(idx - 1));
    next.addEventListener("click", () => show(idx + 1));
    $("[data-lb-close]", lb).addEventListener("click", close);
    lb.addEventListener("cancel", (e) => { e.preventDefault(); close(); });
    lb.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft") { e.preventDefault(); show(idx - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); show(idx + 1); }
    });
    lb.addEventListener("click", (e) => { if (e.target === lb || e.target.classList.contains("lb-figure")) close(); });
    let sx = 0;
    let sy = 0;
    let tracking = false;
    const stage = $(".lb-stage", lb);
    stage.addEventListener("pointerdown", (e) => { if (e.pointerType === "mouse") return; tracking = true; sx = e.clientX; sy = e.clientY; });
    stage.addEventListener("pointerup", (e) => {
      if (!tracking) return;
      tracking = false;
      const dx = e.clientX - sx;
      const dy = e.clientY - sy;
      if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.2) show(idx + (dx < 0 ? 1 : -1));
    });
    stage.addEventListener("pointercancel", () => { tracking = false; });
  }

  /* Copy-to-clipboard (BibTeX) */
  function initCopy() {
    $$("[data-copy]").forEach((btn) => btn.addEventListener("click", async () => {
      const src = doc.getElementById(btn.dataset.copy);
      if (!src) return;
      const text = src.textContent.trim();
      let ok = false;
      try {
        await navigator.clipboard.writeText(text);
        ok = true;
      } catch (e) {
        const ta = doc.createElement("textarea");
        ta.value = text;
        ta.setAttribute("readonly", "");
        ta.style.cssText = "position:fixed;opacity:0;pointer-events:none";
        doc.body.appendChild(ta);
        ta.select();
        try { ok = doc.execCommand("copy"); } catch (err) { ok = false; }
        ta.remove();
      }
      const status = btn.parentElement.querySelector(".copy-status");
      if (status) status.textContent = ok ? "Copied!" : "Copy failed: open “Show BibTeX” and copy by hand.";
      clearTimeout(btn._t);
      btn._t = setTimeout(() => { if (status) status.textContent = ""; }, 2600);
    }));
  }

  /* Post table of contents with scroll-spy */
  function initToc() {
    const toc = $("[data-toc]");
    const body = $("[data-post-body]");
    if (!toc || !body) return;
    const heads = $$("h2[id], h3[id]", body);
    if (heads.length < 2) return;
    const list = $("ol", toc);
    const links = heads.map((h) => {
      const li = doc.createElement("li");
      li.className = `lvl-${h.tagName[1]}`;
      const a = doc.createElement("a");
      a.href = `#${h.id}`;
      a.textContent = h.textContent;
      li.append(a);
      list.append(li);
      return a;
    });
    toc.hidden = false;
    onScroll(() => {
      let active = 0;
      heads.forEach((h, i) => { if (h.getBoundingClientRect().top < 140) active = i; });
      links.forEach((a, i) => {
        a.classList.toggle("is-active", i === active);
        if (i === active) a.setAttribute("aria-current", "location"); else a.removeAttribute("aria-current");
      });
    });
  }

  /* Experience: expandable timeline entries */
  function initDisclosure() {
    $$(".xp-toggle").forEach((btn) => btn.addEventListener("click", () => {
      const item = btn.closest(".xp-item");
      const open = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", String(open));
      item.classList.toggle("is-open", open);
      const lbl = $(".lbl", btn);
      if (lbl) lbl.textContent = open ? "Hide details" : "Details";
      setTimeout(() => doc.dispatchEvent(new Event("layoutchange")), 470);
    }));
  }

  /* Research figures: play once in view; age the network on touch devices */
  function initFigures() {
    const hosts = $$(".fig-host");
    if (!hosts.length) return;
    if ("IntersectionObserver" in window) {
      const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); } });
      }, { threshold: 0.35 });
      hosts.forEach((h) => io.observe(h));
    } else {
      hosts.forEach((h) => h.classList.add("is-in"));
    }
    if (!matchMedia("(hover: hover)").matches && !reduced()) {
      $$(".fig--network-ageing").forEach((svg) => {
        const host = svg.closest(".fig-host");
        setInterval(() => { if (!doc.hidden) host.classList.toggle("is-older"); }, 3200);
      });
    }
  }

  /* Contact form (Formspree) */
  function initForm() {
    const form = $("[data-contact-form]");
    if (!form) return;
    const status = $(".form-status", form);
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      status.className = "form-status";
      if (form.action.includes("YOUR_FORM_ID")) {
        status.textContent = "The contact form is not connected yet. Please reach me on LinkedIn for now.";
        status.classList.add("is-error");
        return;
      }
      const btn = $('[type="submit"]', form);
      btn.disabled = true;
      status.textContent = "Sending…";
      try {
        const r = await fetch(form.action, { method: "POST", body: new FormData(form), headers: { Accept: "application/json" } });
        if (!r.ok) throw new Error(String(r.status));
        form.reset();
        status.textContent = "Thank you, your message has been sent.";
        status.classList.add("is-ok");
      } catch (err) {
        status.textContent = "Sorry, the message could not be sent. Please try again, or reach me on LinkedIn.";
        status.classList.add("is-error");
      } finally {
        btn.disabled = false;
      }
    });
  }

  /* Page transitions: fade/slide fallback where cross-document view transitions are unsupported */
  function initPageTransitions() {
    addEventListener("pageswap", () => {
      const av = $(".hero-avatar");
      if (!av) return;
      const r = av.getBoundingClientRect();
      if (r.bottom < 0 || r.top > innerHeight) av.style.viewTransitionName = "none";
    });
    addEventListener("pageshow", (e) => {
      if (!e.persisted) return;
      root.classList.remove("is-leaving");
      const av = $(".hero-avatar");
      if (av) av.style.viewTransitionName = "";
    });
    if (!root.classList.contains("no-vt")) return;
    doc.addEventListener("click", (e) => {
      if (reduced() || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      const a = e.target.closest("a[href]");
      if (!a || (a.target && a.target !== "_self") || a.hasAttribute("download")) return;
      const url = new URL(a.href, location.href);
      if (url.origin !== location.origin) return;
      if (url.pathname === location.pathname) return;
      if (/\.(pdf|xml|json|webp|jpe?g|png|svg)$/i.test(url.pathname)) return;
      e.preventDefault();
      root.classList.add("is-leaving");
      setTimeout(() => { location.href = url.href; }, 170);
    });
  }

  [initTheme, initScroll, initMenu, initReveal, initTimelines, initTilt, initMagnetic, initCountUp, initTyped,
    initHeroNet, initFilters, initBlog, initModal, initMasonry, initLightbox, initCopy, initToc, initDisclosure,
    initFigures, initForm, initPageTransitions].forEach((fn) => {
    try { fn(); } catch (err) { if (window.console) console.error(`[site] ${fn.name} failed`, err); }
  });
})();
