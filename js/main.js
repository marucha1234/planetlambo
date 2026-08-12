/* ————————————————————————————————
   Planetlambo · Paper Studio
   Loader (knockout type over the reel), reveals, counters,
   video progress, cinema mode.
———————————————————————————————— */

const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const heroVideo = document.getElementById("heroVideo");

/* ———— Loader ———— */

const loader = document.getElementById("loader");
const loaderVideo = document.getElementById("loaderVideo");
const loaderPct = document.getElementById("loaderPct");

// Start the loader footage at a strong moment of the reel
loaderVideo.addEventListener("loadedmetadata", () => {
  try { loaderVideo.currentTime = 4; } catch (e) {}
}, { once: true });

// iOS sometimes ignores the autoplay attribute — insist via JS.
loaderVideo.play().catch(() => {});

// iOS/WebKit can't apply CSS blend modes over hardware video layers, so
// the knockout is blended over a canvas that mirrors the video frames.
// If the video never plays, the poster is painted as a static fallback.
const loaderCanvas = document.getElementById("loaderCanvas");
const lctx = loaderCanvas.getContext("2d");
const posterImg = new Image();
posterImg.src = "assets/poster.jpg";

const coverDraw = (source, sw, sh) => {
  const cw = loaderCanvas.width;
  const ch = loaderCanvas.height;
  if (!sw || !sh) return;
  const scale = Math.max(cw / sw, ch / sh);
  const dw = sw * scale;
  const dh = sh * scale;
  lctx.drawImage(source, (cw - dw) / 2, (ch - dh) / 2, dw, dh);
};

const sizeLoaderCanvas = () => {
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  loaderCanvas.width = Math.round(window.innerWidth * dpr);
  loaderCanvas.height = Math.round(window.innerHeight * dpr);
};
sizeLoaderCanvas();

const paintLoader = () => {
  if (document.body.classList.contains("loaded")) return;
  if (loaderVideo.readyState >= 2) {
    coverDraw(loaderVideo, loaderVideo.videoWidth, loaderVideo.videoHeight);
  } else if (heroVideo && heroVideo.readyState >= 2) {
    // Mobile (no dedicated loader footage) or slow loader buffer:
    // mirror the hero reel — same file, zero extra download.
    coverDraw(heroVideo, heroVideo.videoWidth, heroVideo.videoHeight);
  } else if (posterImg.complete && posterImg.naturalWidth) {
    coverDraw(posterImg, posterImg.naturalWidth, posterImg.naturalHeight);
  }
  requestAnimationFrame(paintLoader);
};
requestAnimationFrame(paintLoader);

const finishLoader = () => {
  if (document.body.classList.contains("loaded")) return;
  document.body.classList.add("loaded");
  document.body.classList.remove("loading");
  loader.classList.add("done");
  // Free the extra decoder once the curtain is gone
  setTimeout(() => { loaderVideo.pause(); loaderVideo.removeAttribute("src"); loaderVideo.load(); }, 1100);
};

if (reduceMotion || !document.documentElement.classList.contains("js")) {
  finishLoader();
} else {
  let pct = 0;
  let videoReady = loaderVideo.readyState >= 3 || !loaderVideo.getAttribute("src");
  loaderVideo.addEventListener("canplay", () => { videoReady = true; }, { once: true });
  const t0 = performance.now();
  const tick = () => {
    const elapsed = performance.now() - t0;
    // Brisk count to 90, hold briefly for the video, always release by 3s
    const cap = videoReady || elapsed > 3000 ? 100 : 90;
    pct = Math.min(pct + 2.2, cap, elapsed / 26);
    loaderPct.textContent = String(Math.floor(pct)).padStart(3, "0");
    if (pct >= 100) { setTimeout(finishLoader, 350); return; }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
  // Absolute safety net — the loader must never trap the page
  setTimeout(finishLoader, 6000);
}

/* ———— Language toggle — ES primary, EN secondary ———— */

const setLang = (lang) => {
  document.querySelectorAll("[data-en]").forEach((el) => {
    if (!el.dataset.es) el.dataset.es = el.innerHTML;
    el.innerHTML = lang === "en" ? el.dataset.en : el.dataset.es;
  });
  document.documentElement.lang = lang;
  document.querySelectorAll(".lang-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.setlang === lang);
  });
  try { localStorage.setItem("pl-lang", lang); } catch (e) {}
  document.dispatchEvent(new CustomEvent("langchange"));
};

