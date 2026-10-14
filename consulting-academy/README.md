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
| 🗂️ **Frameworks** (12) | MECE, issue trees & hypotheses, Pyramid Principle, profitability, market entry, M&A, market sizing, pricing, growth (Ansoff), Five Forces, 3Cs/4Ps, cost reduction. Each has an issue tree, key points, pitfalls and a 3-question check. | 10 per correct answer + 30 per lesson |
| 💼 **Case studies** (5) | Coffee-chain profitability, bank digital-lending market entry, market sizing, PE gym buyout, streaming price hike. Clarify → structure → exhibits & math → brainstorm → synthesis, with interviewer feedback. | 15 per step right first time + 50 bonus |
| 🎤 **Behavioural** (15 questions) | STAR method, what each question tests, sample answers, a 2-minute practice timer, self-assessment rubric and a personal **story bank**. | 10 + 3 per rubric item |
| 🧮 **Mental Math Arena** | 60-second sprints: percentages, zeros, division, growth, breakeven, margins. Accepts `450k`, `1.2m`. | 2 per correct |
| 🎯 **Daily Challenge** | 5 questions a day, the same for everyone on a given date, to keep your 🔥 streak alive. | 10 per correct + 20 for 5/5 |

**Gamification:** XP and a career ladder (Intern → Business Analyst → Associate → Consultant →
Engagement Manager → Principal → Partner), 14 badges, daily streaks, confetti, and personal bests.

**Progress** is saved in your browser (localStorage). Use **Badges → Export progress** to back
it up or move it to another device.

## Editing content

All course content (frameworks, cases, questions, badges, levels) lives in `js/data.js`.
Add a case by copying an entry in `cases`. Step kinds are `mcq` (one correct option),
`multi` (select all correct) and `math` (numeric `answer` with a `tolerance`).

Case figures are illustrative, made up for practice.
