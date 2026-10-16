/* Consulting Academy — single-page app. No dependencies; progress is kept in localStorage. */
(function () {
  "use strict";

  const D = window.CA_DATA;
  const KEY = "consultingAcademy.v1";
  const main = document.getElementById("main");

  /* ================================================================== */
  /* State                                                               */
  /* ================================================================== */
  function defaultState() {
    return {
      name: "",
      theme: null,
      xp: 0,
      lessons: {},        // frameworkId -> date completed
      quiz: {},           // "frameworkId:index" -> { choice, correct }
      cases: {},          // caseId -> { done, best, perfect, plays }
      stories: [],        // { id, qid, s, t, a, r, score, date }
      practiced: {},      // questionId -> true (XP already given)
      drafts: {},         // questionId -> { s, t, a, r }
      math: { best: 0, runs: 0, total: 0, duration: 60, types: null, bests: {} },
      mece: { duration: 120, mode: "free", runs: 0, best: {} },  // best: "promptId:mode" -> score
      daily: {},          // date -> { score, answers }
      quizPerfect: false,
      streak: { count: 0, best: 0, last: null },
      badges: {}          // badgeId -> date earned
    };
  }

  function load() {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? merge(defaultState(), JSON.parse(raw)) : defaultState();
    } catch (e) {
      return defaultState();
    }
  }
  function merge(base, saved) {
    if (!saved || typeof saved !== "object") return base;
    Object.keys(base).forEach(function (k) {
      if (saved[k] === undefined) return;
      if (base[k] && typeof base[k] === "object" && !Array.isArray(base[k])) {
        base[k] = Object.assign(base[k], saved[k]);
      } else {
        base[k] = saved[k];
      }
    });
    return base;
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) { /* private mode: progress lives for this tab only */ }
  }

  let S = load();

  /* ================================================================== */
  /* Helpers                                                             */
  /* ================================================================== */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function pad(n) { return n < 10 ? "0" + n : "" + n; }
  function dateStr(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function today() { return dateStr(new Date()); }
  function yesterday() { const d = new Date(); d.setDate(d.getDate() - 1); return dateStr(d); }
  function fmt(n) { return Number(n).toLocaleString("en-US", { maximumFractionDigits: 2 }); }
  function letter(i) { return String.fromCharCode(65 + i); }
  function shuffle(a, rnd) {
    rnd = rnd || Math.random;
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); const t = a[i]; a[i] = a[j]; a[j] = t; }
    return a;
  }
  /* Display order for answer options, so the right answer isn't always in the same slot. */
  function order(n, rnd) {
    const idx = [];
    for (let i = 0; i < n; i++) idx.push(i);
    return shuffle(idx, rnd);
  }
  function seeded(seedStr) {
    let h = 1779033703 ^ seedStr.length;
    for (let i = 0; i < seedStr.length; i++) { h = Math.imul(h ^ seedStr.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); }
    let a = h >>> 0;
    return function () { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  }
  /* Accepts "1,200,000", "1.2m", "450k", "3b", "12.5%", "$40". */
  function parseNum(v) {
    if (v == null) return NaN;
    let s = String(v).trim().toLowerCase().replace(/[$,%\s]/g, "").replace(/rp/g, "");
    let mult = 1;
    if (/[kmbt]$/.test(s)) {
      mult = { k: 1e3, m: 1e6, b: 1e9, t: 1e12 }[s.slice(-1)];
      s = s.slice(0, -1);
    }
    if (s === "" || isNaN(s)) return NaN;
    return parseFloat(s) * mult;
  }
  function bar(pct, cls) {
    return '<div class="bar ' + (cls || "") + '"><i style="width:' + Math.max(0, Math.min(100, pct)) + '%"></i></div>';
  }

  /* ================================================================== */
  /* Gamification                                                        */
  /* ================================================================== */
  function levelIndex(xp) {
    let idx = 0;
    D.levels.forEach(function (l, i) { if (xp >= l.xp) idx = i; });
    return idx;
  }
  function levelInfo() {
    const i = levelIndex(S.xp);
    const cur = D.levels[i];
    const next = D.levels[i + 1];
    const pct = next ? ((S.xp - cur.xp) / (next.xp - cur.xp)) * 100 : 100;
    return { i: i, cur: cur, next: next, pct: pct, toNext: next ? next.xp - S.xp : 0 };
  }

  function touchStreak() {
    const t = today();
    if (S.streak.last === t) return;
    S.streak.count = S.streak.last === yesterday() ? S.streak.count + 1 : 1;
    S.streak.last = t;
    S.streak.best = Math.max(S.streak.best || 0, S.streak.count);
  }

  function addXP(n, reason) {
    if (!n) return;
    const before = levelIndex(S.xp);
    S.xp += n;
    touchStreak();
    toast("+" + n + " XP" + (reason ? " · " + reason : ""), "xp");
    const after = levelIndex(S.xp);
    if (after > before) {
      toast("🎉 Promoted to " + D.levels[after].name + "!", "level");
      confetti();
    }
    checkBadges();
    save();
    renderHud();
  }

  function checkBadges() {
    const fw = D.frameworks;
    const core = fw.filter(function (f) { return f.group === "core"; });
    const doneCases = Object.keys(S.cases).filter(function (k) { return S.cases[k].done; });
    const lvl = levelIndex(S.xp);
    const rules = {
      "first-lesson": Object.keys(S.lessons).length >= 1,
      "core-done": core.every(function (f) { return S.lessons[f.id]; }),
      "all-frameworks": fw.every(function (f) { return S.lessons[f.id]; }),
      "first-case": doneCases.length >= 1,
      "all-cases": D.cases.every(function (c) { return S.cases[c.id] && S.cases[c.id].done; }),
      "perfect-case": doneCases.some(function (k) { return S.cases[k].perfect; }),
      "storyteller": S.stories.length >= 3,
      "math-10": S.math.best >= 10,
      "math-20": S.math.best >= 20,
      "mece-first": (S.mece.runs || 0) >= 1,
      "mece-master": D.mece.prompts.filter(function (p) {
        return Math.max(S.mece.best[p.id + ":free"] || 0, S.mece.best[p.id + ":builder"] || 0) >= 85;
      }).length >= 5,
      "quiz-perfect": !!S.quizPerfect,
      "streak-3": (S.streak.best || 0) >= 3,
      "streak-7": (S.streak.best || 0) >= 7,
      "level-consultant": lvl >= 3,
      "level-partner": lvl >= D.levels.length - 1
    };
    D.badges.forEach(function (b) {
      if (rules[b.id] && !S.badges[b.id]) {
        S.badges[b.id] = today();
        toast(b.icon + " Badge unlocked: " + b.name, "badge-t");
      }
    });
    save();
  }

  function toast(msg, kind) {
    const box = document.getElementById("toasts");
    const el = document.createElement("div");
    el.className = "toast " + (kind || "");
    el.setAttribute("role", "status");
    el.textContent = msg;
    box.appendChild(el);
    while (box.children.length > 3) box.firstChild.remove();
    setTimeout(function () { el.remove(); }, 3200);
  }

  function confetti() {
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const wrap = document.createElement("div");
    wrap.className = "confetti";
    const colors = ["#1f4fd1", "#0f9d8a", "#f2b84b", "#c2362f", "#6d93ff", "#3cc9b4"];
    for (let i = 0; i < 70; i++) {
      const p = document.createElement("i");
      p.style.left = Math.random() * 100 + "vw";
      p.style.background = colors[i % colors.length];
      p.style.animationDelay = Math.random() * 0.5 + "s";
      p.style.animationDuration = 1.2 + Math.random() * 1.2 + "s";
      wrap.appendChild(p);
    }
    document.body.appendChild(wrap);
    setTimeout(function () { wrap.remove(); }, 3200);
  }

  function renderHud() {
    const li = levelInfo();
    document.getElementById("hud").innerHTML =
      '<span class="hud-pill" title="Daily streak">🔥 ' + (streakAlive() ? S.streak.count : 0) + "</span>" +
      '<span class="hud-pill hide-sm" title="Level">🎓 ' + esc(li.cur.name) + "</span>" +
      '<span class="hud-pill" title="Experience points">⭐ ' + fmt(S.xp) + " XP</span>";
  }
  function streakAlive() { return S.streak.last === today() || S.streak.last === yesterday(); }

  /* ================================================================== */
  /* Theme                                                               */
  /* ================================================================== */
  function applyTheme() {
    if (S.theme) document.documentElement.setAttribute("data-theme", S.theme);
    else document.documentElement.removeAttribute("data-theme");
    const dark = S.theme ? S.theme === "dark" : window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    const btn = document.getElementById("themeBtn");
    btn.textContent = dark ? "☀️" : "🌙";
    btn.title = dark ? "Switch to light mode" : "Switch to dark mode";
  }
  document.getElementById("themeBtn").addEventListener("click", function () {
    const dark = S.theme ? S.theme === "dark" : window.matchMedia("(prefers-color-scheme: dark)").matches;
    S.theme = dark ? "light" : "dark";
    save();
    applyTheme();
  });

  /* ================================================================== */
  /* Router                                                              */
  /* ================================================================== */
  let cleanups = [];
  function onLeave(fn) { cleanups.push(fn); }

  function route() {
    cleanups.forEach(function (fn) { try { fn(); } catch (e) { /* ignore */ } });
    cleanups = [];
    const parts = (location.hash || "#/").replace(/^#\/?/, "").split("/");
    const name = parts[0] || "home";
    const arg = parts[1] ? decodeURIComponent(parts[1]) : null;
    const views = {
      home: viewHome,
      learn: viewLearn,
      framework: viewFramework,
      cases: viewCases,
      "case": viewCase,
      behavioral: viewBehavioral,
      practice: viewPractice,
      math: viewMath,
      mece: viewMece,
      daily: viewDaily,
      profile: viewProfile
    };
    (views[name] || viewNotFound)(arg);
    const navKey = { framework: "learn", "case": "cases", practice: "behavioral" }[name] || name;
    document.querySelectorAll(".nav a").forEach(function (a) {
      a.classList.toggle("active", a.dataset.nav === navKey);
    });
    renderHud();
    window.scrollTo(0, 0);
    main.focus({ preventScroll: true });
  }
  window.addEventListener("hashchange", route);
  // Clicking a link to the page you're already on (e.g. "MECE Practice" from a results screen) re-opens it.
  document.addEventListener("click", function (e) {
    const a = e.target.closest && e.target.closest('a[href^="#/"]');
    if (a && a.getAttribute("href") === (location.hash || "#/")) { e.preventDefault(); route(); }
  });

  /* ================================================================== */
  /* Views                                                               */
  /* ================================================================== */
  function nextUp() {
    const f = D.frameworks.find(function (x) { return !S.lessons[x.id]; });
    if (f) return { href: "#/framework/" + f.id, label: "Continue: " + f.name };
    const c = D.cases.find(function (x) { return !(S.cases[x.id] && S.cases[x.id].done); });
    if (c) return { href: "#/case/" + c.id, label: "Next case: " + c.title };
    return { href: "#/math", label: "Sharpen your mental math" };
  }

  function viewHome() {
    const li = levelInfo();
    const lessonsDone = Object.keys(S.lessons).length;
    const casesDone = D.cases.filter(function (c) { return S.cases[c.id] && S.cases[c.id].done; }).length;
    const dailyDone = !!S.daily[today()];
    const nu = nextUp();
    const hello = S.name ? "Welcome back, " + esc(S.name) + "." : "Crack the case. Ace the fit interview.";
    const badgeCount = Object.keys(S.badges).length;

    main.innerHTML =
      '<section class="hero">' +
        '<div class="hero-main">' +
          "<h1>" + hello + "</h1>" +
          "<p>Learn the frameworks consultants actually use, solve interactive case studies with real exhibits, practise behavioural answers with the STAR method, and level up from Intern to Partner. Everything runs offline on your device.</p>" +
          '<div class="hero-actions">' +
            '<a class="btn light" href="' + nu.href + '">▶ ' + esc(nu.label) + "</a>" +
            '<a class="btn outline-light" href="#/daily">' + (dailyDone ? "✅ Daily challenge done" : "🎯 Daily challenge") + "</a>" +
          "</div>" +
        "</div>" +
        '<div class="card level-card">' +
          '<div class="muted">Current level</div>' +
          '<div class="level-name">🎓 ' + esc(li.cur.name) + "</div>" +
          bar(li.pct) +
          '<div class="muted" style="font-size:.9rem">' + (li.next ? fmt(li.toNext) + " XP to " + esc(li.next.name) : "Top of the pyramid. 👑") + "</div>" +
          '<div class="stat-row">' +
            '<div class="stat"><b>' + (streakAlive() ? S.streak.count : 0) + "</b><span>day streak</span></div>" +
            '<div class="stat"><b>' + fmt(S.xp) + "</b><span>XP</span></div>" +
            '<div class="stat"><b>' + badgeCount + "/" + D.badges.length + "</b><span>badges</span></div>" +
          "</div>" +
        "</div>" +
      "</section>" +

      '<section class="section"><h2>Your training path</h2><div class="grid grid-3">' +
        moduleCard("#/learn", "🗂️", "Frameworks", "MECE, issue trees, profitability, market entry, M&A, pricing and more.", lessonsDone, D.frameworks.length, "lessons") +
        moduleCard("#/cases", "💼", "Case studies", "Interactive cases: clarify, structure, crunch exhibits, recommend.", casesDone, D.cases.length, "cases") +
        moduleCard("#/behavioral", "🎤", "Behavioural", "STAR method, the classic questions, a timer and your story bank.", Math.min(S.stories.length, 8), 8, "stories (aim for 8)") +
        moduleCard("#/mece", "🧩", "MECE Practice", "Structure a case prompt against the clock. Scored on logic, overlaps, gaps and prioritisation.", D.mece.prompts.filter(function (p) { return S.mece.best[p.id + ":free"] != null || S.mece.best[p.id + ":builder"] != null; }).length, D.mece.prompts.length, "prompts practised") +
        moduleCard("#/math", "🧮", "Mental math", "Timed sprints (you set the clock) on percentages, zeros, growth and breakeven.", Math.min(S.math.best, 20), 20, "best score (target 20)") +
        moduleCard("#/daily", "🎯", "Daily challenge", "5 fresh questions every day. Keep the streak alive.", dailyDone ? 1 : 0, 1, "done today") +
        moduleCard("#/profile", "🏅", "Badges & profile", "Track achievements, back up or restore progress.", badgeCount, D.badges.length, "badges") +
      "</div></section>" +

      '<section class="section"><h2>How a case interview flows</h2><div class="grid grid-3">' +
        flowCard(1, "Listen & clarify", "Take notes, play back the problem, confirm the objective, and ask 2–3 sharp clarifying questions.") +
        flowCard(2, "Structure", "Ask for a minute, then present a MECE framework tailored to the case — not a memorised template.") +
        flowCard(3, "Hypothesise & prioritise", "Say where you'd look first and why. Lead the case.") +
        flowCard(4, "Analyse exhibits & math", "Read titles and units, compute out loud, and always state the 'so what'.") +
        flowCard(5, "Brainstorm", "Generate structured, creative ideas — grouped into buckets, not a random list.") +
        flowCard(6, "Synthesise", "Answer first: recommendation, 3 reasons, risks, next steps — in under a minute.") +
      "</div></section>";
  }
  function moduleCard(href, icon, title, desc, done, total, unit) {
    return '<a class="card" href="' + href + '"><div class="card-icon">' + icon + "</div><h3>" + title + '</h3><p class="meta">' + desc + "</p>" +
      bar((done / total) * 100, "small") + '<div class="meta" style="margin-top:6px">' + done + " / " + total + " " + unit + "</div></a>";
  }
  function flowCard(n, t, d) {
    return '<div class="card"><span class="tag brand">Step ' + n + "</span><h3 style=\"margin-top:8px\">" + t + '</h3><p class="meta" style="margin:0">' + d + "</p></div>";
  }

  /* ---------------------------- Frameworks --------------------------- */
  function viewLearn() {
    function cards(group) {
      return D.frameworks.filter(function (f) { return f.group === group; }).map(function (f) {
        const done = !!S.lessons[f.id];
        return '<a class="card" href="#/framework/' + f.id + '"><div class="card-icon">' + f.icon + "</div><h3>" + esc(f.name) +
          (done ? ' <span class="done-mark">✔</span>' : "") + '</h3><p class="meta">' + esc(f.tagline) + '</p><div class="tags">' +
          (done ? '<span class="tag good">Completed</span>' : '<span class="tag gold">+60 XP available</span>') + "</div></a>";
      }).join("");
    }
    main.innerHTML =
      '<div class="page-head"><h1>Frameworks</h1><p>Frameworks are thinking tools, not scripts. Learn the logic behind each one so you can tailor it to any case. Each lesson ends with a 3-question check — finish it to earn XP.</p></div>' +
      '<section><h2>1 · Core thinking</h2><div class="grid grid-3">' + cards("core") + "</div></section>" +
      '<section class="section"><h2>2 · Case frameworks</h2><div class="grid grid-3">' + cards("case") + "</div></section>";
  }

  function treeHTML(node) {
    let h = '<li><span class="node">' + esc(node.t) + "</span>";
    if (node.c && node.c.length) h += "<ul>" + node.c.map(treeHTML).join("") + "</ul>";
    return h + "</li>";
  }

  function viewFramework(id) {
    const idx = D.frameworks.findIndex(function (f) { return f.id === id; });
    if (idx < 0) return viewNotFound();
    const f = D.frameworks[idx];
    const prev = D.frameworks[idx - 1];
    const next = D.frameworks[idx + 1];

    function quizHTML() {
      return f.quiz.map(function (q, qi) {
        const a = S.quiz[f.id + ":" + qi];
        const opts = order(q.options.length, seeded(f.id + ":" + qi)).map(function (oi, pos) {
          const o = q.options[oi];
          let cls = "";
          if (a) { if (oi === q.answer) cls = "correct"; else if (oi === a.choice) cls = "wrong"; }
          return '<button class="opt ' + cls + '" data-q="' + qi + '" data-o="' + oi + '"' + (a ? " disabled" : "") + '><span class="key">' + letter(pos) + "</span><span>" + esc(o) + "</span></button>";
        }).join("");
        const fb = a ? '<div class="feedback ' + (a.correct ? "good" : "bad") + '">' + (a.correct ? "✅ Correct. " : "❌ Not quite. ") + esc(q.explain) + "</div>" : "";
        return '<div class="q-block"><div class="q-title">' + (qi + 1) + ". " + esc(q.q) + '</div><div class="options">' + opts + "</div>" + fb + "</div>";
      }).join("");
    }

    function render() {
      const answered = f.quiz.filter(function (_, qi) { return S.quiz[f.id + ":" + qi]; }).length;
      const correct = f.quiz.filter(function (_, qi) { const a = S.quiz[f.id + ":" + qi]; return a && a.correct; }).length;
      const done = !!S.lessons[f.id];
      main.innerHTML =
        '<a class="crumb" href="#/learn">← All frameworks</a>' +
        '<div class="page-head"><h1>' + f.icon + " " + esc(f.name) + "</h1><p>" + esc(f.tagline) + "</p></div>" +
        '<div class="lesson"><div>' +
          '<div class="card"><p style="margin:0">' + esc(f.intro) + "</p></div>" +
          '<div class="card section" style="margin-top:16px"><h3>The structure</h3><p class="meta">Example issue tree — adapt the branches to each case.</p><ul class="tree">' + treeHTML(f.tree) + "</ul></div>" +
          '<div class="grid grid-2" style="margin-top:16px">' +
            '<div class="card"><h3>Key points</h3><ul class="list-check">' + f.keyPoints.map(function (k) { return "<li>" + esc(k) + "</li>"; }).join("") + "</ul></div>" +
            '<div class="card"><h3>Common pitfalls</h3><ul class="list-check list-x">' + f.pitfalls.map(function (k) { return "<li>" + esc(k) + "</li>"; }).join("") + "</ul></div>" +
          "</div>" +
          '<div class="card" style="margin-top:16px" id="quiz"><h3>Knowledge check</h3><p class="meta">+10 XP per correct answer · +30 XP for finishing the lesson</p>' + quizHTML() + "</div>" +
          '<div class="btn-row">' +
            (prev ? '<a class="btn ghost" href="#/framework/' + prev.id + '">← ' + esc(prev.name) + "</a>" : "") +
            (next ? '<a class="btn" href="#/framework/' + next.id + '">' + esc(next.name) + " →</a>" : '<a class="btn" href="#/cases">Apply it in a case →</a>') +
          "</div>" +
        "</div>" +
        '<aside class="card"><h3>Lesson progress</h3>' + bar((answered / f.quiz.length) * 100) +
          '<p class="meta" style="margin-top:8px">' + answered + "/" + f.quiz.length + " questions answered · " + correct + " correct</p>" +
          (done ? '<p class="done-mark">✔ Lesson complete</p>' : '<p class="meta">Answer all questions to complete the lesson.</p>') +
          '<hr style="border:none;border-top:1px solid var(--border);margin:14px 0">' +
          '<h3>Interview tip</h3><p class="meta" style="margin:0">Never recite a framework by name. Say: "To figure out X, I\'d look at three things…" and tailor each branch to the client.</p>' +
        "</aside></div>";

      main.querySelectorAll("#quiz .opt").forEach(function (b) {
        b.addEventListener("click", function () {
          const qi = +b.dataset.q, oi = +b.dataset.o;
          const k = f.id + ":" + qi;
          if (S.quiz[k]) return;
          const ok = oi === f.quiz[qi].answer;
          S.quiz[k] = { choice: oi, correct: ok };
          save();
          if (ok) addXP(10, "Correct");
          const allAnswered = f.quiz.every(function (_, i) { return S.quiz[f.id + ":" + i]; });
          if (allAnswered && !S.lessons[f.id]) {
            S.lessons[f.id] = today();
            addXP(30, "Lesson complete");
          }
          const y = window.scrollY;
          render();
          window.scrollTo(0, y);
        });
      });
    }
    render();
  }

  /* ------------------------------ Cases ------------------------------ */
  function stars(n) { return '<span class="difficulty" title="Difficulty ' + n + '/3">' + "★".repeat(n) + "☆".repeat(3 - n) + "</span>"; }

  function viewCases() {
    main.innerHTML =
      '<div class="page-head"><h1>Case studies</h1><p>Each case walks you through a real interview flow: clarify, structure, analyse exhibits, do the math, brainstorm and synthesise. First-time completion earns XP for every step you get right first time, plus a completion bonus.</p></div>' +
      '<div class="grid grid-3">' + D.cases.map(function (c) {
        const r = S.cases[c.id];
        return '<a class="card" href="#/case/' + c.id + '"><div class="card-icon">' + c.icon + "</div><h3>" + esc(c.title) + (r && r.done ? ' <span class="done-mark">✔</span>' : "") + "</h3>" +
          '<p class="meta">' + esc(c.client) + "</p>" +
          '<div class="tags"><span class="tag brand">' + esc(c.type) + "</span><span class=\"tag\">" + c.steps.length + " steps</span>" +
          (r && r.done ? '<span class="tag good">Best ' + Math.round(r.best * 100) + "%</span>" : '<span class="tag gold">+' + (c.steps.length * 15 + 50) + " XP</span>") +
          (r && r.perfect ? '<span class="tag gold">🎯 Flawless</span>' : "") + "</div>" +
          '<div style="margin-top:10px">' + stars(c.difficulty) + "</div></a>";
      }).join("") + "</div>" +
      '<section class="section card"><h3>Tips for case math</h3><ul class="list-check">' +
        "<li>Write units next to every number and round aggressively (52 weeks ≈ 50).</li>" +
        "<li>Use scientific shorthand for zeros: 3k × 400 = 1.2M (3 × 4 = 12, then add 5 zeros).</li>" +
        "<li>Percentages: 15% = 10% + 5% (half of 10%).</li>" +
        "<li>After every calculation say the 'so what' — what does the number mean for the client?</li>" +
        "<li>In this app you can type answers like <b>1.2m</b>, <b>450k</b> or <b>32.5</b>.</li>" +
      "</ul></section>";
  }

  function exhibitHTML(ex) {
    if (!ex) return "";
    return '<div class="exhibit"><div class="exhibit-cap">📊 ' + esc(ex.caption) + '</div><table class="tbl"><thead><tr>' +
      ex.headers.map(function (h) { return "<th>" + esc(h) + "</th>"; }).join("") + "</tr></thead><tbody>" +
      ex.rows.map(function (r) { return "<tr>" + r.map(function (c) { return "<td>" + esc(c) + "</td>"; }).join("") + "</tr>"; }).join("") +
      "</tbody></table></div>";
  }

  function viewCase(id) {
    const c = D.cases.find(function (x) { return x.id === id; });
    if (!c) return viewNotFound();
    const firstTime = !(S.cases[id] && S.cases[id].done);
    const run = { i: 0, correct: 0, mistakes: 0, xp: 0, state: [] };

    function award(n, why) { if (firstTime) { run.xp += n; addXP(n, why); } }

    function header() {
      return '<a class="crumb" href="#/cases">← All cases</a>' +
        '<div class="case-head"><div><h1>' + c.icon + " " + esc(c.title) + '</h1><div class="tags"><span class="tag brand">' + esc(c.type) + '</span><span class="tag">' + esc(c.client) + "</span>" +
        (firstTime ? "" : '<span class="tag">Replay · no XP</span>') + "</div></div><div>" + stars(c.difficulty) + "</div></div>" +
        '<div class="prompt" style="margin-top:14px"><b>Case prompt.</b> ' + esc(c.prompt) + "</div>";
    }
    function stepper() {
      return '<div class="stepper" aria-hidden="true">' + c.steps.map(function (_, i) {
        return '<span class="' + (i < run.i ? "done" : i === run.i ? "now" : "") + '"></span>';
      }).join("") + "</div>";
    }

    function render() {
      const step = c.steps[run.i];
      const st = run.state[run.i] || (run.state[run.i] = { answered: false, choice: null, selected: [], attempts: 0, value: "", firstOk: false, order: step.options ? order(step.options.length) : [] });
      let body = "";
      let fb = "";

      if (step.kind === "mcq") {
        body = '<div class="options">' + st.order.map(function (oi, pos) {
          const o = step.options[oi];
          let cls = "";
          if (st.answered) { if (o.correct) cls = "correct"; else if (oi === st.choice) cls = "wrong"; }
          return '<button class="opt ' + cls + '" data-o="' + oi + '"' + (st.answered ? " disabled" : "") + '><span class="key">' + letter(pos) + "</span><span>" + esc(o.text) + "</span></button>";
        }).join("") + "</div>";
        if (st.answered) {
          const ch = step.options[st.choice];
          fb = '<div class="feedback ' + (ch.correct ? "good" : "bad") + '">' + (ch.correct ? "✅ " : "❌ ") + esc(ch.feedback) + "</div>";
          if (!ch.correct) {
            const best = step.options.find(function (o) { return o.correct; });
            fb += '<div class="feedback info"><b>Why the best answer works:</b> ' + esc(best.feedback) + "</div>";
          }
          if (step.reveal) fb += '<div class="interviewer">🗣️ ' + esc(step.reveal) + "</div>";
        }
      } else if (step.kind === "multi") {
        body = '<div class="options">' + st.order.map(function (oi, pos) {
          const o = step.options[oi];
          const sel = st.selected.indexOf(oi) >= 0;
          let cls = sel ? "selected" : "";
          if (st.answered) cls = o.correct && sel ? "correct" : !o.correct && sel ? "wrong" : o.correct ? "missed" : "";
          return '<button class="opt ' + cls + '" data-o="' + oi + '" aria-pressed="' + sel + '"' + (st.answered ? " disabled" : "") + '><span class="key">' + (sel ? "✓" : letter(pos)) + "</span><span>" + esc(o.text) + "</span></button>";
        }).join("") + "</div>";
        if (!st.answered) body += '<div class="btn-row"><button class="btn" id="submitMulti"' + (st.selected.length ? "" : " disabled") + ">Submit selection</button></div>";
        else fb = '<div class="feedback ' + (st.firstOk ? "good" : "bad") + '">' + (st.firstOk ? "✅ Spot on. " : "❌ Not quite — dashed outlines show levers you missed. ") + esc(step.explain) + "</div>";
      } else if (step.kind === "math") {
        body = '<div class="input-row"><input class="input num" id="mathIn" inputmode="decimal" autocomplete="off" placeholder="Your answer" value="' + esc(st.value) + '"' + (st.answered ? " disabled" : "") + '><span class="muted">' + esc(step.unit || "") + "</span>" +
          (st.answered ? "" : '<button class="btn" id="submitMath">Check</button>' + (st.attempts ? '<button class="btn ghost" id="giveUp">Show answer</button>' : "")) + "</div>";
        if (st.answered) {
          fb = '<div class="feedback ' + (st.solved ? "good" : "bad") + '">' + (st.solved ? "✅ Correct! " : "❌ The answer is " + fmt(step.answer) + " " + esc(step.unit || "") + ". ") + esc(step.explain) + "</div>";
        } else if (st.attempts) {
          fb = '<div class="feedback bad">Not quite — check your zeros and units, then try once more.</div>';
        }
      }

      const last = run.i === c.steps.length - 1;
      main.innerHTML = header() + stepper() +
        '<div class="card"><span class="tag brand">Step ' + (run.i + 1) + " of " + c.steps.length + "</span> <b>" + esc(step.title) + "</b>" +
        exhibitHTML(step.exhibit) +
        '<div class="q-title" style="margin-top:12px">' + esc(step.question) + "</div>" + body + fb +
        (st.answered ? '<div class="btn-row"><button class="btn" id="nextStep">' + (last ? "Finish case 🏁" : "Next step →") + "</button></div>" : "") +
        "</div>";

      bind(step, st);
    }

    function settle(st, ok) {
      st.answered = true;
      st.firstOk = ok;
      if (ok) { run.correct++; award(15, "Step nailed"); } else { run.mistakes++; }
    }

    function bind(step, st) {
      if (step.kind === "mcq") {
        main.querySelectorAll(".opt").forEach(function (b) {
          b.addEventListener("click", function () {
            if (st.answered) return;
            st.choice = +b.dataset.o;
            settle(st, !!step.options[st.choice].correct);
            render();
          });
        });
      } else if (step.kind === "multi") {
        main.querySelectorAll(".opt").forEach(function (b) {
          b.addEventListener("click", function () {
            if (st.answered) return;
            const oi = +b.dataset.o;
            const at = st.selected.indexOf(oi);
            if (at >= 0) st.selected.splice(at, 1); else st.selected.push(oi);
            render();
          });
        });
        const sm = document.getElementById("submitMulti");
        if (sm) sm.addEventListener("click", function () {
          const ok = step.options.every(function (o, oi) { return !!o.correct === (st.selected.indexOf(oi) >= 0); });
          settle(st, ok);
          render();
        });
      } else if (step.kind === "math") {
        const inp = document.getElementById("mathIn");
        const check = function () {
          st.value = inp.value;
          const v = parseNum(inp.value);
          if (isNaN(v)) { toast("Enter a number, e.g. 32.5 or 1.2m"); return; }
          st.attempts++;
          // "600t" for an answer already expressed in "Rp T" means 600, not 600 trillion.
          const bare = parseNum(inp.value.replace(/[kmbt]\s*$/i, ""));
          const near = function (x) { return Math.abs(x - step.answer) <= (step.tolerance || 0); };
          if (near(v) || near(bare)) {
            st.solved = true;
            if (st.attempts === 1) settle(st, true);
            else { st.answered = true; run.mistakes++; award(5, "Got there"); }
          } else if (st.attempts >= 2) {
            settle(st, false);
          }
          render();
        };
        if (!st.answered) {
          inp.addEventListener("keydown", function (e) { if (e.key === "Enter") check(); });
          document.getElementById("submitMath").addEventListener("click", check);
          const gu = document.getElementById("giveUp");
          if (gu) gu.addEventListener("click", function () { settle(st, false); render(); });
          inp.focus();
        }
      }
      const nx = document.getElementById("nextStep");
      if (nx) nx.addEventListener("click", function () {
        if (run.i < c.steps.length - 1) { run.i++; render(); window.scrollTo(0, 0); }
        else finish();
      });
    }

    function finish() {
      const score = run.correct / c.steps.length;
      const prev = S.cases[id] || {};
      const perfect = run.mistakes === 0;
      S.cases[id] = {
        done: true,
        best: Math.max(prev.best || 0, score),
        perfect: !!prev.perfect || perfect,
        plays: (prev.plays || 0) + 1
      };
      save();
      if (firstTime) award(50, "Case complete");
      else touchStreak();
      checkBadges();
      if (perfect) confetti();
      const nextCase = D.cases.find(function (x) { return !(S.cases[x.id] && S.cases[x.id].done); });
      const grade = score === 1 ? ["🏆", "Partner-ready!"] : score >= 0.7 ? ["💪", "Strong performance"] : score >= 0.4 ? ["📈", "Getting there"] : ["🧭", "Keep practising"];
      main.innerHTML = header() + stepper().replace(/class="(now|)"/g, 'class="done"') +
        '<div class="card center"><div class="big-emoji">' + grade[0] + "</div><h2>" + grade[1] + '</h2><div class="kpi">' + Math.round(score * 100) + '%</div><p class="muted">' +
        run.correct + " of " + c.steps.length + " steps right first time" + (firstTime ? " · +" + run.xp + " XP earned" : " · replay (no XP)") + "</p></div>" +
        '<div class="card" style="margin-top:16px"><h3>Model synthesis</h3><p style="margin:0">' + esc(c.modelAnswer) + "</p></div>" +
        '<div class="btn-row"><a class="btn ghost" href="#/case/' + c.id + '" id="replay">↻ Replay</a>' +
        (nextCase ? '<a class="btn" href="#/case/' + nextCase.id + '">Next case: ' + esc(nextCase.title) + " →</a>" : '<a class="btn" href="#/cases">All cases</a>') + "</div>";
      document.getElementById("replay").addEventListener("click", function (e) { e.preventDefault(); viewCase(id); });
      renderHud();
    }

    render();
  }

  /* --------------------------- Behavioural --------------------------- */
  let behavFilter = "all";

  function viewBehavioral() {
    const B = D.behavioral;
    function list() {
      return B.questions.filter(function (q) { return behavFilter === "all" || q.cat === behavFilter; }).map(function (q) {
        const n = S.stories.filter(function (s) { return s.qid === q.id; }).length;
        const cat = B.categories.find(function (c) { return c.id === q.cat; });
        return '<a class="card" href="#/practice/' + q.id + '"><span class="tag brand">' + esc(cat.name) + "</span>" +
          (S.practiced[q.id] ? ' <span class="tag good">✔ Practised</span>' : ' <span class="tag gold">+XP</span>') +
          '<h3 style="margin-top:8px">' + esc(q.q) + '</h3><p class="meta" style="margin:0">Testing: ' + esc(q.tests) + "</p>" +
          (n ? '<p class="meta" style="margin:6px 0 0">📚 ' + n + " saved " + (n === 1 ? "story" : "stories") + "</p>" : "") + "</a>";
      }).join("");
    }
    function render() {
      main.innerHTML =
        '<div class="page-head"><h1>Behavioural & fit interview</h1><p>Half of every consulting interview is about you. Firms want evidence of leadership, drive, teamwork and impact — told as crisp stories. Use the STAR method, practise out loud with the timer, and build a story bank you can reuse.</p></div>' +
        '<div class="star-grid">' + B.star.map(function (s) {
          return '<div class="star-card"><div class="star-letter">' + s.k + "</div><h3>" + s.name + '</h3><p class="meta" style="margin:0">' + esc(s.tip) + "</p></div>";
        }).join("") + "</div>" +
        '<section class="section grid grid-2">' + B.tips.map(function (t) {
          return '<div class="card"><h3>💡 ' + esc(t.t) + '</h3><p class="meta" style="margin:0">' + esc(t.d) + "</p></div>";
        }).join("") + "</section>" +
        '<section class="section"><h2>Question bank</h2><div class="filter-row">' +
          ['<button class="chip' + (behavFilter === "all" ? " active" : "") + '" data-f="all">All</button>'].concat(B.categories.map(function (c) {
            return '<button class="chip' + (behavFilter === c.id ? " active" : "") + '" data-f="' + c.id + '">' + esc(c.name) + "</button>";
          })).join("") +
        '</div><div class="grid grid-2">' + list() + "</div></section>" +
        storyBankHTML(null);
      main.querySelectorAll(".chip").forEach(function (b) {
        b.addEventListener("click", function () { behavFilter = b.dataset.f; render(); });
      });
      bindStoryDelete(render);
    }
    render();
  }

  function storyBankHTML(qid) {
    const items = S.stories.filter(function (s) { return !qid || s.qid === qid; }).slice().reverse();
    const title = qid ? "Your saved answers to this question" : "📚 Your story bank (" + S.stories.length + ")";
    if (!items.length) {
      return '<section class="section card"><h3>' + title + '</h3><p class="meta" style="margin:0">' + (qid ? "Nothing saved yet — write your STAR answer above and save it." : "Practise a question and save your answer — your stories show up here. Aim for 6–8 strong stories.") + "</p></section>";
    }
    return '<section class="section card"><h3>' + title + "</h3>" + items.map(function (s) {
      const q = D.behavioral.questions.find(function (x) { return x.id === s.qid; });
      return '<div class="story"><div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap"><b>' + esc(q ? q.q : s.qid) + '</b><span class="meta">' + esc(s.date) + " · self-score " + s.score + "/" + D.behavioral.rubric.length + "</span></div>" +
        ["s", "t", "a", "r"].map(function (k, i) {
          return s[k] ? '<p style="margin:6px 0"><span class="story-label">' + "STAR"[i] + ":</span> " + esc(s[k]) + "</p>" : "";
        }).join("") +
        '<button class="btn ghost sm" data-del="' + esc(s.id) + '">Delete</button></div>';
    }).join("") + "</section>";
  }
  function bindStoryDelete(rerender) {
    main.querySelectorAll("[data-del]").forEach(function (b) {
      b.addEventListener("click", function () {
        if (!confirm("Delete this story?")) return;
        S.stories = S.stories.filter(function (s) { return s.id !== b.dataset.del; });
        save();
        rerender();
      });
    });
  }

  function viewPractice(qid) {
    const B = D.behavioral;
    const q = B.questions.find(function (x) { return x.id === qid; });
    if (!q) return viewNotFound();
    const draft = S.drafts[qid] || { s: "", t: "", a: "", r: "" };
    const timer = { start: null, acc: 0, iv: null };

    function elapsed() { return timer.acc + (timer.start ? (Date.now() - timer.start) / 1000 : 0); }
    function paintTimer() {
      const el = document.getElementById("timer");
      if (!el) return;
      const t = elapsed();
      el.textContent = Math.floor(t / 60) + ":" + pad(Math.floor(t % 60));
      el.className = "timer" + (t > 120 ? " over" : t > 105 ? " warn" : "");
    }
    onLeave(function () { clearInterval(timer.iv); });

    function render() {
      main.innerHTML =
        '<a class="crumb" href="#/behavioral">← Question bank</a>' +
        '<div class="page-head"><h1>' + esc(q.q) + '</h1><p><b>What they\'re testing:</b> ' + esc(q.tests) + "</p></div>" +
        '<div class="lesson"><div>' +
          '<div class="card"><h3>How to nail it</h3><ul class="list-check">' + q.tips.map(function (t) { return "<li>" + esc(t) + "</li>"; }).join("") + "</ul>" +
          (q.sample ? '<details class="sample"><summary>See a sample answer</summary><p style="margin:10px 0 0">' + esc(q.sample) + "</p></details>" : "") + "</div>" +
          '<div class="card" style="margin-top:16px"><h3>Draft your STAR answer</h3><p class="meta">Drafts save automatically on this device.</p>' +
          B.star.map(function (s) {
            const k = s.k.toLowerCase();
            return '<label style="display:block;margin-top:12px"><b>' + s.k + " — " + s.name + '</b> <span class="meta">' + esc(s.tip) + '</span><textarea class="input" data-k="' + k + '" rows="' + (k === "a" ? 5 : 3) + '">' + esc(draft[k]) + "</textarea></label>";
          }).join("") + "</div>" +
          '<div class="card" style="margin-top:16px"><h3>Self-assessment</h3><p class="meta">Say your answer out loud with the timer, then tick what you honestly achieved.</p>' +
          B.rubric.map(function (r, i) { return '<label class="check"><input type="checkbox" data-r="' + i + '"><span>' + esc(r) + "</span></label>"; }).join("") +
          '<div class="btn-row"><button class="btn accent" id="saveStory">💾 Save to story bank</button></div>' +
          '<p class="meta" style="margin:8px 0 0">' + (S.practiced[qid] ? "You've already earned XP for this question — saving again adds another version." : "First save earns 10 XP + 3 XP per rubric item ticked.") + "</p></div>" +
        "</div>" +
        '<aside class="card center"><h3>Practice timer</h3><div class="timer" id="timer">0:00</div><p class="meta">Target: under 2:00</p>' +
          '<div class="btn-row" style="justify-content:center"><button class="btn" id="tStart">▶ Start</button><button class="btn ghost" id="tReset">↺ Reset</button></div>' +
          '<hr style="border:none;border-top:1px solid var(--border);margin:14px 0"><p class="meta" style="margin:0;text-align:left">Expect follow-ups: "What did you personally do?", "What would you do differently?", "How did the other person react?"</p></aside>' +
        "</div>" + storyBankHTML(qid);

      paintTimer();
      const startBtn = document.getElementById("tStart");
      startBtn.textContent = timer.start ? "⏸ Pause" : "▶ Start";
      startBtn.addEventListener("click", function () {
        if (timer.start) { timer.acc = elapsed(); timer.start = null; clearInterval(timer.iv); startBtn.textContent = "▶ Start"; }
        else { timer.start = Date.now(); timer.iv = setInterval(paintTimer, 250); startBtn.textContent = "⏸ Pause"; }
      });
      document.getElementById("tReset").addEventListener("click", function () {
        clearInterval(timer.iv); timer.start = null; timer.acc = 0; startBtn.textContent = "▶ Start"; paintTimer();
      });

      let saveT = null;
      main.querySelectorAll("textarea[data-k]").forEach(function (ta) {
        ta.addEventListener("input", function () {
          draft[ta.dataset.k] = ta.value;
          clearTimeout(saveT);
          saveT = setTimeout(function () { S.drafts[qid] = draft; save(); }, 400);
        });
      });

      document.getElementById("saveStory").addEventListener("click", function () {
        const filled = ["s", "t", "a", "r"].filter(function (k) { return draft[k].trim(); }).length;
        if (filled < 3) { toast("Fill in at least 3 of the 4 STAR boxes first ✍️"); return; }
        const score = main.querySelectorAll("input[data-r]:checked").length;
        S.stories.push({ id: Date.now().toString(36), qid: qid, s: draft.s.trim(), t: draft.t.trim(), a: draft.a.trim(), r: draft.r.trim(), score: score, date: today() });
        delete S.drafts[qid];
        draft.s = draft.t = draft.a = draft.r = "";
        const first = !S.practiced[qid];
        S.practiced[qid] = true;
        save();
        if (first) addXP(10 + score * 3, "Story saved");
        else { touchStreak(); checkBadges(); toast("Story saved 📚"); }
        render();
      });
      bindStoryDelete(render);
    }
    render();
  }

  /* --------------------------- Mental math --------------------------- */
  function randInt(a, b) { return a + Math.floor(Math.random() * (b - a + 1)); }
  function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

  const generators = [
    { key: "pct", label: "% of", make: function () {
      const p = pick([5, 10, 15, 20, 25, 30, 40, 50, 60, 75]);
      const base = randInt(2, 40) * 20;
      return { q: p + "% of " + fmt(base), a: (p * base) / 100 };
    } },
    { key: "zeros", label: "× with zeros", make: function () {
      const a = randInt(2, 9) * Math.pow(10, randInt(1, 4));
      const b = randInt(2, 9) * Math.pow(10, randInt(1, 3));
      return { q: fmt(a) + " × " + fmt(b), a: a * b };
    } },
    { key: "divide", label: "Division", make: function () {
      const b = pick([4, 5, 6, 8, 12, 15, 20, 25, 40, 50, 60]);
      const ans = randInt(3, 60) * pick([1, 10, 100]);
      return { q: fmt(ans * b) + " ÷ " + b, a: ans };
    } },
    { key: "growth", label: "% change", make: function () {
      const from = pick([40, 50, 80, 100, 120, 200, 250, 400]);
      const g = pick([-50, -25, -20, -10, 10, 20, 25, 50, 75, 100]);
      const to = (from * (100 + g)) / 100;
      return { q: fmt(from) + " → " + fmt(to) + ": % change?", a: g, unit: "%" };
    } },
    { key: "breakeven", label: "Breakeven", make: function () {
      const m = pick([5, 10, 20, 25, 40, 50]);
      const units = randInt(2, 40) * 1000;
      return { q: "Fixed cost $" + fmt(m * units) + ", margin $" + m + "/unit → breakeven units?", a: units };
    } },
    { key: "margin", label: "Margin %", make: function () {
      const rev = pick([200, 400, 500, 800, 1000, 1200]);
      const pctv = pick([5, 10, 15, 20, 25, 30, 40]);
      return { q: "Revenue $" + fmt(rev) + "M, profit $" + fmt((rev * pctv) / 100) + "M → margin %?", a: pctv, unit: "%" };
    } }
  ];

  const TIME_PRESETS = [30, 60, 120, 180, 300, 0]; // 0 = untimed
  const MIN_TIME = 10, MAX_TIME = 1800;

  function fmtDuration(sec) {
    if (!sec) return "Untimed";
    if (sec < 60) return sec + " sec";
    return sec % 60 ? Math.floor(sec / 60) + " min " + (sec % 60) + " sec" : sec / 60 + " min";
  }
  function clock(sec) { sec = Math.max(0, Math.round(sec)); return Math.floor(sec / 60) + ":" + pad(sec % 60); }

  function viewMath() {
    if (typeof S.math.duration !== "number") S.math.duration = 60;
    if (!S.math.bests || typeof S.math.bests !== "object") S.math.bests = {};
    const enabledTypes = function () {
      const t = Array.isArray(S.math.types) ? S.math.types : [];
      const valid = generators.filter(function (g) { return t.indexOf(g.key) >= 0; });
      return valid.length ? valid : generators;
    };
    const game = { running: false, score: 0, wrong: 0, cur: null, log: [], iv: null, start: 0, end: 0, duration: 60 };
    onLeave(function () { clearInterval(game.iv); });

    function intro(result) {
      const d = S.math.duration;
      const types = enabledTypes();
      const best = d ? S.math.bests[d] || 0 : null;
      main.innerHTML =
        '<div class="page-head"><h1>Mental Math Arena</h1><p>Consulting interviews expect quick, accurate math without a calculator. Pick a time limit and question types, then answer as many as you can. Shortcuts accepted: <b>450k</b>, <b>1.2m</b>, <b>3b</b>.</p></div>' +
        '<div class="arena card">' +
          (result || '<div class="big-emoji">🧮</div><h2>Ready?</h2>') +
          '<div class="arena-stats"><div><div class="kpi">' + (d ? best : "—") + '</div><div class="meta">Best (' + esc(fmtDuration(d)) + ')</div></div><div><div class="kpi">' + S.math.runs + '</div><div class="meta">Sprints</div></div></div>' +
          '<div class="btn-row" style="justify-content:center"><button class="btn" id="go">▶ Start ' + (d ? esc(fmtDuration(d)) + " sprint" : "untimed practice") + "</button></div>" +
          '<p class="meta" style="margin-top:10px">' + (d ? "+2 XP per correct answer · badges at 10 and 20 correct in a sprint of 1 minute or less" : "Untimed practice: +1 XP per correct answer, no badges. End whenever you like.") + "</p>" +
        "</div>" +
        '<section class="section card"><h3>⏱️ Time limit</h3><div class="filter-row">' +
          TIME_PRESETS.map(function (t) {
            return '<button class="chip' + (d === t ? " active" : "") + '" data-time="' + t + '">' + esc(fmtDuration(t)) + "</button>";
          }).join("") +
        '</div><div class="input-row"><label class="meta" for="customTime">Custom (seconds)</label>' +
          '<input class="input" id="customTime" type="number" min="' + MIN_TIME + '" max="' + MAX_TIME + '" step="5" style="width:120px" placeholder="e.g. 90" value="' + (d && TIME_PRESETS.indexOf(d) < 0 ? d : "") + '">' +
          '<button class="btn sm ghost" id="setTime">Set</button></div>' +
          '<h3 style="margin-top:18px">🔢 Question types</h3><div class="filter-row">' +
          generators.map(function (g) {
            const on = types.indexOf(g) >= 0;
            return '<button class="chip' + (on ? " active" : "") + '" data-type="' + g.key + '" aria-pressed="' + on + '">' + esc(g.label) + "</button>";
          }).join("") +
        '</div><p class="meta" style="margin:0">Your settings are remembered. Best scores are tracked separately for each time limit.</p></section>' +
        '<section class="section grid grid-2">' +
          '<div class="card"><h3>Zero management</h3><p class="meta" style="margin:0">Split numbers into digits × powers of ten: 3,000 × 400 = (3 × 4) × 10⁵ = 1.2M. Count zeros before you speak.</p></div>' +
          '<div class="card"><h3>Percent tricks</h3><p class="meta" style="margin:0">x% of y = y% of x (8% of 50 = 50% of 8 = 4). 15% = 10% + 5%. Breakeven churn after a price rise = 1 − old/new.</p></div>' +
        "</section>";

      document.getElementById("go").addEventListener("click", start);
      main.querySelectorAll("[data-time]").forEach(function (b) {
        b.addEventListener("click", function () { S.math.duration = +b.dataset.time; save(); intro(result); });
      });
      const setCustom = function () {
        const v = Math.round(+document.getElementById("customTime").value);
        if (!v || v < MIN_TIME || v > MAX_TIME) { toast("Enter " + MIN_TIME + "–" + MAX_TIME + " seconds"); return; }
        S.math.duration = v; save(); intro(result);
      };
      document.getElementById("setTime").addEventListener("click", setCustom);
      document.getElementById("customTime").addEventListener("keydown", function (e) { if (e.key === "Enter") setCustom(); });
      main.querySelectorAll("[data-type]").forEach(function (b) {
        b.addEventListener("click", function () {
          const cur = enabledTypes().map(function (g) { return g.key; });
          const k = b.dataset.type;
          const at = cur.indexOf(k);
          if (at >= 0) {
            if (cur.length === 1) { toast("Keep at least one question type"); return; }
            cur.splice(at, 1);
          } else cur.push(k);
          S.math.types = cur.length === generators.length ? null : cur;
          save(); intro(result);
        });
      });
    }

    function nextQ() { game.cur = pick(enabledTypes()).make(); }

    function start() {
      game.running = true; game.score = 0; game.wrong = 0; game.log = [];
      game.duration = S.math.duration;
      game.start = Date.now();
      game.end = game.start + game.duration * 1000;
      nextQ();
      main.innerHTML =
        '<div class="arena card" id="arena">' +
          '<div class="arena-stats"><div><div class="kpi" id="left">' + (game.duration ? clock(game.duration) : "0:00") + '</div><div class="meta">' + (game.duration ? "time left" : "elapsed") + '</div></div><div><div class="kpi" id="score">0</div><div class="meta">correct</div></div></div>' +
          (game.duration ? bar(100) : "") +
          '<div class="arena-q" id="q"></div>' +
          '<div class="input-row" style="justify-content:center"><input class="input num" id="ans" inputmode="decimal" autocomplete="off" placeholder="Answer"><span class="muted" id="unit"></span></div>' +
          '<div class="btn-row" style="justify-content:center"><button class="btn" id="submit">Submit ⏎</button><button class="btn ghost" id="skip">Skip</button><button class="btn ghost" id="endRun">' + (game.duration ? "End early" : "Finish") + "</button></div>" +
        "</div>";
      const inp = document.getElementById("ans");
      paintQ();
      inp.focus();
      inp.addEventListener("keydown", function (e) { if (e.key === "Enter") submit(); });
      document.getElementById("submit").addEventListener("click", submit);
      document.getElementById("skip").addEventListener("click", function () {
        game.log.push({ q: game.cur.q, a: game.cur.a, you: "—", ok: false });
        nextQ(); paintQ(); inp.focus();
      });
      document.getElementById("endRun").addEventListener("click", stop);
      game.iv = setInterval(tick, 200);
    }

    function paintQ() {
      document.getElementById("q").textContent = game.cur.q;
      document.getElementById("unit").textContent = game.cur.unit || "";
      document.getElementById("ans").value = "";
    }

    function submit() {
      if (!game.running) return;
      const inp = document.getElementById("ans");
      const v = parseNum(inp.value);
      if (isNaN(v)) return;
      const a = game.cur.a;
      const ok = Math.abs(v - a) <= Math.max(Math.abs(a) * 0.01, 1e-9);
      game.log.push({ q: game.cur.q, a: a, you: inp.value, ok: ok });
      if (ok) game.score++; else game.wrong++;
      document.getElementById("score").textContent = game.score;
      const arena = document.getElementById("arena");
      arena.classList.remove("flash-good", "flash-bad");
      void arena.offsetWidth;
      arena.classList.add(ok ? "flash-good" : "flash-bad");
      nextQ(); paintQ(); inp.focus();
    }

    function tick() {
      const el = document.getElementById("left");
      if (!game.duration) {
        if (el) el.textContent = clock((Date.now() - game.start) / 1000);
        return;
      }
      const left = Math.max(0, (game.end - Date.now()) / 1000);
      if (el) el.textContent = clock(Math.ceil(left));
      const b = main.querySelector(".bar > i");
      if (b) b.style.width = (left / game.duration) * 100 + "%";
      if (left <= 0) stop();
    }

    function stop() {
      if (!game.running) return;
      clearInterval(game.iv);
      game.running = false;
      const d = game.duration;
      const timed = d > 0;
      const newBest = timed && game.score > (S.math.bests[d] || 0);
      if (timed) {
        S.math.bests[d] = Math.max(S.math.bests[d] || 0, game.score);
        if (d <= 60) S.math.best = Math.max(S.math.best, game.score); // badges stay comparable
      }
      S.math.runs++;
      S.math.total += game.score;
      save();
      if (game.score) addXP(game.score * (timed ? 2 : 1), timed ? "Math sprint" : "Math practice"); else { touchStreak(); checkBadges(); }
      if (newBest && game.score) { toast("🏅 New personal best (" + fmtDuration(d) + "): " + game.score); confetti(); }
      const acc = game.log.length ? Math.round((game.score / game.log.length) * 100) : 0;
      const secs = timed ? Math.min(d, (Date.now() - game.start) / 1000) : (Date.now() - game.start) / 1000;
      const pace = game.score ? (secs / game.score).toFixed(1) + " sec per correct answer" : "";
      const review = game.log.length ? '<table class="tbl" style="margin-top:14px"><thead><tr><th>Question</th><th>Answer</th><th>You</th></tr></thead><tbody>' +
        game.log.map(function (l) {
          return "<tr><td>" + esc(l.q) + "</td><td>" + fmt(l.a) + "</td><td>" + (l.ok ? "✅ " : "❌ ") + esc(l.you) + "</td></tr>";
        }).join("") + "</tbody></table>" : "";
      intro('<div class="big-emoji">' + (newBest ? "🏅" : "⏱️") + "</div><h2>" + game.score + ' correct</h2><p class="muted">' + esc(fmtDuration(d)) + " · accuracy " + acc + "%" + (pace ? " · " + pace : "") + (newBest ? " · new personal best!" : "") + '</p><div style="overflow-x:auto">' + review + "</div>");
      renderHud();
    }

    intro();
  }

  /* -------------------------- MECE Practice -------------------------- */
  const MECE_TIMES = [60, 90, 120, 180, 300, 0];
  const MECE_MAX_BRANCHES = 6;

  function meceState() {
    const m = S.mece;
    if (typeof m.duration !== "number") m.duration = 120;
    if (m.mode !== "free" && m.mode !== "builder") m.mode = "free";
    if (!m.best || typeof m.best !== "object") m.best = {};
    return m;
  }

  /* --- free-text scoring helpers --- */
  function normText(s) {
    return " " + String(s || "").toLowerCase().replace(/[’']/g, "'").replace(/[^a-z0-9&%.'\-\s]/g, " ").replace(/\s+/g, " ").trim() + " ";
  }
  function kwLen(text, kws) {
    let best = 0;
    for (let i = 0; i < kws.length; i++) {
      if (kws[i].length > best && text.indexOf(" " + kws[i].toLowerCase()) >= 0) best = kws[i].length;
    }
    return best;
  }
  function kwHit(text, kws) {
    for (let i = 0; i < kws.length; i++) {
      if (text.indexOf(" " + kws[i].toLowerCase()) >= 0) return kws[i];
    }
    return null;
  }
  const STOP = ["the", "a", "an", "of", "and", "or", "to", "in", "on", "for", "by", "vs", "per", "with", "our", "its", "is", "are", "dan", "di", "ke", "yang", "untuk"];
  function tokens(s) {
    return normText(s).trim().split(" ").filter(function (w) { return w.length > 1 && STOP.indexOf(w) < 0; });
  }
  function jaccard(a, b) {
    const A = tokens(a), B = tokens(b);
    if (!A.length || !B.length) return 0;
    const inter = A.filter(function (w) { return B.indexOf(w) >= 0; }).length;
    return inter / (A.length + B.length - inter);
  }

  function scoreFree(p, rawBranches, hypothesis, overtime) {
    const M = D.mece;
    const tops = rawBranches.map(function (b) {
      return {
        label: b.label.trim(),
        subs: b.subs.split(/\n/).map(function (s) { return s.replace(/^[\s\-–•*>]+|^\d+[.)]\s*/g, "").trim(); }).filter(Boolean)
      };
    }).filter(function (b) { return b.label || b.subs.length; });
    const fb = [];
    if (!tops.length) {
      return { total: 0, parts: [], feedback: [{ ok: false, t: "Your tree is empty. Add at least two top-level branches with sub-points." }], frame: p.frames[0].name, tops: tops };
    }
    const labelsN = tops.map(function (b) { return normText(b.label); });
    const subsN = tops.map(function (b) { return normText(b.subs.join(" | ")); });
    const allN = normText(tops.map(function (b) { return b.label + " | " + b.subs.join(" | "); }).join(" | "));

    // Evaluate every valid frame and keep the best fit.
    let best = null;
    p.frames.forEach(function (fr) {
      const req = fr.pillars.filter(function (x) { return !x.opt; });
      // Assign each top-level label to the single pillar it names most specifically (longest keyword),
      // so "Uniforms per student" isn't also counted as "Number of students".
      const owner = labelsN.map(function (ln) {
        let pick = null;
        fr.pillars.forEach(function (pl, pi) {
          const g = kwLen(ln, pl.kw), a = kwLen(ln, pl.alt || []);
          const score = g ? 1000 + g : a;
          if (score && (!pick || score > pick.score)) pick = { pi: pi, score: score, general: !!g };
        });
        return pick;
      });
      const res = fr.pillars.map(function (pl, pi) {
        const general = [], viaAlt = [];
        owner.forEach(function (o, i) {
          if (!o || o.pi !== pi) return;
          (o.general ? general : viaAlt).push(i);
        });
        const inSubs = subsN.some(function (sn) { return kwHit(sn, pl.kw) || kwHit(sn, pl.alt || []); });
        const level = general.length || viaAlt.length ? 1 : inSubs ? 0.5 : 0;
        const subsHit = pl.subs.filter(function (s) { return kwHit(allN, s.kw); });
        return { pl: pl, general: general, viaAlt: viaAlt, level: level, subsHit: subsHit };
      });
      const reqRes = res.filter(function (r) { return !r.pl.opt; });
      const coverage = 40 * reqRes.reduce(function (a, r) { return a + r.level; }, 0) / req.length;
      const totalSubs = reqRes.reduce(function (a, r) { return a + r.pl.subs.length; }, 0);
      const hitSubs = reqRes.reduce(function (a, r) { return a + r.subsHit.length; }, 0) +
        res.filter(function (r) { return r.pl.opt; }).reduce(function (a, r) { return a + r.subsHit.length; }, 0);
      const depth = 20 * Math.min(1, hitSubs / Math.max(1, Math.ceil(totalSubs * 0.6)));
      if (!best || coverage + depth > best.coverage + best.depth) best = { fr: fr, res: res, owner: owner, coverage: coverage, depth: depth, hitSubs: hitSubs, totalSubs: totalSubs };
    });

    // Coverage feedback
    fb.push({ ok: true, info: true, t: "Recognised structure: " + best.fr.name + (p.frames.length > 1 ? " (other valid structures were considered too)" : "") + "." });
    best.res.forEach(function (r) {
      if (r.level === 1) fb.push({ ok: true, t: "Covers " + r.pl.label + " as a top-level branch." });
      else if (r.level === 0.5) fb.push({ ok: false, half: true, t: r.pl.label + " only appears inside a sub-point. It deserves its own top-level branch." });
      else if (!r.pl.opt) fb.push({ ok: false, t: "Gap: nothing covers " + r.pl.label + ". Without it the tree isn't collectively exhaustive." });
    });
    const missedSubs = [];
    best.res.forEach(function (r) {
      if (r.pl.opt) return;
      r.pl.subs.forEach(function (s) { if (r.subsHit.indexOf(s) < 0) missedSubs.push(s.label); });
    });
    fb.push({ ok: best.depth >= 16, half: best.depth >= 8 && best.depth < 16, t: "Depth: " + best.hitSubs + " of " + best.totalSubs + " key drivers named." + (missedSubs.length ? " Worth adding: " + missedSubs.slice(0, 4).join("; ") + "." : "") });

    // MECE structure
    let structure = 0;
    const n = tops.length;
    const countPts = n >= 2 && n <= 5 ? 4 : n > 5 ? 2 : 0;
    structure += countPts;
    if (n < 2) fb.push({ ok: false, t: "Only one top-level branch. Split the problem into 2–5 buckets." });
    else if (n > 5) fb.push({ ok: false, half: true, t: n + " top-level branches is a lot. Group them into 2–5 so the interviewer can follow." });
    const deep = tops.filter(function (b) { return b.subs.length >= 2; }).length;
    structure += 4 * deep / n;
    if (deep < n) fb.push({ ok: false, half: true, t: (n - deep) + " branch(es) have fewer than 2 sub-points. Go one level deeper." });

    const overlaps = [];
    const seen = {};
    function addOverlap(i, j, why) {
      const k = Math.min(i, j) + "-" + Math.max(i, j);
      if (seen[k]) return;
      seen[k] = 1;
      overlaps.push("'" + (tops[i].label || "branch " + (i + 1)) + "' and '" + (tops[j].label || "branch " + (j + 1)) + "' " + why);
    }
    best.res.forEach(function (r) {
      for (let a = 1; a < r.general.length; a++) addOverlap(r.general[0], r.general[a], "both cover " + r.pl.label + ".");
    });
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        if (tops[i].label && tops[j].label && jaccard(tops[i].label, tops[j].label) >= 0.5) addOverlap(i, j, "are near-duplicates.");
        M.overlapPairs.forEach(function (pr) {
          if ((kwHit(labelsN[i], [pr[0]]) && kwHit(labelsN[j], [pr[1]])) || (kwHit(labelsN[i], [pr[1]]) && kwHit(labelsN[j], [pr[0]]))) addOverlap(i, j, "overlap (" + pr[0] + " / " + pr[1] + ").");
        });
        tops[i].subs.forEach(function (si) {
          tops[j].subs.forEach(function (sj) {
            if (jaccard(si, sj) >= 0.6) addOverlap(i, j, "both contain '" + si + "'.");
          });
        });
      }
    }
    structure += Math.max(0, 10 - 6 * overlaps.length);
    if (overlaps.length) overlaps.forEach(function (o) { fb.push({ ok: false, t: "Overlap: " + o + " Not mutually exclusive." }); });
    else if (n >= 2) fb.push({ ok: true, t: "No overlaps detected between branches." });

    const levelIssues = [];
    best.res.forEach(function (r) {
      if (!r.general.length) return;
      r.viaAlt.forEach(function (i) {
        if (r.general.indexOf(i) < 0) levelIssues.push("'" + tops[i].label + "' belongs under '" + tops[r.general[0]].label + "'. It's one level lower.");
      });
    });
    tops.forEach(function (b, i) {
      const t = tokens(b.label);
      const named = best.owner[i] && best.owner[i].general;
      if (!named && t.length && t.length <= 2 && t.every(function (w) { return M.vague.some(function (v) { return w.indexOf(v) === 0; }); })) levelIssues.push("'" + b.label + "' is too vague. Name what the bucket actually contains.");
      if (kwHit(normText(b.label), M.solutionWords)) levelIssues.push("'" + b.label + "' mixes solutions into a driver tree. Structure the drivers first; ideas come later.");
    });
    structure += Math.max(0, 7 - 4 * levelIssues.length);
    levelIssues.forEach(function (t) { fb.push({ ok: false, t: "Level: " + t }); });
    // A clean split of the wrong problem is only partly useful: scale structure by prompt fit.
    const fit = best.coverage / 40;
    if (fit < 1) {
      structure *= 0.5 + 0.5 * fit;
      if (fit < 0.75) fb.push({ ok: false, half: true, t: "MECE structure points are scaled down because the tree doesn't fit this prompt yet." });
    }

    // Prioritisation
    let prio = 0;
    const hyp = String(hypothesis || "").trim();
    if (hyp.length >= 15) prio += 5;
    if (hyp && kwHit(normText(hyp), p.priority.kw)) {
      prio += 10;
      fb.push({ ok: true, t: "Good prioritisation: you started where the prompt's clue points." });
    } else {
      fb.push({ ok: false, t: (hyp ? "Your starting point misses the clue. " : "You didn't say where you'd start. ") + p.priority.why });
    }

    // Off-prompt content
    let pen = 0;
    p.offs.forEach(function (o) {
      if (kwHit(allN, o.kw)) { pen += 5; fb.push({ ok: false, t: "Off-prompt: " + o.why }); }
    });
    pen = Math.min(15, pen);
    const otPen = overtime > 30 ? 10 : overtime > 0 ? 5 : 0;
    if (otPen) fb.push({ ok: false, t: "Over time by " + Math.round(overtime) + " sec (−" + otPen + ")." });

    const parts = [
      { name: "Fits the prompt", v: best.coverage, max: 40 },
      { name: "Depth", v: best.depth, max: 20 },
      { name: "MECE structure", v: structure, max: 25 },
      { name: "Prioritisation", v: prio, max: 15 }
    ];
    const raw = parts.reduce(function (a, x) { return a + x.v; }, 0) - pen - otPen;
    return { total: Math.max(0, Math.min(100, Math.round(raw))), parts: parts, penalty: pen + otPen, feedback: fb, frame: best.fr.name, tops: tops };
  }

  function scoreBuilder(p, chosen, placed, prioPick, overtime) {
    const B = p.builder;
    const correct = B.buckets.filter(function (b) { return b.ok; }).map(function (b) { return b.t; });
    const fb = [];
    const hits = chosen.filter(function (t) { return correct.indexOf(t) >= 0; });
    const decoys = chosen.filter(function (t) { return correct.indexOf(t) < 0; });
    const bucketPts = Math.max(0, 30 * hits.length / correct.length - 10 * decoys.length);
    correct.forEach(function (t) {
      if (chosen.indexOf(t) < 0) fb.push({ ok: false, t: "Gap: you didn't use '" + t + "' as a top-level bucket." });
    });
    decoys.forEach(function (t) {
      const b = B.buckets.find(function (x) { return x.t === t; });
      fb.push({ ok: false, t: "'" + t + "' isn't a good top-level bucket. " + b.why });
    });
    if (!decoys.length && hits.length === correct.length) fb.push({ ok: true, t: "Your top-level buckets are MECE and fit the prompt." });

    let right = 0;
    B.cards.forEach(function (c) {
      const at = placed[c.t] || "__out";
      const ok = c.b ? at === c.b : at === "__out";
      if (ok) right++;
      else if (c.b) fb.push({ ok: false, t: "'" + c.t + "' belongs under " + c.b + (at === "__out" ? " (you left it out)." : ", not " + at + ".") });
      else fb.push({ ok: false, t: "'" + c.t + "' should be left out: " + c.why });
    });
    const cardPts = 50 * right / B.cards.length;
    if (right === B.cards.length) fb.push({ ok: true, t: "Every card is in the right place." });

    const empty = chosen.filter(function (t) { return !B.cards.some(function (c) { return placed[c.t] === t; }); });
    const structPts = (empty.length ? 0 : 5) + (decoys.length ? 0 : 5);
    if (empty.length) fb.push({ ok: false, t: "Empty bucket(s): " + empty.join(", ") + ". A bucket with nothing in it shouldn't be in the tree." });

    const prioOk = B.priority.indexOf(prioPick) >= 0;
    const prioPts = prioOk ? 10 : 0;
    fb.push(prioOk ? { ok: true, t: "Good prioritisation: you'd start where the prompt's clue points." } : { ok: false, t: (prioPick ? "Starting with '" + prioPick + "' misses the clue. " : "You didn't pick a starting branch. ") + p.priority.why });

    const otPen = overtime > 30 ? 10 : overtime > 0 ? 5 : 0;
    if (otPen) fb.push({ ok: false, t: "Over time by " + Math.round(overtime) + " sec (−" + otPen + ")." });
    const parts = [
      { name: "Top-level buckets", v: bucketPts, max: 30 },
      { name: "Cards placed correctly", v: cardPts, max: 50 },
      { name: "Clean structure", v: structPts, max: 10 },
      { name: "Prioritisation", v: prioPts, max: 10 }
    ];
    const raw = parts.reduce(function (a, x) { return a + x.v; }, 0) - otPen;
    return { total: Math.max(0, Math.min(100, Math.round(raw))), parts: parts, penalty: otPen, feedback: fb };
  }

  function modelTree(p) {
    return { t: p.question, c: p.builder.buckets.filter(function (b) { return b.ok; }).map(function (b) {
      return { t: b.t, c: p.builder.cards.filter(function (c) { return c.b === b.t; }).map(function (c) { return { t: c.t }; }) };
    }) };
  }

  function viewMece(arg) {
    const m = meceState();
    const P = D.mece.prompts;
    const game = { iv: null };
    onLeave(function () { clearInterval(game.iv); });

    function menu() {
      clearInterval(game.iv);
      const d = m.duration;
      main.innerHTML =
        '<div class="page-head"><h1>MECE Practice</h1><p>Get a case prompt, then structure it against the clock, just like the "give me a minute to structure" moment in an interview. There\'s no single correct tree; you\'re scored on the <b>logic</b>: does it fit the prompt, is it mutually exclusive and collectively exhaustive, does it go deep enough, and do you start where the clues point?</p></div>' +
        '<section class="card"><h3>Mode</h3><div class="filter-row">' +
          '<button class="chip' + (m.mode === "free" ? " active" : "") + '" data-mode="free">✍️ Free-type</button>' +
          '<button class="chip' + (m.mode === "builder" ? " active" : "") + '" data-mode="builder">🧱 Builder (cards)</button>' +
        '</div><p class="meta" style="margin:0">' + (m.mode === "free"
          ? "Type your own branches and sub-points, as you would on paper. Scored on concepts and MECE rules against several valid structures."
          : "Choose top-level buckets from a bank (some are traps), then sort the cards into them or leave them out. Scored exactly.") + "</p>" +
        '<h3 style="margin-top:16px">⏱️ Time to structure</h3><div class="filter-row">' +
          MECE_TIMES.map(function (t) { return '<button class="chip' + (d === t ? " active" : "") + '" data-time="' + t + '">' + esc(fmtDuration(t)) + "</button>"; }).join("") +
        '</div><div class="input-row"><label class="meta" for="meceCustom">Custom (seconds)</label><input class="input" id="meceCustom" type="number" min="' + MIN_TIME + '" max="' + MAX_TIME + '" step="5" style="width:120px" placeholder="e.g. 150" value="' + (d && MECE_TIMES.indexOf(d) < 0 ? d : "") + '"><button class="btn sm ghost" id="meceSet">Set</button></div>' +
        '<p class="meta" style="margin:8px 0 0">The clock keeps running past zero: going over time costs 5 points (10 if more than 30 sec over).</p>' +
        '<div class="btn-row"><button class="btn" id="meceRandom">🎲 Random prompt</button></div></section>' +
        '<section class="section"><h2>Prompts</h2><div class="grid grid-3">' + P.map(function (p) {
          const bf = m.best[p.id + ":free"], bb = m.best[p.id + ":builder"];
          return '<button class="card mece-pick" data-pid="' + p.id + '" style="text-align:left;cursor:pointer"><div class="card-icon">' + p.icon + "</div><h3>" + esc(p.title) + "</h3>" +
            '<div class="tags"><span class="tag brand">' + esc(p.type) + "</span>" +
            (bf != null ? '<span class="tag ' + (bf >= 85 ? "good" : "") + '">✍️ ' + bf + "</span>" : "") +
            (bb != null ? '<span class="tag ' + (bb >= 85 ? "good" : "") + '">🧱 ' + bb + "</span>" : "") +
            (bf == null && bb == null ? '<span class="tag gold">+XP</span>' : "") + '</div><div style="margin-top:10px">' + stars(p.difficulty) + "</div></button>";
        }).join("") + "</div></section>" +
        '<section class="section grid grid-2">' +
          '<div class="card"><h3>How free-type is scored</h3><ul class="list-check">' +
            "<li><b>Fits the prompt (40):</b> your top-level branches cover the drivers this case needs.</li>" +
            "<li><b>Depth (20):</b> the sub-points name the key drivers.</li>" +
            "<li><b>MECE structure (25):</b> 2–5 branches, no overlaps, no mixed levels, no vague buckets.</li>" +
            "<li><b>Prioritisation (15):</b> where you'd start, and whether it follows the clue.</li>" +
          '</ul><p class="meta" style="margin:0">Scoring runs offline using keyword rules, so it can\'t understand wording the way a person would. If valid logic scores low, compare with the model tree.</p></div>' +
          '<div class="card"><h3>Tips</h3><ul class="list-check">' +
            "<li>Split with an equation when you can (Profit = Revenue − Costs; Book = inflows − outflows).</li>" +
            "<li>Keep each level at the same altitude: 'Fuel' doesn't sit next to 'Costs'.</li>" +
            "<li>Read the prompt for clues that rule branches in or out.</li>" +
            "<li>Name buckets by what they contain, not 'Factors' or 'Analysis'.</li>" +
          "</ul></div></section>";

      main.querySelectorAll("[data-mode]").forEach(function (b) { b.addEventListener("click", function () { m.mode = b.dataset.mode; save(); menu(); }); });
      main.querySelectorAll("[data-time]").forEach(function (b) { b.addEventListener("click", function () { m.duration = +b.dataset.time; save(); menu(); }); });
      const setCustom = function () {
        const v = Math.round(+document.getElementById("meceCustom").value);
        if (!v || v < MIN_TIME || v > MAX_TIME) { toast("Enter " + MIN_TIME + "–" + MAX_TIME + " seconds"); return; }
        m.duration = v; save(); menu();
      };
      document.getElementById("meceSet").addEventListener("click", setCustom);
      document.getElementById("meceCustom").addEventListener("keydown", function (e) { if (e.key === "Enter") setCustom(); });
      document.getElementById("meceRandom").addEventListener("click", function () {
        const pool = P.filter(function (p) { return p.id !== arg; });
        play(pick(pool));
      });
      main.querySelectorAll(".mece-pick").forEach(function (b) {
        b.addEventListener("click", function () { play(P.find(function (p) { return p.id === b.dataset.pid; })); });
      });
    }

    function startClock(run) {
      clearInterval(game.iv);
      run.start = Date.now();
      const paint = function () {
        const el = document.getElementById("meceClock");
        if (!el) return;
        const t = (Date.now() - run.start) / 1000;
        if (!run.duration) { el.textContent = clock(t); return; }
        const left = run.duration - t;
        el.textContent = left >= 0 ? clock(Math.ceil(left)) : "+" + clock(-left);
        el.className = "timer" + (left < 0 ? " over" : left < 15 ? " warn" : "");
        const b = document.getElementById("meceBar");
        if (b) b.style.width = Math.max(0, left / run.duration) * 100 + "%";
      };
      paint();
      game.iv = setInterval(paint, 250);
    }
    function overtime(run) { return run.duration ? Math.max(0, (Date.now() - run.start) / 1000 - run.duration) : 0; }

    function header(p, run) {
      return '<a class="crumb" href="#/mece" id="meceBack">← All prompts</a>' +
        '<div class="mece-top card"><div><span class="tag brand">' + esc(p.type) + '</span> <span class="tag">' + (run.mode === "free" ? "✍️ Free-type" : "🧱 Builder") + "</span>" +
        '<h2 style="margin:8px 0 0">' + p.icon + " " + esc(p.title) + '</h2></div><div class="center"><div class="timer" id="meceClock">0:00</div><div class="meta">' + (run.duration ? "to structure" : "untimed") + "</div></div></div>" +
        (run.duration ? '<div class="bar" style="margin-top:10px"><i id="meceBar" style="width:100%"></i></div>' : "") +
        '<div class="prompt" style="margin-top:14px"><b>Prompt.</b> ' + esc(p.prompt) + "</div>";
    }

    function play(p) {
      const run = { p: p, mode: m.mode, duration: m.duration, start: Date.now() };
      if (run.mode === "free") playFree(run); else playBuilder(run);
      startClock(run);
    }

    /* ---- free-type ---- */
    function playFree(run) {
      const p = run.p;
      run.branches = [{ label: "", subs: "" }, { label: "", subs: "" }, { label: "", subs: "" }];
      run.hyp = "";
      function render() {
        main.innerHTML = header(p, run) +
          '<div class="card" style="margin-top:16px"><h3>Your framework</h3><p class="meta">Top-level branch on the left, sub-points on the right (one per line). Aim for 2–5 branches.</p>' +
          '<div class="mece-root">🎯 ' + esc(p.question) + "</div>" +
          run.branches.map(function (b, i) {
            return '<div class="branch-row"><div class="branch-num">' + (i + 1) + '</div><input class="input branch-label" data-i="' + i + '" placeholder="Branch ' + (i + 1) + ' (e.g. ' + (i === 0 ? "Revenue" : i === 1 ? "Costs" : "…") + ')" value="' + esc(b.label) + '">' +
              '<textarea class="input branch-subs" data-i="' + i + '" rows="3" placeholder="Sub-points, one per line">' + esc(b.subs) + "</textarea>" +
              (run.branches.length > 2 ? '<button class="icon-btn" data-del="' + i + '" title="Remove branch" aria-label="Remove branch ' + (i + 1) + '">✕</button>' : "<span></span>") + "</div>";
          }).join("") +
          (run.branches.length < MECE_MAX_BRANCHES ? '<button class="btn ghost sm" id="addBranch">+ Add branch</button>' : "") +
          '<label style="display:block;margin-top:16px"><b>Where would you start, and why?</b> <span class="meta">One or two sentences: your hypothesis and the clue behind it.</span>' +
          '<textarea class="input" id="hyp" rows="2" placeholder="e.g. I\'d start with … because the prompt says …">' + esc(run.hyp) + "</textarea></label>" +
          '<div class="btn-row"><button class="btn accent" id="submitFree">Submit framework</button></div></div>';
        main.querySelectorAll(".branch-label").forEach(function (el) { el.addEventListener("input", function () { run.branches[+el.dataset.i].label = el.value; }); });
        main.querySelectorAll(".branch-subs").forEach(function (el) { el.addEventListener("input", function () { run.branches[+el.dataset.i].subs = el.value; }); });
        main.querySelectorAll("[data-del]").forEach(function (el) { el.addEventListener("click", function () { run.branches.splice(+el.dataset.del, 1); render(); }); });
        const add = document.getElementById("addBranch");
        if (add) add.addEventListener("click", function () { run.branches.push({ label: "", subs: "" }); render(); const ls = main.querySelectorAll(".branch-label"); ls[ls.length - 1].focus(); });
        document.getElementById("hyp").addEventListener("input", function (e) { run.hyp = e.target.value; });
        document.getElementById("submitFree").addEventListener("click", function () {
          const filled = run.branches.filter(function (b) { return b.label.trim(); }).length;
          if (filled < 2) { toast("Add at least two top-level branches first"); return; }
          const r = scoreFree(p, run.branches, run.hyp, overtime(run));
          finish(run, r, { t: p.question, c: r.tops.map(function (b) { return { t: b.label || "(unnamed)", c: b.subs.map(function (s) { return { t: s }; }) }; }) });
        });
        document.getElementById("meceBack").addEventListener("click", function (e) { e.preventDefault(); menu(); });
      }
      render();
      const first = main.querySelector(".branch-label");
      if (first) first.focus();
    }

    /* ---- builder ---- */
    function playBuilder(run) {
      const p = run.p;
      const B = p.builder;
      run.bank = shuffle(B.buckets.map(function (b) { return b.t; }));
      run.cardOrder = shuffle(B.cards.map(function (c) { return c.t; }));
      run.chosen = [];
      run.placed = {};
      run.sel = null;
      run.prio = null;
      run.stage = "pick";

      function render() {
        let body;
        if (run.stage === "pick") {
          body = '<div class="card" style="margin-top:16px"><h3>Step 1 · Choose your top-level buckets</h3><p class="meta">Pick 2–5. Some options are traps: overlapping, at the wrong level, or off-prompt.</p><div class="filter-row">' +
            run.bank.map(function (t) {
              const on = run.chosen.indexOf(t) >= 0;
              return '<button class="chip' + (on ? " active" : "") + '" data-bucket="' + esc(t) + '" aria-pressed="' + on + '">' + esc(t) + "</button>";
            }).join("") + '</div><div class="btn-row"><button class="btn" id="toPlace"' + (run.chosen.length >= 2 && run.chosen.length <= 5 ? "" : " disabled") + ">Next: sort the cards →</button></div></div>";
        } else {
          const cols = run.chosen.concat(["__out"]);
          const unplaced = run.cardOrder.filter(function (t) { return !run.placed[t]; });
          const cardBtn = function (t) {
            return '<button class="mece-card' + (run.sel === t ? " sel" : "") + '" draggable="true" data-card="' + esc(t) + '">' + esc(t) + "</button>";
          };
          body = '<div class="card" style="margin-top:16px"><h3>Step 2 · Sort the cards</h3><p class="meta">Tap a card, then tap a bucket (or drag it). Cards that don\'t belong go to <b>Leave out</b>. Tap a placed card to move it again.</p>' +
            '<div class="mece-bank" data-col="__bank">' + (unplaced.length ? unplaced.map(cardBtn).join("") : '<span class="meta">All cards placed ✔</span>') + "</div>" +
            '<div class="mece-board">' + cols.map(function (c) {
              const inCol = run.cardOrder.filter(function (t) { return run.placed[t] === c; });
              return '<div class="mece-col' + (c === "__out" ? " out" : "") + '" data-col="' + esc(c) + '"><div class="mece-col-head">' + (c === "__out" ? "🗑️ Leave out" : esc(c)) + "</div>" + inCol.map(cardBtn).join("") + '<div class="mece-drop">' + (run.sel ? "Tap to place here" : "") + "</div></div>";
            }).join("") + "</div>" +
            '<h3 style="margin-top:16px">Step 3 · Where would you start?</h3><div class="filter-row">' +
            run.chosen.map(function (t) { return '<button class="chip' + (run.prio === t ? " active" : "") + '" data-prio="' + esc(t) + '">' + esc(t) + "</button>"; }).join("") + "</div>" +
            '<div class="btn-row"><button class="btn ghost" id="backPick">← Change buckets</button><button class="btn accent" id="submitBuilder">Submit framework</button></div></div>';
        }
        main.innerHTML = header(p, run) + body;
        document.getElementById("meceBack").addEventListener("click", function (e) { e.preventDefault(); menu(); });

        if (run.stage === "pick") {
          main.querySelectorAll("[data-bucket]").forEach(function (b) {
            b.addEventListener("click", function () {
              const t = b.dataset.bucket, at = run.chosen.indexOf(t);
              if (at >= 0) run.chosen.splice(at, 1);
              else if (run.chosen.length >= 5) { toast("Five buckets is the maximum"); return; }
              else run.chosen.push(t);
              render();
            });
          });
          document.getElementById("toPlace").addEventListener("click", function () {
            Object.keys(run.placed).forEach(function (k) { if (run.placed[k] !== "__out" && run.chosen.indexOf(run.placed[k]) < 0) delete run.placed[k]; });
            if (run.chosen.indexOf(run.prio) < 0) run.prio = null;
            run.stage = "place"; render();
          });
          return;
        }

        const place = function (card, col) {
          if (col === "__bank") delete run.placed[card]; else run.placed[card] = col;
          run.sel = null; render();
        };
        main.querySelectorAll("[data-card]").forEach(function (el) {
          el.addEventListener("click", function (e) {
            e.stopPropagation();
            run.sel = run.sel === el.dataset.card ? null : el.dataset.card;
            render();
          });
          el.addEventListener("dragstart", function (e) { e.dataTransfer.setData("text/plain", el.dataset.card); });
        });
        main.querySelectorAll("[data-col]").forEach(function (col) {
          col.addEventListener("click", function () { if (run.sel) place(run.sel, col.dataset.col); });
          col.addEventListener("dragover", function (e) { e.preventDefault(); col.classList.add("over"); });
          col.addEventListener("dragleave", function () { col.classList.remove("over"); });
          col.addEventListener("drop", function (e) { e.preventDefault(); const t = e.dataTransfer.getData("text/plain"); if (t) place(t, col.dataset.col); });
        });
        main.querySelectorAll("[data-prio]").forEach(function (b) { b.addEventListener("click", function () { run.prio = b.dataset.prio; render(); }); });
        document.getElementById("backPick").addEventListener("click", function () { run.stage = "pick"; run.sel = null; render(); });
        document.getElementById("submitBuilder").addEventListener("click", function () {
          const left = run.cardOrder.filter(function (t) { return !run.placed[t]; }).length;
          if (left && !confirm(left + " card(s) aren't placed yet. They'll count as 'Leave out'. Submit anyway?")) return;
          const r = scoreBuilder(p, run.chosen, run.placed, run.prio, overtime(run));
          finish(run, r, { t: p.question, c: run.chosen.map(function (b) {
            return { t: b, c: run.cardOrder.filter(function (t) { return run.placed[t] === b; }).map(function (t) { return { t: t }; }) };
          }) });
        });
      }
      render();
    }

    /* ---- results ---- */
    function finish(run, r, yourTree) {
      clearInterval(game.iv);
      const p = run.p;
      const key = p.id + ":" + run.mode;
      const prev = m.best[key];
      const first = prev == null;
      m.best[key] = Math.max(prev || 0, r.total);
      m.runs = (m.runs || 0) + 1;
      save();
      const xp = first ? Math.round(r.total / 5) : Math.round(r.total / 20);
      if (xp) addXP(xp, "MECE practice"); else { touchStreak(); checkBadges(); }
      if (r.total >= 85) confetti();
      const grade = r.total >= 85 ? ["🏆", "Partner-ready structure"] : r.total >= 70 ? ["💪", "Strong structure"] : r.total >= 50 ? ["📈", "Getting there"] : ["🧭", "Keep practising"];
      const secs = Math.round((Date.now() - run.start) / 1000);
      const others = p.frames.length > 1 ? '<p class="meta" style="margin:8px 0 0">Other valid structures for this prompt: ' + p.frames.slice(1).map(function (f) { return esc(f.name); }).join("; ") + ".</p>" : "";
      main.innerHTML =
        '<a class="crumb" href="#/mece" id="meceBack">← All prompts</a>' +
        '<div class="card center"><div class="big-emoji">' + grade[0] + "</div><h2>" + grade[1] + '</h2><div class="kpi">' + r.total + '/100</div><p class="muted">' + esc(p.title) + " · " + (run.mode === "free" ? "Free-type" : "Builder") + " · " + clock(secs) + (run.duration ? " of " + clock(run.duration) : "") +
          (prev != null && r.total > prev ? " · new best!" : "") + " · +" + xp + ' XP</p>' +
          '<div class="mece-parts">' + r.parts.map(function (x) {
            return '<div><div class="mece-part-head"><span>' + esc(x.name) + "</span><b>" + Math.round(x.v) + "/" + x.max + "</b></div>" + bar((x.v / x.max) * 100, "small") + "</div>";
          }).join("") + (r.penalty ? '<div class="meta">Penalties: −' + r.penalty + "</div>" : "") + "</div></div>" +
        '<div class="card" style="margin-top:16px"><h3>Feedback</h3><ul class="mece-fb">' + r.feedback.map(function (f) {
          return '<li class="' + (f.info ? "info" : f.ok ? "ok" : f.half ? "half" : "no") + '">' + esc(f.t) + "</li>";
        }).join("") + "</ul></div>" +
        '<div class="grid grid-2" style="margin-top:16px"><div class="card"><h3>Your tree</h3><ul class="tree">' + treeHTML(yourTree) + "</ul></div>" +
        '<div class="card"><h3>Model tree</h3><ul class="tree">' + treeHTML(modelTree(p)) + "</ul>" + others + "</div></div>" +
        '<div class="card" style="margin-top:16px"><h3>💡 Takeaway</h3><p style="margin:0">' + esc(p.takeaway) + '</p><p class="meta" style="margin:8px 0 0"><b>Where to start:</b> ' + esc(p.priority.why) + "</p></div>" +
        '<div class="btn-row"><button class="btn ghost" id="again">↻ Try again</button><button class="btn ghost" id="switchMode">Try in ' + (run.mode === "free" ? "🧱 Builder" : "✍️ Free-type") + ' mode</button><button class="btn" id="nextPrompt">Next prompt →</button></div>';
      document.getElementById("meceBack").addEventListener("click", function (e) { e.preventDefault(); menu(); });
      document.getElementById("again").addEventListener("click", function () { play(p); });
      document.getElementById("switchMode").addEventListener("click", function () { m.mode = run.mode === "free" ? "builder" : "free"; save(); play(p); });
      document.getElementById("nextPrompt").addEventListener("click", function () {
        const i = P.indexOf(p);
        play(P[(i + 1) % P.length]);
      });
      window.scrollTo(0, 0);
      renderHud();
    }

    const direct = arg && P.find(function (p) { return p.id === arg; });
    if (direct) play(direct); else menu();
  }

  /* ------------------------- Daily challenge ------------------------- */
  function quizPool() {
    const pool = [];
    D.frameworks.forEach(function (f) {
      f.quiz.forEach(function (q) { pool.push(Object.assign({ src: f.name }, q)); });
    });
    D.extraQuiz.forEach(function (q) { pool.push(Object.assign({ src: "Case toolkit" }, q)); });
    return pool;
  }

  function viewDaily() {
    const t = today();
    const pool = quizPool();
    const done = S.daily[t];
    let practice = false;
    let qs, answers, idx;

    function setup(isPractice) {
      practice = isPractice;
      const rnd = isPractice ? Math.random : seeded("daily-" + t);
      qs = shuffle(pool.slice(), rnd).slice(0, 5).map(function (q) {
        return Object.assign({ order: order(q.options.length, rnd) }, q);
      });
      answers = [];
      idx = 0;
    }

    function summary() {
      const d = S.daily[t];
      main.innerHTML =
        '<div class="page-head"><h1>Daily challenge</h1><p>5 questions, refreshed every day. Come back tomorrow to keep your 🔥 streak.</p></div>' +
        '<div class="card center"><div class="big-emoji">' + (d.score === 5 ? "🏆" : "✅") + "</div><h2>Today: " + d.score + '/5</h2><p class="muted">Current streak: ' + (streakAlive() ? S.streak.count : 0) + " day(s) · best " + (S.streak.best || 0) + "</p>" +
        '<div class="btn-row" style="justify-content:center"><button class="btn" id="practice">Practice round (no XP)</button><a class="btn ghost" href="#/cases">Try a case</a></div></div>';
      document.getElementById("practice").addEventListener("click", function () { setup(true); render(); });
    }

    function render() {
      const q = qs[idx];
      const a = answers[idx];
      main.innerHTML =
        '<div class="page-head"><h1>' + (practice ? "Practice round" : "Daily challenge") + "</h1><p>" + (practice ? "Random questions — just for practice." : "+10 XP per correct answer · +20 XP bonus for a perfect 5/5.") + "</p></div>" +
        '<div class="stepper">' + qs.map(function (_, i) { return '<span class="' + (i < idx ? "done" : i === idx ? "now" : "") + '"></span>'; }).join("") + "</div>" +
        '<div class="card"><span class="tag brand">' + esc(q.src) + '</span><div class="q-title" style="margin-top:10px">' + (idx + 1) + ". " + esc(q.q) + '</div><div class="options">' +
        q.order.map(function (oi, pos) {
          const o = q.options[oi];
          let cls = "";
          if (a != null) { if (oi === q.answer) cls = "correct"; else if (oi === a) cls = "wrong"; }
          return '<button class="opt ' + cls + '" data-o="' + oi + '"' + (a != null ? " disabled" : "") + '><span class="key">' + letter(pos) + "</span><span>" + esc(o) + "</span></button>";
        }).join("") + "</div>" +
        (a != null ? '<div class="feedback ' + (a === q.answer ? "good" : "bad") + '">' + (a === q.answer ? "✅ " : "❌ ") + esc(q.explain) + '</div><div class="btn-row"><button class="btn" id="next">' + (idx < qs.length - 1 ? "Next →" : "See results") + "</button></div>" : "") +
        "</div>";
      main.querySelectorAll(".opt").forEach(function (b) {
        b.addEventListener("click", function () {
          if (answers[idx] != null) return;
          answers[idx] = +b.dataset.o;
          render();
        });
      });
      const nx = document.getElementById("next");
      if (nx) nx.addEventListener("click", function () {
        if (idx < qs.length - 1) { idx++; render(); return; }
        const score = answers.filter(function (x, i) { return x === qs[i].answer; }).length;
        if (practice) {
          toast("Practice score: " + score + "/5");
          if (S.daily[t]) summary(); else { setup(false); render(); }
          return;
        }
        S.daily[t] = { score: score };
        if (score === 5) { S.quizPerfect = true; confetti(); }
        save();
        if (score) addXP(score * 10 + (score === 5 ? 20 : 0), "Daily challenge");
        else { touchStreak(); checkBadges(); save(); }
        summary();
        renderHud();
      });
    }

    if (done) summary();
    else { setup(false); render(); }
  }

  /* ----------------------------- Profile ----------------------------- */
  function viewProfile() {
    const li = levelInfo();
    const casesDone = D.cases.filter(function (c) { return S.cases[c.id] && S.cases[c.id].done; }).length;
    main.innerHTML =
      '<div class="page-head"><h1>Profile & badges</h1><p>Your progress is stored only in this browser. Export a backup to move it to another device.</p></div>' +
      '<div class="grid grid-2"><div class="card level-card"><div class="muted">Level ' + (li.i + 1) + " of " + D.levels.length + '</div><div class="level-name">🎓 ' + esc(li.cur.name) + "</div>" + bar(li.pct) +
        '<div class="muted" style="font-size:.9rem">' + fmt(S.xp) + " XP" + (li.next ? " · " + fmt(li.toNext) + " to " + esc(li.next.name) : "") + "</div>" +
        '<div class="stat-row"><div class="stat"><b>' + Object.keys(S.lessons).length + "</b><span>lessons</span></div>" +
        '<div class="stat"><b>' + casesDone + "</b><span>cases</span></div>" +
        '<div class="stat"><b>' + S.stories.length + "</b><span>stories</span></div></div>" +
        '<div class="stat-row"><div class="stat"><b>' + S.math.best + "</b><span>math best</span></div>" +
        '<div class="stat"><b>' + (S.streak.best || 0) + "</b><span>best streak</span></div>" +
        '<div class="stat"><b>' + Object.keys(S.daily).length + "</b><span>daily done</span></div></div></div>" +
      '<div class="card"><h3>Career ladder</h3>' + D.levels.map(function (l, i) {
        return '<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px dashed var(--border)' + (i === li.i ? ";font-weight:800;color:var(--brand)" : i > li.i ? ";opacity:.55" : "") + '"><span>' + (i < li.i ? "✔ " : i === li.i ? "▶ " : "") + esc(l.name) + '</span><span class="meta">' + fmt(l.xp) + " XP</span></div>";
      }).join("") + "</div></div>" +
      '<section class="section"><h2>Badges (' + Object.keys(S.badges).length + "/" + D.badges.length + ')</h2><div class="grid grid-4">' +
      D.badges.map(function (b) {
        const got = S.badges[b.id];
        return '<div class="badge' + (got ? "" : " locked") + '"><div class="b-icon">' + b.icon + "</div><b>" + esc(b.name) + "</b><small>" + esc(b.desc) + "</small>" + (got ? '<div class="meta" style="font-size:.75rem;margin-top:4px">Earned ' + esc(got) + "</div>" : "") + "</div>";
      }).join("") + "</div></section>" +
      '<section class="section card"><h3>Settings</h3>' +
        '<label class="meta" for="nm">Your name (for the greeting)</label><div class="input-row" style="margin-top:6px"><input class="input" id="nm" maxlength="40" value="' + esc(S.name) + '" placeholder="e.g. Alex"><button class="btn sm" id="saveName">Save</button></div>' +
        '<div class="btn-row"><button class="btn ghost" id="export">⬇ Export progress</button><label class="btn ghost" style="cursor:pointer">⬆ Import progress<input type="file" id="import" accept="application/json,.json" hidden></label><button class="btn danger" id="reset">Reset all progress</button></div>' +
      "</section>";

    document.getElementById("saveName").addEventListener("click", function () {
      S.name = document.getElementById("nm").value.trim();
      save();
      toast("Saved 👍");
    });
    document.getElementById("export").addEventListener("click", function () {
      const blob = new Blob([JSON.stringify(S, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = "consulting-academy-progress-" + today() + ".json";
      document.body.appendChild(a);
      a.click();
      setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 500);
    });
    document.getElementById("import").addEventListener("change", function (e) {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function () {
        try {
          const data = JSON.parse(reader.result);
          if (typeof data !== "object" || typeof data.xp !== "number") throw new Error("bad file");
          S = merge(defaultState(), data);
          save();
          applyTheme();
          toast("Progress imported ✅");
          route();
        } catch (err) {
          toast("That file doesn't look like a Consulting Academy backup.");
        }
      };
      reader.readAsText(file);
    });
    document.getElementById("reset").addEventListener("click", function () {
      if (!confirm("Reset ALL progress, XP, badges and stories? This cannot be undone.")) return;
      S = defaultState();
      save();
      applyTheme();
      toast("Progress reset.");
      route();
    });
  }

  function viewNotFound() {
    main.innerHTML = '<div class="card center"><div class="big-emoji">🧭</div><h2>Page not found</h2><p class="muted">That page doesn\'t exist.</p><a class="btn" href="#/">Go home</a></div>';
  }

  /* ================================================================== */
  /* Boot                                                                */
  /* ================================================================== */
  applyTheme();
  if (window.matchMedia) {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) mq.addEventListener("change", applyTheme);
  }
  checkBadges();
  route();

  // Installable offline app when served over http(s); opening index.html directly already works offline.
  if ("serviceWorker" in navigator && /^https?:$/.test(location.protocol)) {
    navigator.serviceWorker.register("sw.js").catch(function () { /* optional */ });
  }
})();