document.querySelectorAll(".lang-btn").forEach((b) => {
  b.addEventListener("click", () => setLang(b.dataset.setlang));
});

try {
  const saved = localStorage.getItem("pl-lang");
  if (saved === "en") setLang("en");
} catch (e) {}

/* ———— Nav — transparent over the hero, solid after ———— */

const nav = document.getElementById("siteNav");
const syncNav = () => {
  nav.classList.toggle("scrolled", window.scrollY > window.innerHeight - 80);
};
window.addEventListener("scroll", syncNav, { passive: true });
syncNav();

/* ———— Mobile index — burger toggle ———— */

const navBurger = document.getElementById("navBurger");

const setMenu = (open) => {
  document.body.classList.toggle("menu-open", open);
  navBurger.setAttribute("aria-expanded", String(open));
};

navBurger.addEventListener("click", () => {
  setMenu(!document.body.classList.contains("menu-open"));
});

// Navigating from the index closes the panel
document.querySelectorAll(".nav-links a").forEach((a) => {
  a.addEventListener("click", () => setMenu(false));
});

window.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && document.body.classList.contains("menu-open")) setMenu(false);
});

/* ———— Reveals ———— */

const io = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) {
      e.target.classList.add("in");
      io.unobserve(e.target);
    }
  }
}, { threshold: 0.12 });
document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

/* ———— Stat counters ———— */

const animateCount = (el) => {
  const end = +el.dataset.count;
  const suffix = el.dataset.suffix || "";
  const start = performance.now();
  const dur = 1400;
  const tick = (now) => {
    const p = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(end * eased) + suffix;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
};

const statIO = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (e.isIntersecting) {
      animateCount(e.target);
      statIO.unobserve(e.target);
    }
  }
}, { threshold: 0.6 });
document.querySelectorAll(".stat-num").forEach((el) => statIO.observe(el));

/* ———— Knockout title videos — play only while on screen ———— */

const _mob = matchMedia("(max-width:800px)").matches;
document.querySelectorAll(".knock-video").forEach((v) => {
  const knock = v.closest(".knock");
  v.src = _mob ? v.dataset.mob : v.dataset.desk;
  const offset = +v.dataset.offset || 0;
  let inView = false;
  let hovered = false;
  v.addEventListener("loadedmetadata", () => {
    try { v.currentTime = offset; } catch (e) {}
  }, { once: true });
  // Solid-ink fallback until the reel actually has frames to show
  knock.classList.add("no-video");
  v.addEventListener("canplay", () => knock.classList.remove("no-video"));
  v.addEventListener("error", () => knock.classList.add("no-video"));
  const sync = () => {
    if (inView && !hovered) v.play().catch(() => {});
    else v.pause();
  };
  // Freeze the frame while the cursor rests on the title
  knock.addEventListener("pointerenter", () => { hovered = true; sync(); });
  knock.addEventListener("pointerleave", () => { hovered = false; sync(); });
  const vio = new IntersectionObserver((entries) => {
    for (const e of entries) {
      inView = e.isIntersecting;
      sync();
    }
  }, { threshold: 0.1 });
  vio.observe(v);
});

/* ———— Hero video progress (—— 100) ———— */

const vprogFill = document.getElementById("vprogFill");
const vprogNum = document.getElementById("vprogNum");
heroVideo.addEventListener("timeupdate", () => {
  const p = heroVideo.duration ? heroVideo.currentTime / heroVideo.duration : 0;
  vprogFill.style.width = `${p * 100}%`;
  vprogNum.textContent = String(Math.round(p * 100)).padStart(3, "0");
});

// Pause the muted preview when it leaves the viewport
const heroIO = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (document.body.classList.contains("cinema-open")) return;
    if (e.isIntersecting) heroVideo.play().catch(() => {});
    else heroVideo.pause();
  }
}, { threshold: 0.1 });
heroIO.observe(heroVideo);

/* ———— Work filters — client & campaign type ———— */

const filterClient = document.getElementById("filterClient");
const filterType = document.getElementById("filterType");
const gridEmpty = document.getElementById("gridEmpty");
const showMore = document.getElementById("showMore");

