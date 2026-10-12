/* LEMI Office — small, dependency-free behaviours */
(function () {
  "use strict";

  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Smooth scrolling for in-page links only, once the page has settled ---------- */
  window.addEventListener("load", function () {
    setTimeout(function () { document.documentElement.classList.add("smooth"); }, 400);
  });

  /* ---------- Header: hide on the way down, return on the way up ---------- */
  var hdr = $("[data-hdr]");
  var fab = $("[data-fab]");
  var ftr = $(".ftr");
  var heroImg = $("[data-drift]");
  var lastY = window.scrollY;
  var ticking = false;

  function onScroll() {
    var y = window.scrollY;
    if (hdr && !document.documentElement.classList.contains("nav-open")) {
      if (y > 220 && y > lastY + 4) hdr.classList.add("is-hidden");
      else if (y < lastY - 4 || y <= 220) hdr.classList.remove("is-hidden");
    }
    if (fab) {
      var nearEnd = ftr && ftr.getBoundingClientRect().top < window.innerHeight - 40;
      fab.classList.toggle("is-on", y > 520 && !nearEnd);
    }
    if (heroImg && !calm && y < window.innerHeight * 1.6) {
      heroImg.style.transform = "translate3d(0," + (y * 0.045).toFixed(1) + "px,0)";
    }
    lastY = y;
    ticking = false;
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  onScroll();

  /* ---------- Mobile menu ---------- */
  var burger = $("[data-burger]");
  var mnav = $("#mnav");
  function setNav(open) {
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    mnav.classList.toggle("is-open", open);
    document.documentElement.classList.toggle("nav-open", open);
    document.body.style.overflow = open ? "hidden" : "";
  }
  if (burger && mnav) {
    burger.addEventListener("click", function () {
      setNav(burger.getAttribute("aria-expanded") !== "true");
    });
    mnav.addEventListener("click", function (e) {
      if (e.target.closest("a")) setNav(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") setNav(false);
    });
    window.matchMedia("(min-width: 901px)").addEventListener("change", function (e) {
      if (e.matches) setNav(false);
    });
  }

  /* ---------- The strand: measure the line as it appears on screen, then draw it ---------- */
  function draw(svg) {
    var path = $("path", svg);
    if (calm || !path.getTotalLength) { svg.classList.add("is-ready"); return; }
    var box = svg.getBoundingClientRect(), vb = svg.viewBox.baseVal;
    var sx = box.width / vb.width, sy = box.height / vb.height;
    var total = path.getTotalLength(), steps = 240, len = 0, a = path.getPointAtLength(0), b;
    for (var k = 1; k <= steps; k++) {
      b = path.getPointAtLength(total * k / steps);
      len += Math.hypot((b.x - a.x) * sx, (b.y - a.y) * sy);
      a = b;
    }
    len = Math.ceil(len) + 4;
    path.style.strokeDasharray = len;
    path.style.strokeDashoffset = len;
    svg.classList.add("is-ready");
    path.getBoundingClientRect(); // commit the start state before animating
    path.style.transition = "stroke-dashoffset 3.6s cubic-bezier(0.3, 0.6, 0.15, 1) 0.4s";
    path.style.strokeDashoffset = 0;
    path.addEventListener("transitionend", function () {
      path.style.strokeDasharray = path.style.strokeDashoffset = path.style.transition = "";
    }, { once: true });
  }

  /* ---------- Reveal on scroll ---------- */
  var targets = $$("[data-r], [data-clip], .strand");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        en.target.classList.add("in");
        if (en.target.classList.contains("strand")) draw(en.target);
        io.unobserve(en.target);
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    targets.forEach(function (t) { io.observe(t); });
  } else {
    targets.forEach(function (t) { t.classList.add("in", "is-ready"); });
  }

  /* ---------- Opening hours, always in New York time ---------- */
  var HOURS = { 0: [10, 19], 1: null, 2: null, 3: [10, 19], 4: [10, 19], 5: [10, 19], 6: [10, 19] }; // null = closed
  var DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
  function clock(h) { return (h % 12 || 12) + "\u00a0" + (h < 12 ? "AM" : "PM"); }
  try {
    var parts = {};
    new Intl.DateTimeFormat("en-US", {
      timeZone: "America/New_York", weekday: "long", hour: "numeric", minute: "numeric", hourCycle: "h23"
    }).formatToParts(new Date()).forEach(function (p) { parts[p.type] = p.value; });
    var day = DAYS.indexOf(parts.weekday);
    var now = Number(parts.hour) + Number(parts.minute) / 60;
    var today = HOURS[day];
    var open = !!today && now >= today[0] && now < today[1];
    var text;
    if (open) text = "Open today until " + clock(today[1]);
    else if (today && now < today[0]) text = "Opens today at " + clock(today[0]);
    else {
      var next = (day + 1) % 7;
      while (!HOURS[next]) next = (next + 1) % 7;
      text = "Opens " + DAYS[next] + " at " + clock(HOURS[next][0]);
    }

    $$("[data-status]").forEach(function (el) {
      el.innerHTML = '<i class="dot' + (open ? " is-open" : "") + '"></i>' + text;
    });
    $$('[data-day="' + day + '"]').forEach(function (el) { el.classList.add("is-today"); });
  } catch (e) { /* static hours remain */ }

  /* ---------- Client voices ---------- */
  $$("[data-voices]").forEach(function (box) {
    var quotes = $$("blockquote", box);
    var count = $("[data-count]", box);
    var i = 0, timer;
    function show(n) {
      i = (n + quotes.length) % quotes.length;
      quotes.forEach(function (q, k) {
        q.classList.toggle("is-on", k === i);
        q.setAttribute("aria-hidden", String(k !== i));
      });
      if (count) count.textContent = (i + 1) + " / " + quotes.length;
    }
    function play() { if (!calm) { stop(); timer = setInterval(function () { show(i + 1); }, 7000); } }
    function stop() { clearInterval(timer); }
    $(".next", box).addEventListener("click", function () { show(i + 1); play(); });
    $(".prev", box).addEventListener("click", function () { show(i - 1); play(); });
    box.addEventListener("mouseenter", stop);
    box.addEventListener("mouseleave", play);
    box.addEventListener("focusin", stop);
    box.addEventListener("focusout", play);
    show(0); play();
  });

  /* ---------- Work strip: drag to scroll + progress hairline ---------- */
  $$("[data-strip]").forEach(function (strip) {
    var bar = $("[data-bar]");
    function progress() {
      if (!bar) return;
      var max = strip.scrollWidth - strip.clientWidth;
      var seen = strip.clientWidth / strip.scrollWidth;
      var p = max > 0 ? strip.scrollLeft / max : 0;
      bar.style.transform = "scaleX(" + (seen + (1 - seen) * p).toFixed(4) + ")";
    }
    strip.addEventListener("scroll", progress, { passive: true });
    window.addEventListener("resize", progress);
    progress();

    var down = false, startX = 0, startL = 0;
    strip.addEventListener("pointerdown", function (e) {
      if (e.pointerType !== "mouse") return;
      down = true; startX = e.clientX; startL = strip.scrollLeft;
    });
    window.addEventListener("pointermove", function (e) {
      if (!down) return;
      if (Math.abs(e.clientX - startX) > 4) strip.classList.add("is-drag");
      strip.scrollLeft = startL - (e.clientX - startX);
    });
    window.addEventListener("pointerup", function () {
      down = false; strip.classList.remove("is-drag");
    });
  });
})();
