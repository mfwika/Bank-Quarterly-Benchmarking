# Consulting Academy 🎓

An **offline, gamified** training site for consulting interviews: frameworks, interactive case
studies, behavioural (fit) questions and mental math. Plain HTML/CSS/JavaScript: no install,
no build step, no internet.

## How to use

- **Open `index.html`** in any modern browser (double-click it). Everything works offline.
- To install it as an app (phone/desktop), serve the folder over http(s), e.g.
  `python3 -m http.server` from this folder, open it once, then use "Install app" or
  "Add to Home Screen". A service worker caches it for offline use.

## What's inside

| Module | What you do | XP |
|---|---|---|
| 🗂️ **Frameworks** (14) | How case interviews work (what's scored, common stumbles, the 3 follow-up questions), MECE, issue trees & hypotheses, Pyramid Principle, profitability, market entry, M&A, market sizing, pricing, growth (Ansoff), where to play / how to win, Five Forces, 3Cs/4Ps, cost reduction. Each has an issue tree, key points, pitfalls and a 3-question check. | 10 per correct answer + 30 per lesson |
| 💼 **Case studies** (10) | Coffee-chain profitability, bank digital-lending market entry, segmented market sizing, PE gym buyout (MOIC / max price), streaming tiered pricing, and a phone-repair chain (4-step market sizing by income segment with sense checks, then a where-to-play / how-to-win growth strategy)), plus four harder cases: doubling a charity's donations (retention and donor lifetime value), tripling a ramen group's sales (capacity math and the franchise-royalty trap), cutting a bank's branch costs 25% without losing deposits, and a carmaker's US EV share push. 6–9 steps each with multi-step math, trap exhibits and believable wrong answers of similar length. Answer order is shuffled every play. | 15 per step right first time + 50 bonus |
| 🎤 **Behavioural** (15 questions) | STAR method, what each question tests, sample answers, a 2-minute practice timer, self-assessment rubric and a personal **story bank**. | 10 + 3 per rubric item |
| 🧩 **MECE Practice** (12 prompts) | Structure a case prompt against a clock you set (60 sec – 5 min, custom, or untimed). **Free-type**: write your own branches; scored offline on prompt fit, depth, MECE rules (overlaps, gaps, mixed levels, vague buckets) and whether your starting point follows the prompt's clue, against several valid structures per prompt. **Builder**: pick top-level buckets (some are traps) and sort cards into them. Model tree and takeaway after each attempt. | up to 20 per prompt and mode |
| 🧮 **Mental Math Arena** | Timed sprints with a **custom time limit** (30 sec – 5 min presets, any value from 10 sec to 30 min, or untimed practice) and selectable question types: percentages, zeros, division, growth, breakeven, margins. Best score is tracked per time limit. Accepts `450k`, `1.2m`. | 2 per correct (1 untimed) |
| 🎯 **Daily Challenge** | 5 questions a day, the same for everyone on a given date, to keep your 🔥 streak alive. | 10 per correct + 20 for 5/5 |

**Gamification:** XP and a career ladder (Intern → Business Analyst → Associate → Consultant →
Engagement Manager → Principal → Partner), 14 badges, daily streaks, confetti, and personal bests.

**Progress** is saved in your browser (localStorage). Use **Badges → Export progress** to back
it up or move it to another device.

## Editing content

All course content (frameworks, cases, questions, badges, levels) lives in `js/data.js`; MECE Practice prompts, valid structures and keywords live in `js/mece-data.js`.
Add a case by copying an entry in `cases`. Step kinds are `mcq` (one correct option),
`multi` (select all correct) and `math` (numeric `answer` with a `tolerance`).

Case figures are illustrative, made up for practice.
