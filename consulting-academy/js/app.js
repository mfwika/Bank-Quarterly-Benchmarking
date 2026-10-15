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