// Collapsed by default: only the first 6 matching campaigns are visible
const VISIBLE_MAX = 6;
let expanded = false;

const showMoreLabel = () => {
  const en = document.documentElement.lang === "en";
  showMore.textContent = expanded
    ? (en ? "See less ↑" : "Ver menos ↑")
    : (en ? "See more ↓" : "Ver más ↓");
};

const applyFilters = () => {
  const client = filterClient.value;
  const type = filterType.value;
  let matches = 0;
  document.querySelectorAll(".grid .card").forEach((card) => {
    const match =
      (client === "all" || card.dataset.client === client) &&
      (type === "all" || card.dataset.type === type);
    const show = match && (expanded || matches < VISIBLE_MAX);
    if (match) matches++;
    card.style.display = show ? "" : "none";
  });
  gridEmpty.hidden = matches > 0;
  showMore.parentElement.hidden = matches <= VISIBLE_MAX;
  showMoreLabel();
};

filterClient.addEventListener("change", () => { expanded = false; applyFilters(); });
filterType.addEventListener("change", () => { expanded = false; applyFilters(); });

showMore.addEventListener("click", () => {
  expanded = !expanded;
  applyFilters();
  if (!expanded) {
    document.getElementById("work").scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

document.addEventListener("langchange", showMoreLabel);
applyFilters();

/* ———— Touch screens: cards bloom into color as you scroll past them ———— */

if (window.matchMedia("(hover: none)").matches) {
  const colorIO = new IntersectionObserver((entries) => {
    for (const e of entries) {
      e.target.classList.toggle("in-color", e.isIntersecting);
    }
  }, { rootMargin: "-18% 0px -18% 0px", threshold: 0.35 });
  document.querySelectorAll(".grid .card").forEach((c) => colorIO.observe(c));
}

/* ———— Case modal — campaign clip + description on card click ———— */

const caseModal = document.getElementById("caseModal");
const caseVideo = document.getElementById("caseVideo");
const caseClose = document.getElementById("caseClose");
let segStart = 0;
let segEnd = 0;

const openCase = (card) => {
  // The campaign's own frame as poster — never a generic reel frame
  const cardImg = card.querySelector(".card-img img");
  if (cardImg) caseVideo.poster = cardImg.currentSrc || cardImg.src;
  // Full campaign video when available; reel segment as fallback
  const src = card.dataset.video || "assets/reel.mp4";
  if (card.dataset.video) {
    segStart = 0;
    segEnd = 0;
    caseVideo.loop = true; // full piece, loops natively
  } else {
    segStart = parseFloat(card.dataset.start || "0");
    segEnd = parseFloat(card.dataset.end || "0");
    caseVideo.loop = false; // reel excerpt loops via segment handler
  }
  document.getElementById("caseClient").textContent = card.querySelector(".card-meta").textContent;
  document.getElementById("caseTitle").textContent = card.querySelector(".card-title").textContent;
  document.getElementById("caseDesc").textContent = card.querySelector(".card-desc").textContent;
  document.body.classList.add("case-open");
  caseModal.setAttribute("aria-hidden", "false");
  document.documentElement.style.overflow = "hidden";
  heroVideo.pause();
  requestAnimationFrame(() => { if (typeof syncHint === "function") syncHint(); });
  const startPlayback = () => {
    try { caseVideo.currentTime = segStart; } catch (e) {}
    caseVideo.muted = false;
    caseVideo.volume = 1;
    // Direct user gesture: play with sound; if the browser blocks it,
    // the campaign poster stays up and a tap on the video starts playback.
    caseVideo.play().catch(() => {});
  };
  if (caseVideo.getAttribute("src") !== src) {
    caseVideo.setAttribute("src", src);
    caseVideo.load();
    caseVideo.addEventListener("loadedmetadata", startPlayback, { once: true });
  } else if (caseVideo.readyState >= 1) {
    startPlayback();
  } else {
    caseVideo.addEventListener("loadedmetadata", startPlayback, { once: true });
  }
};

const closeCase = () => {
  document.body.classList.remove("case-open");
  caseModal.setAttribute("aria-hidden", "true");
  document.documentElement.style.overflow = "";
  caseVideo.pause();
  heroVideo.play().catch(() => {});
};

document.querySelectorAll(".grid .card").forEach((card) => {
  card.addEventListener("click", (e) => {
    e.preventDefault();
    openCase(card);
  });
});

// Loop the campaign segment
caseVideo.addEventListener("timeupdate", () => {
  if (segEnd && caseVideo.currentTime >= segEnd) {
    caseVideo.currentTime = segStart;
  }
});

/* Elegant mini-player: tap toggles playback, hairline progress with seek */

const caseCur = document.getElementById("caseCur");
const caseDur = document.getElementById("caseDur");
const caseFill = document.getElementById("caseFill");
const caseProgress = document.getElementById("caseProgress");

caseVideo.addEventListener("click", () => {
  if (caseVideo.paused) caseVideo.play().catch(() => {});
  else caseVideo.pause();
});

// Play cue: visible whenever the piece is paused so the tap is obvious
const caseHint = document.getElementById("caseHint");
const syncHint = () => {
  caseHint.classList.toggle("show", caseVideo.paused && document.body.classList.contains("case-open"));
};
caseVideo.addEventListener("playing", syncHint);
caseVideo.addEventListener("pause", syncHint);
caseModal.addEventListener("transitionend", syncHint);

caseVideo.addEventListener("loadedmetadata", () => {
  caseDur.textContent = `${fmt(caseVideo.duration / 60)}:${fmt(caseVideo.duration % 60)}`;
});

caseVideo.addEventListener("timeupdate", () => {
  const p = caseVideo.duration ? caseVideo.currentTime / caseVideo.duration : 0;
  caseFill.style.width = `${p * 100}%`;
  caseCur.textContent = `${fmt(caseVideo.currentTime / 60)}:${fmt(caseVideo.currentTime % 60)}`;
});

caseProgress.addEventListener("click", (e) => {
  e.stopPropagation();
  const r = caseProgress.getBoundingClientRect();
  const p = Math.min(Math.max((e.clientX - r.left) / r.width, 0), 1);
  if (caseVideo.duration) caseVideo.currentTime = p * caseVideo.duration;
});

caseClose.addEventListener("click", closeCase);
caseModal.addEventListener("click", (e) => { if (e.target === caseModal) closeCase(); });

/* ———— Cinema mode — lights off, sound on ———— */

const cinema = document.getElementById("cinema");
const cinemaVideo = document.getElementById("cinemaVideo");
const cinemaFill = document.getElementById("cinemaFill");
const cinemaProgress = document.getElementById("cinemaProgress");
const cinemaTc = document.getElementById("cinemaTc");
const fmt = (n) => String(Math.floor(n)).padStart(2, "0");

const openCinema = () => {
  document.body.classList.add("cinema-open");
  cinema.setAttribute("aria-hidden", "false");
  document.documentElement.style.overflow = "hidden";
  heroVideo.pause();
  cinemaVideo.currentTime = 0;
  cinemaVideo.muted = false;
  cinemaVideo.volume = 1;
  cinemaVideo.play().catch(() => {});
};

const closeCinema = () => {
  document.body.classList.remove("cinema-open");
  cinema.setAttribute("aria-hidden", "true");
  document.documentElement.style.overflow = "";
  cinemaVideo.pause();
  heroVideo.play().catch(() => {});
};

document.getElementById("playReel").addEventListener("click", openCinema);
document.getElementById("reelBand").addEventListener("click", openCinema);
document.getElementById("cinemaClose").addEventListener("click", closeCinema);
cinemaVideo.addEventListener("ended", closeCinema);
window.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (document.body.classList.contains("cinema-open")) closeCinema();
  if (document.body.classList.contains("case-open")) closeCase();
});

cinemaVideo.addEventListener("timeupdate", () => {
  const p = cinemaVideo.duration ? cinemaVideo.currentTime / cinemaVideo.duration : 0;
  cinemaFill.style.width = `${p * 100}%`;
  const s = cinemaVideo.currentTime;
  cinemaTc.textContent = `${fmt(s / 60)}:${fmt(s % 60)}`;
});

cinemaProgress.addEventListener("click", (e) => {
  const r = cinemaProgress.getBoundingClientRect();
  const p = (e.clientX - r.left) / r.width;
  if (cinemaVideo.duration) cinemaVideo.currentTime = p * cinemaVideo.duration;
});
