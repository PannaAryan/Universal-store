/* Dokan AI — progressive enhancement for marketing, dashboard and storefront pages. */
(function () {
  "use strict";
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const csrf = () => ($("[name=csrfmiddlewaretoken]") || {}).value || "";

  /* Sticky nav: solid background once scrolled */
  const nav = $("[data-nav]");
  if (nav) {
    const onScroll = () => nav.classList.toggle("is-scrolled", window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* Mobile menu */
  const toggle = $("[data-menu-toggle]");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const open = document.body.classList.toggle("menu-open");
      toggle.setAttribute("aria-expanded", String(open));
      toggle.querySelector("use").setAttribute("href", open ? "#i-x" : "#i-menu");
    });
    $$("[data-mobile-menu] a").forEach((a) => a.addEventListener("click", () => document.body.classList.remove("menu-open")));
  }

  /* Dashboard sidebar */
  const side = $("[data-sidebar-toggle]");
  if (side) side.addEventListener("click", () => document.body.classList.toggle("sidebar-open"));
  const scrim = $("[data-sidebar-scrim]");
  if (scrim) scrim.addEventListener("click", () => document.body.classList.remove("sidebar-open"));

  /* Reveal on scroll */
  const reveals = $$(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-in"));
  }

  /* Toasts */
  $$("[data-toast]").forEach((t, i) => {
    const close = () => { t.classList.add("is-leaving"); setTimeout(() => t.remove(), 300); };
    t.querySelector("[data-toast-close]").addEventListener("click", close);
    setTimeout(close, 5200 + i * 400);
  });
  window.toast = function (text, kind) {
    let wrap = $(".toasts");
    if (!wrap) { wrap = document.createElement("div"); wrap.className = "toasts"; document.body.appendChild(wrap); }
    const t = document.createElement("div");
    t.className = "toast " + (kind || "");
    t.innerHTML = '<svg class="i"><use href="#i-' + (kind === "error" ? "x-circle" : "check-circle") + '"/></svg><span></span>';
    t.querySelector("span").textContent = text;
    wrap.appendChild(t);
    setTimeout(() => { t.classList.add("is-leaving"); setTimeout(() => t.remove(), 300); }, 4500);
  };

  /* Pricing: monthly / annual */
  $$("[data-billing]").forEach((wrap) => {
    $$("[data-billing-set]", wrap).forEach((btn) => btn.addEventListener("click", () => {
      $$("[data-billing-set]", wrap).forEach((b) => b.classList.toggle("active", b === btn));
      wrap.classList.toggle("is-annual", btn.dataset.billingSet === "annual");
      $$("input[name=cycle]", wrap).forEach((i) => { i.value = btn.dataset.billingSet; });
    }));
  });

  /* Slug auto-fill */
  const slugSrc = $("[data-slug-source]"), slugDst = $("[data-slug-target]");
  if (slugSrc && slugDst) {
    let touched = !!slugDst.value;
    slugDst.addEventListener("input", () => { touched = true; });
    const slugify = (s) => s.toLowerCase().normalize("NFKD").replace(/[^\w\s-]/g, "").trim().replace(/[\s_-]+/g, "-").slice(0, 50);
    const preview = $("[data-slug-preview]");
    const update = () => { if (preview) preview.textContent = (slugDst.value || "yourshop"); };
    slugSrc.addEventListener("input", () => { if (!touched) slugDst.value = slugify(slugSrc.value); update(); });
    slugDst.addEventListener("input", update);
    update();
  }

  /* Image dropzones with preview */
  $$("[data-dropzone]").forEach((dz) => {
    const input = $("input[type=file]", dz);
    const show = (file) => {
      if (!file || !file.type.startsWith("image/")) return;
      let img = $("img", dz);
      if (!img) { img = document.createElement("img"); img.alt = ""; dz.appendChild(img); }
      img.src = URL.createObjectURL(file);
      dz.classList.add("has-image");
    };
    input.addEventListener("change", () => show(input.files[0]));
    ["dragenter", "dragover"].forEach((ev) => dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("is-over"); }));
    ["dragleave", "drop"].forEach((ev) => dz.addEventListener(ev, () => dz.classList.remove("is-over")));
    dz.addEventListener("drop", (e) => {
      e.preventDefault();
      if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; show(input.files[0]); }
    });
  });

  /* Typewriter helper for AI results */
  function typeInto(el, text, speed) {
    return new Promise((resolve) => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { el.textContent = text; return resolve(); }
      el.textContent = ""; el.classList.add("typing");
      let i = 0;
      const step = Math.max(1, Math.round(text.length / 90));
      (function tick() {
        i += step; el.textContent = text.slice(0, i);
        if (i < text.length) setTimeout(tick, speed || 12); else { el.classList.remove("typing"); resolve(); }
      })();
    });
  }

  function errorText(data) {
    if (data.error) return data.error;
    if (data.errors) return Object.values(data.errors).flat().join(" ");
    return "Something went wrong. Please try again.";
  }

  /* Public Snap & Sell demo */
  const demo = $("[data-snap-demo]");
  if (demo) {
    const out = $("[data-snap-result]");
    demo.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btn = $("button[type=submit]", demo);
      btn.classList.add("is-loading");
      out.innerHTML = '<div class="result-empty"><span class="icon-tile orange"><span class="spinner"></span></span><p>Reading your photo and writing the listing…</p></div>';
      try {
        const res = await fetch(demo.action, { method: "POST", body: new FormData(demo), headers: { "X-CSRFToken": csrf() } });
        const data = await res.json();
        if (!data.ok) throw new Error(errorText(data));
        renderListing(out, data.listing, demo);
        const left = $("[data-snap-remaining]");
        if (left) left.textContent = data.remaining + " free tries left";
      } catch (err) {
        out.innerHTML = '<div class="result-empty"><span class="icon-tile orange"><svg class="i"><use href="#i-alert"/></svg></span><p></p></div>';
        $("p", out).textContent = err.message;
      } finally {
        btn.classList.remove("is-loading");
      }
    });
  }

  function renderListing(out, l, form) {
    const price = form.querySelector("[name=price]").value;
    const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    out.innerHTML = `
      <div style="display:flex;justify-content:space-between;gap:1rem;align-items:center;margin-bottom:1rem;flex-wrap:wrap">
        <span class="hv-ai"><svg class="i"><use href="#i-sparkle"/></svg> ${l.source === "ai" ? "Written by Claude AI" : "Written by the template writer"}</span>
        <span class="badge badge-green">Ready to publish</span>
      </div>
      <h3 data-t="title"></h3>
      <div class="bn-title" lang="bn">${esc(l.title_bn)}</div>
      <div class="hv-price" style="margin:.8rem 0 0"><strong>৳${esc(Number(price || 0).toLocaleString("en-IN"))}</strong></div>
      <div class="result-block"><h5>Description · English</h5><p data-t="en"></p></div>
      <div class="result-block"><h5>বিবরণ · Bangla</h5><p lang="bn">${esc(l.description_bn)}</p></div>
      <div class="result-block"><h5>Highlights</h5><ul class="check-list" style="margin:0">${l.highlights.map((h) => `<li><svg class="i"><use href="#i-check"/></svg>${esc(h)}</li>`).join("")}</ul></div>
      ${l.variants.length ? `<div class="result-block"><h5>Variants</h5><div class="chips">${l.variants.map((v) => `<span class="chip">${esc(v)}</span>`).join("")}</div></div>` : ""}
      <div class="result-block"><h5>Tags</h5><div class="chips">${l.tags.map((t) => `<span class="chip green">#${esc(t)}</span>`).join("")}</div></div>
      <div class="result-block"><h5>Google preview</h5><div class="serp"><div class="u">yourshop.dokan.ai › products</div><div class="t">${esc(l.seo_title)}</div><div class="d">${esc(l.seo_description)}</div></div></div>`;
    typeInto($("[data-t=title]", out), l.title, 20).then(() => typeInto($("[data-t=en]", out), l.description_en, 8));
  }

  /* Dashboard: AI fill for the product form */
  const aiBtn = $("[data-ai-generate]");
  if (aiBtn) {
    aiBtn.addEventListener("click", async () => {
      const form = aiBtn.closest("form");
      const fd = new FormData();
      const title = form.querySelector("[name=title]").value;
      const price = form.querySelector("[name=price]").value;
      const image = form.querySelector("[name=image]");
      if (!price) { window.toast("Add a price first so the AI can write the listing.", "error"); form.querySelector("[name=price]").focus(); return; }
      if (!title && !(image && image.files.length)) { window.toast("Add a photo or a short title first.", "error"); return; }
      fd.append("title", title); fd.append("price", price);
      if (image && image.files.length) fd.append("image", image.files[0]);
      aiBtn.classList.add("is-loading");
      try {
        const res = await fetch(aiBtn.dataset.url, { method: "POST", body: fd, headers: { "X-CSRFToken": csrf() } });
        const data = await res.json();
        if (!data.ok) throw new Error(errorText(data));
        const l = data.listing;
        const set = (name, value) => {
          const el = form.querySelector(`[name=${name}]`);
          if (!el) return;
          el.value = value;
          el.dispatchEvent(new Event("input"));
          const f = el.closest(".field");
          if (f) { f.classList.remove("ai-filled"); void f.offsetWidth; f.classList.add("ai-filled"); }
        };
        set("title", l.title); set("title_bn", l.title_bn);
        set("description_en", l.description_en); set("description_bn", l.description_bn);
        set("highlights", l.highlights.join("\n")); set("variants", l.variants.join(", "));
        set("tags", l.tags.join(", ")); set("seo_title", l.seo_title); set("seo_description", l.seo_description);
        set("ai_generated", "True");
        const used = $("[data-ai-used]");
        if (used) used.textContent = String(Number(used.textContent) + 1);
        window.toast(l.source === "ai" ? "Listing written by Claude AI — review and save." : "Listing drafted — review and save.");
      } catch (err) {
        window.toast(err.message, "error");
      } finally {
        aiBtn.classList.remove("is-loading");
      }
    });
  }

  /* Character counters */
  $$("[data-count]").forEach((el) => {
    const target = $("#" + el.dataset.count);
    if (!target) return;
    const max = Number(el.dataset.max);
    const upd = () => { el.textContent = `${target.value.length}/${max}`; el.style.color = target.value.length > max ? "var(--danger)" : ""; };
    target.addEventListener("input", upd); upd();
  });

  /* Copy to clipboard */
  $$("[data-copy]").forEach((b) => b.addEventListener("click", () => {
    navigator.clipboard && navigator.clipboard.writeText(b.dataset.copy).then(() => window.toast("Link copied"));
  }));

  /* Confirm destructive actions */
  $$("[data-confirm]").forEach((f) => f.addEventListener("submit", (e) => { if (!confirm(f.dataset.confirm)) e.preventDefault(); }));

  /* Storefront: quantity steppers & variant pills */
  $$("[data-qty]").forEach((w) => {
    const input = $("input", w);
    $$("button", w).forEach((b) => b.addEventListener("click", () => {
      const min = Number(input.min || 0), max = Number(input.max || 999);
      input.value = Math.min(max, Math.max(min, Number(input.value || 0) + Number(b.dataset.step)));
      input.dispatchEvent(new Event("change"));
    }));
  });
  $$("[data-autosubmit]").forEach((el) => el.addEventListener("change", () => el.form.submit()));

  /* Checkout: live delivery fee */
  const co = $("[data-checkout]");
  if (co) {
    const fees = { "1": Number(co.dataset.feeIn), "0": Number(co.dataset.feeOut) };
    const base = Number(co.dataset.base);
    const upd = () => {
      const area = ($("input[name=inside_dhaka]:checked", co) || {}).value || "1";
      $("[data-fee]").textContent = "৳" + fees[area].toLocaleString("en-IN");
      $("[data-total]").textContent = "৳" + (base + fees[area]).toLocaleString("en-IN");
    };
    $$("input[name=inside_dhaka]", co).forEach((r) => r.addEventListener("change", upd));
    upd();
  }

  /* Onboarding wizard */
  const wiz = $("[data-wizard]");
  if (wiz) {
    const steps = $$("[data-step]", wiz);
    const dots = $$("[data-step-dot]");
    let i = 0;
    const firstErr = steps.findIndex((s) => $(".has-error", s));
    if (firstErr > -1) i = firstErr;
    const show = () => {
      steps.forEach((s, n) => { s.hidden = n !== i; });
      dots.forEach((d, n) => { d.classList.toggle("done", n < i); d.classList.toggle("current", n === i); });
      $("[data-prev]", wiz).hidden = i === 0;
      $("[data-next]", wiz).hidden = i === steps.length - 1;
      $("[data-submit]", wiz).hidden = i !== steps.length - 1;
    };
    $("[data-next]", wiz).addEventListener("click", () => {
      const invalid = $$("input,select,textarea", steps[i]).find((el) => !el.checkValidity());
      if (invalid) { invalid.reportValidity(); return; }
      i = Math.min(steps.length - 1, i + 1); show();
    });
    $("[data-prev]", wiz).addEventListener("click", () => { i = Math.max(0, i - 1); show(); });
    $$("[data-theme-color]", wiz).forEach((sw) => sw.addEventListener("click", () => {
      const input = $("input[type=color]", wiz);
      input.value = sw.dataset.themeColor; input.dispatchEvent(new Event("input"));
    }));
    const color = $("input[type=color]", wiz);
    const prev = $("[data-brand-preview]");
    if (color && prev) { const u = () => prev.style.setProperty("--brand", color.value); color.addEventListener("input", u); u(); }
    show();
  }
})();
