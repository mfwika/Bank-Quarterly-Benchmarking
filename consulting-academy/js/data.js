/* Consulting Academy — course content.
 * Everything lives in this file so the site works from file:// with no server.
 * Tree nodes: { t: "label", c: [children] }.
 */
window.CA_DATA = {
  levels: [
    { name: "Intern", xp: 0 },
    { name: "Business Analyst", xp: 150 },
    { name: "Associate", xp: 400 },
    { name: "Consultant", xp: 800 },
    { name: "Engagement Manager", xp: 1300 },
    { name: "Principal", xp: 2000 },
    { name: "Partner", xp: 3000 }
  ],

  badges: [
    { id: "first-lesson", icon: "📘", name: "First Steps", desc: "Finish your first framework lesson." },
    { id: "core-done", icon: "🧠", name: "MECE Mind", desc: "Finish every core-thinking lesson." },
    { id: "all-frameworks", icon: "🗂️", name: "Framework Fluent", desc: "Finish every framework lesson." },
    { id: "first-case", icon: "💼", name: "Case Cracker", desc: "Complete your first case." },
    { id: "all-cases", icon: "🏆", name: "Case Veteran", desc: "Complete every case." },
    { id: "perfect-case", icon: "🎯", name: "Flawless", desc: "Complete a case without a single wrong answer." },
    { id: "storyteller", icon: "🎤", name: "Storyteller", desc: "Save 3 STAR stories in your story bank." },
    { id: "math-10", icon: "🧮", name: "Human Calculator", desc: "Score 10+ in one Mental Math sprint." },
    { id: "math-20", icon: "⚡", name: "Excel Who?", desc: "Score 20+ in one Mental Math sprint." },
    { id: "quiz-perfect", icon: "✅", name: "Quiz Whiz", desc: "Get 5/5 on a Daily Challenge." },
    { id: "streak-3", icon: "🔥", name: "On Fire", desc: "Practise 3 days in a row." },
    { id: "streak-7", icon: "🌋", name: "Unstoppable", desc: "Practise 7 days in a row." },
    { id: "level-consultant", icon: "🎓", name: "Staffed!", desc: "Reach the Consultant level." },
    { id: "level-partner", icon: "👑", name: "Partner Track", desc: "Reach the Partner level." }
  ],

  /* ------------------------------------------------------------------ */
  frameworks: [
    {
      id: "mece",
      group: "core",
      icon: "🧩",
      name: "MECE Thinking",
      tagline: "Mutually Exclusive, Collectively Exhaustive — the grammar of consulting.",
      intro: "Every structure you build in a case should be MECE: the buckets must not overlap (mutually exclusive) and together they must cover every possibility (collectively exhaustive). Interviewers listen for this before they listen for business insight.",
      tree: { t: "Why are a retailer's sales down?", c: [
        { t: "Fewer customers", c: [{ t: "New customers acquired" }, { t: "Existing customers churned" }] },
        { t: "Fewer transactions per customer", c: [{ t: "Visit frequency" }, { t: "Conversion per visit" }] },
        { t: "Lower value per transaction", c: [{ t: "Items per basket" }, { t: "Price per item" }] }
      ]},
      keyPoints: [
        "Split with math whenever you can (Revenue = Customers × Frequency × Basket) — math splits are MECE by construction.",
        "Other clean splits: internal vs external, supply vs demand, by segment / region / channel, by time (before / during / after).",
        "Keep 2–4 buckets per level. More than 5 usually means overlap or missing hierarchy.",
        "An 'Other' bucket is allowed — it makes a list exhaustive — but should be small."
      ],
      pitfalls: [
        "Overlap: 'Marketing' and 'Social media' as sibling buckets.",
        "Gaps: splitting customers into 'young' and 'professionals' (what about retirees?).",
        "Mixing levels: 'Costs' next to 'Rent' on the same level."
      ],
      quiz: [
        { q: "Which split of a bank's customers is MECE?", options: ["Retail, SME, Corporate", "Retail, Online, Corporate", "Young, Wealthy, Corporate", "Savers, Borrowers, Retail"], answer: 0, explain: "Retail / SME / Corporate are distinct segments that together cover the customer base. The others overlap (an online customer can be retail) or leave gaps." },
        { q: "Profit = Revenue − Costs is a good first split because…", options: ["It's what every interviewer expects", "It is a mathematical identity, so it is MECE by definition", "Costs are always the problem", "It avoids needing data"], answer: 1, explain: "Equation-based splits can't overlap and can't miss anything — that's why consultants love them." },
        { q: "You list causes of churn as: price, service quality, customer service, competitor offers. What's wrong?", options: ["Nothing", "'Service quality' and 'customer service' overlap", "It needs at least 6 items", "Price should come last"], answer: 1, explain: "Customer service is part of service quality — that's an overlap. Fix by defining the buckets more precisely (e.g. product, price, experience, competitive pull)." }
      ]
    },
    {
      id: "issue-tree",
      group: "core",
      icon: "🌳",
      name: "Issue Trees & Hypotheses",
      tagline: "Break a big question into small answerable ones — then test the most likely answer first.",
      intro: "An issue tree decomposes the client's key question into sub-questions until each leaf is something you can answer with data or a quick analysis. A hypothesis tree flips this: you state a likely answer up front and list what must be true for it to hold. Top firms are hypothesis-driven: form a view early, test it, revise it.",
      tree: { t: "Should Client X launch product Y? (Hypothesis: yes, if it earns > 15% ROI in 3 yrs)", c: [
        { t: "Is the market attractive?", c: [{ t: "Size & growth" }, { t: "Margins & competition" }] },
        { t: "Can we win?", c: [{ t: "Customer need vs our offer" }, { t: "Capabilities vs competitors" }] },
        { t: "Does it pay off?", c: [{ t: "Investment & breakeven" }, { t: "Cannibalisation & risks" }] }
      ]},
      keyPoints: [
        "Start from one crisp question: specific, measurable, time-bound ('How can we grow profit by 10% in 2 years?').",
        "Each level must be MECE; each leaf must be answerable.",
        "State your hypothesis aloud in the interview: 'My initial hypothesis is X, because Y — let me test that by looking at Z.'",
        "Prioritise: go first to the branch most likely to contain the answer (80/20)."
      ],
      pitfalls: [
        "Boiling the ocean — analysing every branch equally.",
        "Falling in love with your hypothesis; ignore data that disproves it and you fail the case.",
        "Leaves that are vague ('look at the market') instead of answerable."
      ],
      quiz: [
        { q: "Being 'hypothesis-driven' in a case means…", options: ["Guessing the answer and defending it no matter what", "Forming an early best guess, then testing and revising it with data", "Waiting for all data before forming a view", "Using the hypothesis from the interviewer"], answer: 1, explain: "A hypothesis focuses your analysis; data either confirms it or tells you to pivot." },
        { q: "Which is the best leaf for an issue tree?", options: ["Analyse the market", "Is the industry good?", "What % of revenue comes from customers lost in the last 12 months?", "Think about costs"], answer: 2, explain: "A good leaf is specific and answerable with data." },
        { q: "You've drawn a 3-branch tree. What do you do first?", options: ["Analyse branches left to right", "Ask the interviewer which branch they like", "Prioritise the branch most likely to explain the problem and say why", "Add more branches"], answer: 2, explain: "Prioritising (and explaining why) shows judgment — a core consulting skill." }
      ]
    },
    {
      id: "pyramid",
      group: "core",
      icon: "🔺",
      name: "Pyramid Principle",
      tagline: "Answer first. Then the reasons. Then the data.",
      intro: "Barbara Minto's Pyramid Principle is how consultants communicate: lead with the governing thought (the answer), support it with 2–4 grouped arguments, and support each argument with facts. Use it for your final recommendation, for emails, and for every slide title.",
      tree: { t: "Recommendation: Enter the Vietnam market via a JV", c: [
        { t: "The market is attractive", c: [{ t: "$2B, growing 12%/yr" }, { t: "Fragmented — top player has 8%" }] },
        { t: "We can win", c: [{ t: "Our cost per unit is 20% below locals" }, { t: "Partner brings distribution" }] },
        { t: "It pays back fast", c: [{ t: "Breakeven in year 2" }, { t: "NPV $45M at 10%" }] }
      ]},
      keyPoints: [
        "Synthesis structure: Recommendation → 3 reasons → Risks → Next steps.",
        "Ideas at any level summarise the ideas grouped below them.",
        "Use 'So what?' to climb up, 'Why?' / 'How?' to go down.",
        "Slide titles are full-sentence takeaways, not topics ('Costs rose 20% due to fuel', not 'Costs')."
      ],
      pitfalls: [
        "Recapping the whole case chronologically ('First we looked at…').",
        "Hedging with no answer ('It depends…'). Take a position; flag risks after.",
        "Too many supporting points — keep to 3."
      ],
      quiz: [
        { q: "The interviewer says 'The CEO just walked in — what do you tell her?' Your first sentence should be…", options: ["'We started by looking at revenue…'", "'We recommend closing the 40 unprofitable stores, which restores profit to $35M.'", "'There are several factors to consider.'", "'I need more data.'"], answer: 1, explain: "Answer first. The CEO wants the decision and the impact in one sentence." },
        { q: "In the Pyramid Principle, the supporting arguments should be…", options: ["As many as possible", "MECE and logically grouped (ideally 3)", "In the order you discovered them", "Only numbers"], answer: 1, explain: "Grouped, MECE, and few — so the listener can hold them in memory." },
        { q: "Which is the best slide title?", options: ["Revenue analysis", "Revenue by region", "Asia drove 80% of revenue decline, mostly from lost distributor contracts", "Q3 results"], answer: 2, explain: "Action titles state the takeaway — the 'so what'." }
      ]
    },
    {
      id: "profitability",
      group: "case",
      icon: "💰",
      name: "Profitability",
      tagline: "The most common case. Profit = (Price × Volume) − (Fixed + Variable costs).",
      intro: "Use it when the client's profits are falling, or they want to raise them. Quantify first: is the issue revenue, costs, or both? Then segment (by product, customer, channel, region) to locate the problem, then find the root cause, then recommend.",
      tree: { t: "Profit", c: [
        { t: "Revenue", c: [
          { t: "Price per unit", c: [{ t: "List price, discounts, mix" }] },
          { t: "Volume", c: [{ t: "Market size × market share" }] },
          { t: "Segment by product / customer / channel / region" }
        ]},
        { t: "Costs", c: [
          { t: "Fixed costs", c: [{ t: "Rent, salaries, D&A, overheads" }] },
          { t: "Variable costs", c: [{ t: "Cost per unit × volume (materials, labour, logistics)" }] }
        ]},
        { t: "External context", c: [{ t: "Market trends, competitors, regulation" }] }
      ]},
      keyPoints: [
        "Always ask: is this a company problem or an industry problem? (Compare to competitors.)",
        "Look at trends over time and as % of revenue — absolute numbers hide the story.",
        "Mix effects are a classic trap: overall margin falls because sales shift to low-margin products.",
        "Brainstorm levers in both directions: grow revenue AND cut cost."
      ],
      pitfalls: [
        "Diving into costs before checking whether revenue changed.",
        "Forgetting to segment — the average hides which product/region is broken.",
        "Ending with a list of ideas without prioritising by impact & feasibility."
      ],
      quiz: [
        { q: "Revenue is up 10%, profit is down 30%. Where do you look first?", options: ["Price", "Costs — which line grew faster than revenue", "Market share", "Competitor pricing"], answer: 1, explain: "If revenue grew yet profit fell, costs grew faster. Find the line item that outpaced revenue." },
        { q: "Average margin dropped though every product's margin is unchanged. Most likely cause?", options: ["Fixed costs rose", "Product mix shifted toward lower-margin products", "Prices fell", "Accounting error"], answer: 1, explain: "If each product's margin is stable, only the weights (mix) can move the average." },
        { q: "A firm sells 1M units at $20 with $12 variable cost and $5M fixed cost. Profit?", options: ["$3M", "$8M", "$13M", "$15M"], answer: 0, explain: "1M × ($20 − $12) = $8M contribution − $5M fixed = $3M." }
      ]
    },
    {
      id: "market-entry",
      group: "case",
      icon: "🚪",
      name: "Market Entry",
      tagline: "Should we enter? Is the market attractive, can we win, how do we enter, and does it pay?",
      intro: "Used when a client considers a new geography, segment, or industry. The four questions below make a tight, MECE structure. Finish with a clear go / no-go and the entry mode.",
      tree: { t: "Should the client enter market X?", c: [
        { t: "Market attractiveness", c: [{ t: "Size & growth" }, { t: "Profitability" }, { t: "Competition & concentration" }, { t: "Barriers: regulation, capital, access" }] },
        { t: "Client's ability to win", c: [{ t: "Customer needs vs our offer" }, { t: "Capabilities & right to win" }, { t: "Synergy with existing business" }] },
        { t: "Entry mode", c: [{ t: "Build (organic)" }, { t: "Buy (acquisition)" }, { t: "Partner (JV, licensing, alliance)" }] },
        { t: "Economics & risks", c: [{ t: "Investment, breakeven, ROI" }, { t: "Competitor reaction, execution risk" }] }
      ]},
      keyPoints: [
        "Build = control, slow. Buy = fast, expensive, integration risk. Partner = fast & cheap, shared control.",
        "Ask about the client's objective and timeline — it often decides the entry mode.",
        "Compute breakeven (fixed investment ÷ contribution per unit) — interviewers love it.",
        "Think about incumbent reaction: price war? lobbying?"
      ],
      pitfalls: [
        "Only analysing the market and forgetting whether the client can win.",
        "Recommending 'enter' without saying how.",
        "Ignoring regulation in banking, pharma, telecom."
      ],
      quiz: [
        { q: "The client needs to be in the market within 6 months and has lots of cash. Best entry mode?", options: ["Build", "Buy", "Wait", "License the brand only"], answer: 1, explain: "Speed + cash point to acquisition; building takes years." },
        { q: "Investment $10M, contribution per unit $50. Breakeven volume?", options: ["20,000", "200,000", "2,000,000", "500,000"], answer: 1, explain: "$10,000,000 ÷ $50 = 200,000 units." },
        { q: "Which is NOT a market attractiveness factor?", options: ["Market growth", "Competitive intensity", "Our brand strength", "Average industry margin"], answer: 2, explain: "Our brand strength is about the client's ability to win, not the market itself." }
      ]
    },
    {
      id: "mna",
      group: "case",
      icon: "🤝",
      name: "Mergers & Acquisitions",
      tagline: "Should we buy this company — and at what price?",
      intro: "M&A cases test strategic logic plus valuation basics. Start with the rationale (why buy?), assess the target on its own, then synergies, then price vs value, then risks. Distinguish strategic buyers (synergies) from financial buyers (PE: returns, leverage, exit).",
      tree: { t: "Should the client acquire Target?", c: [
        { t: "Strategic rationale", c: [{ t: "Growth, capabilities, market access, defence" }] },
        { t: "Target standalone", c: [{ t: "Market: size, growth, position" }, { t: "Financials: revenue, margins, cash flow" }, { t: "Management & culture" }] },
        { t: "Synergies", c: [{ t: "Revenue: cross-sell, new channels" }, { t: "Cost: procurement, overheads, footprint" }] },
        { t: "Valuation & deal", c: [{ t: "Standalone value (multiples, DCF)" }, { t: "+ Synergies − integration costs" }, { t: "vs Asking price" }] },
        { t: "Risks & alternatives", c: [{ t: "Integration, regulatory/antitrust, culture" }, { t: "Build or partner instead?" }] }
      ]},
      keyPoints: [
        "Enterprise Value ≈ EBITDA × comparable multiple (quick-and-dirty in interviews).",
        "Don't pay away all synergies — they're uncertain and you're the one creating them.",
        "Cost synergies are more reliable than revenue synergies.",
        "PE angle: entry price, leverage, operational improvements, exit multiple, 3–7 year horizon."
      ],
      pitfalls: [
        "Saying yes just because the target is profitable — the question is whether price < value.",
        "Ignoring integration costs and timing of synergies.",
        "Forgetting antitrust in concentrated markets."
      ],
      quiz: [
        { q: "Target EBITDA $40M, sector multiple 8×. Rough standalone value?", options: ["$48M", "$320M", "$400M", "$5M"], answer: 1, explain: "$40M × 8 = $320M." },
        { q: "Which synergies are typically more reliable?", options: ["Revenue synergies", "Cost synergies", "Both equally", "Neither"], answer: 1, explain: "Cost synergies (closing duplicate offices, procurement) are more within the buyer's control." },
        { q: "Value = $300M standalone + $50M synergies. Seller asks $360M. Best response?", options: ["Accept", "Walk away immediately", "Negotiate down — at $360M you pay away more than all synergies", "Offer $400M to secure the deal"], answer: 2, explain: "Above $350M you destroy value. Negotiate to share the synergies, or walk." }
      ]
    },
    {
      id: "market-sizing",
      group: "case",
      icon: "📏",
      name: "Market Sizing",
      tagline: "Estimate anything with a clear, logical chain of assumptions.",
      intro: "Market sizing tests structured thinking and comfortable math — not knowing the real number. Choose top-down (population → segments → usage) or bottom-up (units × price from the supply side), state assumptions clearly, round aggressively, and sanity-check at the end.",
      tree: { t: "Annual market for product X", c: [
        { t: "Top-down (demand side)", c: [{ t: "Population" }, { t: "× % target segment" }, { t: "× % who buy / adoption" }, { t: "× units per year" }, { t: "× price per unit" }] },
        { t: "Bottom-up (supply side)", c: [{ t: "# outlets / producers" }, { t: "× capacity or sales per outlet" }, { t: "× price" }] },
        { t: "Sanity check", c: [{ t: "Compare with a known number (GDP, a competitor's revenue)" }] }
      ]},
      keyPoints: [
        "Say your structure before you calculate — the logic matters more than the result.",
        "Use round numbers: 330M → 300M; 52 weeks → 50.",
        "Segment where it changes the answer (households vs businesses, urban vs rural).",
        "Market value = units × price. Clarify whether they want units or revenue."
      ],
      pitfalls: [
        "Jumping into numbers without a structure.",
        "Losing track of zeros — write units at every step.",
        "No sanity check, so a 1,000× error goes unnoticed."
      ],
      quiz: [
        { q: "100M people, 60% adults, 1/3 of adults drink coffee daily, 1 cup/day, 350 days. Cups per year?", options: ["7 billion", "21 billion", "2.1 billion", "70 billion"], answer: 0, explain: "100M × 0.6 = 60M adults × 1/3 = 20M drinkers × 350 ≈ 7B cups." },
        { q: "Which approach sizes 'number of taxi rides per day in a city' from the supply side?", options: ["Population × trips per person", "# taxis × rides per taxi per day", "GDP × % on transport", "Tourists × days"], answer: 1, explain: "Supply side = number of taxis × rides each can do per shift." },
        { q: "The most important thing in a market-sizing question is…", options: ["Getting the exact number", "A clear, logical structure with explicit assumptions", "Using many decimal places", "Knowing industry reports"], answer: 1, explain: "Interviewers grade the approach and communication, not the decimal." }
      ]
    },
    {
      id: "pricing",
      group: "case",
      icon: "🏷️",
      name: "Pricing",
      tagline: "Cost-based, competitor-based, value-based — triangulate to a price.",
      intro: "Pricing cases ask how to price a new product or whether to change an existing price. Triangulate three anchors: the cost floor, competitor reference points, and the customer's willingness to pay (value). Then align with strategic objectives (share vs margin) and test volume impact.",
      tree: { t: "What price should we set?", c: [
        { t: "Cost-based (floor)", c: [{ t: "Unit cost + target margin" }, { t: "Breakeven volume at each price" }] },
        { t: "Competitor-based (reference)", c: [{ t: "Competitor prices & positioning" }, { t: "Substitutes" }, { t: "Likely competitor reaction" }] },
        { t: "Value-based (ceiling)", c: [{ t: "Economic value to customer (savings, gains)" }, { t: "Willingness to pay by segment" }] },
        { t: "Strategy", c: [{ t: "Objective: share vs margin (penetration vs skimming)" }, { t: "Tiers, bundles, discounts" }] }
      ]},
      keyPoints: [
        "Price floor = cost; price ceiling = customer value. The right price sits between.",
        "For price changes, compute breakeven churn: the % of volume you can lose before revenue falls.",
        "Price elasticity: % change in quantity ÷ % change in price.",
        "Segmentation (good / better / best tiers) captures more value than one price."
      ],
      pitfalls: [
        "Only using cost-plus — leaves money on the table for high-value products.",
        "Ignoring how competitors will react.",
        "Forgetting cannibalisation of the client's own products."
      ],
      quiz: [
        { q: "A machine saves a factory $100k/yr for 5 years. Competitors' machines cost $200k. Cost to make is $80k. Value-based ceiling?", options: ["$80k", "$200k", "~$500k (before discounting)", "$100k"], answer: 2, explain: "Customer value is ~5 × $100k = $500k (less with discounting). That's the ceiling; competitor price and cost are lower anchors." },
        { q: "Raising price from $10 to $12. Max % of customers you can lose before revenue falls?", options: ["10%", "16.7%", "20%", "25%"], answer: 1, explain: "Breakeven: 1 − 10/12 = 16.7%." },
        { q: "Launching a new tech product to grab share fast before competitors arrive suggests…", options: ["Skimming price", "Penetration price", "Cost-plus price", "Random pricing"], answer: 1, explain: "Penetration pricing: low price to win share quickly." }
      ]
    },
    {
      id: "growth",
      group: "case",
      icon: "📈",
      name: "Growth Strategy (Ansoff)",
      tagline: "Grow via existing or new products, in existing or new markets — organically or inorganically.",
      intro: "When the client asks 'How do we grow revenue by X%?', use Ansoff's matrix to cover every growth avenue, then decide build vs buy vs partner. Quantify the gap first: how much growth do we need, and how much can each lever deliver?",
      tree: { t: "How can the client grow revenue 20% in 3 years?", c: [
        { t: "Existing products, existing markets", c: [{ t: "Market penetration: share, pricing, frequency" }] },
        { t: "New products, existing markets", c: [{ t: "Product development, cross-sell, upsell" }] },
        { t: "Existing products, new markets", c: [{ t: "Market development: new regions, segments, channels" }] },
        { t: "New products, new markets", c: [{ t: "Diversification (riskiest)" }] },
        { t: "How: organic vs inorganic", c: [{ t: "Build, acquire, partner" }] }
      ]},
      keyPoints: [
        "Risk rises as you move away from the core (penetration → diversification).",
        "Size each lever and add them up to see if they close the growth gap.",
        "Prioritise by impact × feasibility × time-to-revenue."
      ],
      pitfalls: [
        "Listing ideas without sizing them.",
        "Defaulting to acquisitions without checking organic options.",
        "Forgetting capability fit — new markets need new skills."
      ],
      quiz: [
        { q: "A bank starts selling insurance to its existing deposit customers. Which Ansoff quadrant?", options: ["Market penetration", "Product development", "Market development", "Diversification"], answer: 1, explain: "New product (insurance) to existing customers = product development." },
        { q: "Which quadrant is generally riskiest?", options: ["Market penetration", "Product development", "Market development", "Diversification"], answer: 3, explain: "New products in new markets — the furthest from current capabilities." },
        { q: "First step in a growth case?", options: ["List acquisition targets", "Quantify the growth gap and the baseline trajectory", "Cut costs", "Raise prices"], answer: 1, explain: "Know how much growth is needed versus where you're heading anyway." }
      ]
    },
    {
      id: "five-forces",
      group: "case",
      icon: "⚔️",
      name: "Porter's Five Forces",
      tagline: "How attractive (profitable) is an industry?",
      intro: "Five forces explain why some industries earn higher margins than others. Use it as one branch of a market-entry or industry-analysis case — rarely as a whole case structure on its own.",
      tree: { t: "Industry attractiveness", c: [
        { t: "Rivalry among competitors", c: [{ t: "Number, concentration, growth, exit barriers" }] },
        { t: "Threat of new entrants", c: [{ t: "Capital needs, regulation, scale, brand" }] },
        { t: "Bargaining power of suppliers", c: [{ t: "Supplier concentration, switching costs" }] },
        { t: "Bargaining power of buyers", c: [{ t: "Buyer concentration, price sensitivity" }] },
        { t: "Threat of substitutes", c: [{ t: "Alternatives that meet the same need" }] }
      ]},
      keyPoints: [
        "Strong forces = lower profits. Weak forces = attractive industry.",
        "Tie each force to a 'so what' for the client.",
        "Combine with company-specific analysis — an attractive industry doesn't mean the client can win."
      ],
      pitfalls: [
        "Reciting all five forces mechanically with no conclusion.",
        "Using it as the only framework in a profitability case."
      ],
      quiz: [
        { q: "Airlines buy jets from essentially two manufacturers. That's high…", options: ["Buyer power", "Supplier power", "Threat of substitutes", "Rivalry"], answer: 1, explain: "Concentrated suppliers (Airbus, Boeing) have strong bargaining power." },
        { q: "Video calls replacing business travel is an example of…", options: ["New entrants", "Substitutes", "Buyer power", "Supplier power"], answer: 1, explain: "A different product meeting the same need = substitute." },
        { q: "Banking licences are hard to get. This lowers…", options: ["Threat of new entrants", "Rivalry", "Supplier power", "Buyer power"], answer: 0, explain: "Regulatory barriers protect incumbents from new entrants." }
      ]
    },
    {
      id: "product-launch",
      group: "case",
      icon: "🚀",
      name: "3Cs & 4Ps (Product Launch)",
      tagline: "Understand Customers, Company, Competitors — then design Product, Price, Place, Promotion.",
      intro: "For a new product launch or marketing case, first analyse the situation with the 3Cs, then design the go-to-market plan with the 4Ps. It's a natural two-step structure: diagnose, then decide.",
      tree: { t: "How should we launch product X?", c: [
        { t: "3Cs — situation", c: [{ t: "Customers: segments, needs, willingness to pay" }, { t: "Company: capabilities, brand, capacity" }, { t: "Competitors: offers, share, likely reaction" }] },
        { t: "4Ps — plan", c: [{ t: "Product: features, positioning" }, { t: "Price: strategy & level" }, { t: "Place: channels, distribution" }, { t: "Promotion: messaging, media, budget" }] },
        { t: "Economics", c: [{ t: "Volume forecast, breakeven, cannibalisation" }] }
      ]},
      keyPoints: [
        "Pick a target segment before designing the 4Ps — one product can't please everyone.",
        "Channel choice often determines margins (direct vs retail vs online).",
        "Always check cannibalisation of the client's existing products."
      ],
      pitfalls: [
        "Jumping to promotion ideas before understanding the customer.",
        "Ignoring the client's capability to manufacture or distribute."
      ],
      quiz: [
        { q: "Which of these is one of the 3Cs?", options: ["Cost", "Competitors", "Channels", "Capital"], answer: 1, explain: "Customers, Company, Competitors." },
        { q: "'Sell via supermarkets or online only?' is a decision about…", options: ["Product", "Price", "Place", "Promotion"], answer: 2, explain: "Place = distribution channels." },
        { q: "What should you define first in a launch case?", options: ["The ad budget", "The target customer segment", "The package colour", "The discount level"], answer: 1, explain: "Everything else (product, price, channel, message) depends on who you're targeting." }
      ]
    },
    {
      id: "cost-reduction",
      group: "case",
      icon: "✂️",
      name: "Operations & Cost Reduction",
      tagline: "Map the value chain, benchmark each step, attack the biggest gaps.",
      intro: "When the client must cut costs (or fix a slow/broken process), break total cost down along the value chain, benchmark each component against peers or best practice, and prioritise levers by size and ease. Distinguish one-off from structural savings.",
      tree: { t: "How can the client cut costs by 15%?", c: [
        { t: "Map the cost base", c: [{ t: "By value-chain step: sourcing → production → logistics → sales → support" }, { t: "Fixed vs variable" }] },
        { t: "Benchmark", c: [{ t: "vs competitors" }, { t: "vs own best units / history" }] },
        { t: "Levers", c: [{ t: "Spend less: renegotiate, consolidate suppliers" }, { t: "Use less: process redesign, automation, lean" }, { t: "Structure: footprint, outsourcing, spans & layers" }] },
        { t: "Implementation", c: [{ t: "Savings vs one-off costs, timing, risks to quality / morale" }] }
      ]},
      keyPoints: [
        "Go after the biggest cost buckets first — 5% of a big bucket beats 50% of a tiny one.",
        "Price × quantity applies to costs too: pay less per unit, or use fewer units.",
        "For process cases, find the bottleneck — the slowest step sets the throughput."
      ],
      pitfalls: [
        "Proposing across-the-board cuts without diagnosis.",
        "Ignoring impact on customers, quality, and employees."
      ],
      quiz: [
        { q: "Cost base: labour $60M, materials $30M, IT $5M. Where do you look first?", options: ["IT", "Materials", "Labour", "All equally"], answer: 2, explain: "Start with the biggest bucket — that's where meaningful savings are." },
        { q: "A factory line: step A 10 units/hr, step B 6 units/hr, step C 12 units/hr. Throughput?", options: ["6/hr", "10/hr", "12/hr", "28/hr"], answer: 0, explain: "The bottleneck (step B) caps output at 6/hr." },
        { q: "'Use less' cost levers include…", options: ["Renegotiating supplier prices", "Reducing waste through process redesign", "Changing currency", "Raising prices"], answer: 1, explain: "Using less = lower quantity consumed; renegotiating = paying less per unit." }
      ]
    }
  ],

  /* ------------------------------------------------------------------ */
  cases: [
    {
      id: "coffee",
      icon: "☕",
      title: "Brewed Awakening",
      type: "Profitability",
      difficulty: 1,
      client: "Regional coffee-shop chain",
      prompt: "Our client, Brewed Awakening, runs 220 coffee shops. Over the last two years revenue grew from $400M to $440M, yet operating profit fell from $40M to $28M. The CEO wants to know why profits are falling and what to do about it.",
      steps: [
        {
          kind: "mcq",
          title: "Clarify",
          question: "What's the most useful clarifying question to ask first?",
          options: [
            { text: "What's the CEO's favourite drink?", feedback: "Friendly, but it doesn't help you solve the case." },
            { text: "Is the profit decline specific to us, or are competitors seeing the same thing — and what profit target does the CEO have in mind?", correct: true, feedback: "Great — it separates company vs industry issues and pins down the objective." },
            { text: "Can you give me every number you have?", feedback: "Too broad. Ask targeted questions so you control the case." },
            { text: "Should we close stores?", feedback: "Jumping to a solution before understanding the problem." }
          ],
          reveal: "Interviewer: Competitors' margins have been roughly stable, so this looks specific to our client. The CEO wants margins back to 2023 levels (10%)."
        },
        {
          kind: "mcq",
          title: "Structure",
          question: "Which structure is the best starting point?",
          options: [
            { text: "Porter's Five Forces", feedback: "Competitors are fine, so industry structure isn't the issue. Too external." },
            { text: "Profit = Revenue (price × volume, by segment) − Costs (fixed + variable)", correct: true, feedback: "Exactly — a classic profitability tree, MECE by construction." },
            { text: "4Ps marketing mix", feedback: "Useful for a launch, not to diagnose a profit decline." },
            { text: "SWOT analysis", feedback: "SWOT isn't MECE or quantitative enough for this." }
          ],
          reveal: "Revenue grew 10%, so you go to costs. The interviewer hands you an exhibit."
        },
        {
          kind: "math",
          title: "Exhibit 1 — Cost breakdown",
          exhibit: { caption: "Brewed Awakening P&L ($M)", headers: ["Line", "2023", "2025"], rows: [["Revenue", "400", "440"], ["Cost of goods (ingredients, cups)", "120", "143"], ["Store labour", "120", "135"], ["Rent", "80", "90"], ["Marketing & other", "40", "44"], ["Operating profit", "40", "28"]] },
          question: "What was cost of goods as a % of revenue in 2025? (2023 was 30%.) Enter a number, e.g. 31.2",
          answer: 32.5,
          tolerance: 0.3,
          unit: "%",
          explain: "143 ÷ 440 = 32.5%. Labour (30.7%), rent (20.5%) and other (10%) moved roughly with revenue; cost of goods jumped 2.5 points — that's $11M of the $12M profit drop (2.5% × 440)."
        },
        {
          kind: "mcq",
          title: "Exhibit 2 — Find the root cause",
          exhibit: { caption: "Revenue mix and cost of goods by category", headers: ["Category", "Share of revenue 2023", "Share of revenue 2025", "COGS % of price"], rows: [["Hot coffee & tea", "85%", "65%", "28%"], ["Iced specialty drinks", "15%", "35%", "40%"]] },
          question: "What is driving the rise in cost of goods?",
          options: [
            { text: "Suppliers raised coffee bean prices", feedback: "Each category's COGS % is unchanged, so input prices aren't the story." },
            { text: "A mix shift toward iced specialty drinks, which carry a much higher ingredient cost", correct: true, feedback: "Yes. 0.85×28% + 0.15×40% ≈ 30% → 0.65×28% + 0.35×40% ≈ 32%. The mix explains the jump." },
            { text: "Theft in stores", feedback: "Nothing in the data points to shrinkage." },
            { text: "The new stores are inefficient", feedback: "The exhibit is about product mix, not store vintage." }
          ],
          reveal: "Interviewer: Correct. Iced drinks are popular with younger customers, but they're priced only $0.30 above hot drinks while using syrups, milk alternatives, and premium cups."
        },
        {
          kind: "multi",
          title: "Brainstorm levers",
          question: "Select ALL the levers that directly address the root cause.",
          options: [
            { text: "Re-price iced specialty drinks closer to customer willingness to pay", correct: true },
            { text: "Renegotiate syrup, milk-alternative and cup costs / standardise recipes", correct: true },
            { text: "Stop selling iced drinks altogether", correct: false },
            { text: "Promote high-margin add-ons (pastries, larger sizes) with iced drinks", correct: true },
            { text: "Cut store opening hours by 30%", correct: false }
          ],
          explain: "Attack price and unit cost of the growing product, and lift basket margin. Killing the category or slashing hours would lose the customers who drive growth."
        },
        {
          kind: "mcq",
          title: "Synthesis",
          question: "The CEO walks in. Which recommendation do you give?",
          options: [
            { text: "We looked at revenue, then costs, then the mix, and found several interesting things…", feedback: "Chronological recap — lead with the answer instead." },
            { text: "Profit fell because customers shifted to iced drinks that are under-priced for their ~40% ingredient cost. Raise iced-drink prices ~$0.50, cut their ingredient cost via supplier renegotiation, and bundle high-margin add-ons — restoring ~$11M of profit. Risk: price sensitivity among younger customers, so test in 20 stores first.", correct: true, feedback: "Answer first, quantified, with reasons, risk, and next step. Partner-ready." },
            { text: "It's complicated; we need more data before saying anything.", feedback: "Always give a recommendation with what you have, then flag next steps." },
            { text: "Close the least profitable 50 stores.", feedback: "Not supported by the analysis — the issue is product mix, not specific stores." }
          ]
        }
      ],
      modelAnswer: "Profits fell $12M because sales shifted from hot coffee (28% COGS) to iced specialty drinks (40% COGS), raising cost of goods from 30% to 32.5% of revenue. Recommend re-pricing iced drinks, renegotiating their inputs, and bundling high-margin add-ons, piloted in a subset of stores."
    },
    {
      id: "bank-digital",
      icon: "🏦",
      title: "Nusantara Bank Goes Digital",
      type: "Market Entry",
      difficulty: 2,
      client: "Mid-size Indonesian commercial bank",
      prompt: "Nusantara Bank is a mid-size Indonesian bank focused on corporate clients. Its board is considering launching a digital lending app for small businesses (MSMEs). They ask: should we enter this market, and if so, how? (All figures are illustrative.)",
      steps: [
        {
          kind: "mcq",
          title: "Structure",
          question: "Which structure best fits this question?",
          options: [
            { text: "Market attractiveness → Bank's ability to win → Entry mode (build / buy / partner) → Economics & risks", correct: true, feedback: "Textbook market-entry structure that ends in a decision and a 'how'." },
            { text: "Revenue − Costs", feedback: "Useful later for economics, but it misses whether the market is attractive and how to enter." },
            { text: "Ansoff matrix only", feedback: "Ansoff tells you this is 'market development', but not whether to do it." },
            { text: "STAR method", feedback: "That's for behavioural questions!" }
          ],
          reveal: "Interviewer: Good. Let's start with the size of the opportunity."
        },
        {
          kind: "math",
          title: "Size the market",
          exhibit: { caption: "Assumptions", headers: ["Item", "Value"], rows: [["Number of MSMEs", "60 million"], ["Share that are digitally active AND need credit", "20%"], ["Average loan per business per year", "Rp 50 million"]] },
          question: "What is the annual loan demand from this segment, in Rp trillion?",
          answer: 600,
          tolerance: 1,
          unit: "Rp T",
          explain: "60M × 20% = 12M businesses × Rp 50M = Rp 600 trillion per year. A huge pool — though banks currently serve only a fraction of it."
        },
        {
          kind: "math",
          title: "Breakeven",
          exhibit: { caption: "Unit economics per active loan per year", headers: ["Item", "Value"], rows: [["Net interest + fee income", "Rp 3.0 million"], ["Expected credit losses", "Rp 1.0 million"], ["Servicing & acquisition cost", "Rp 0.5 million"], ["Platform build + annual fixed costs", "Rp 300 billion / year"]] },
          question: "How many active loans does the bank need to break even each year? (Answer in thousands, e.g. 150)",
          answer: 200,
          tolerance: 1,
          unit: "k loans",
          explain: "Contribution per loan = 3.0 − 1.0 − 0.5 = Rp 1.5M. Breakeven = Rp 300B ÷ Rp 1.5M = 200,000 loans — about 1.7% of the 12M target businesses."
        },
        {
          kind: "mcq",
          title: "Ability to win",
          exhibit: { caption: "What we learn about the bank and the market", headers: ["Fact", ""], rows: [["Bank's MSME credit-scoring experience", "Very limited"], ["Bank's funding cost vs fintechs", "~3 pts cheaper (deposit base)"], ["Time to build an app in-house", "~24 months"], ["Leading fintech lenders", "Strong data & UX, but expensive funding"]] },
          question: "Given this, which entry mode makes most sense?",
          options: [
            { text: "Build everything in-house", feedback: "24 months is slow, and the bank lacks MSME scoring know-how — big execution risk." },
            { text: "Partner with (or acquire a stake in) a fintech lender: the bank provides cheap funding, the fintech provides scoring, data and UX", correct: true, feedback: "Combines each side's strength — cheap funding meets proven risk models — and gets to market fast." },
            { text: "Don't enter; stay in corporate banking", feedback: "The market is large and the bank has a real funding advantage. Walking away ignores that." },
            { text: "Launch a marketing campaign first", feedback: "Without a product and a scoring engine there's nothing to sell." }
          ],
          reveal: "Interviewer: Makes sense. Several fintechs are open to channeling/joint-financing partnerships with banks."
        },
        {
          kind: "multi",
          title: "Risks",
          question: "Select ALL the key risks you'd flag to the board.",
          options: [
            { text: "Credit risk: MSME default rates could exceed the 1.0M loss assumption", correct: true },
            { text: "Regulatory requirements from the financial regulator on digital lending & partnerships", correct: true },
            { text: "Partner dependency / misaligned incentives (fintech originates, bank holds the risk)", correct: true },
            { text: "The bank's logo colour", correct: false },
            { text: "Cannibalising the bank's corporate loan book", correct: false }
          ],
          explain: "Credit, regulatory and partnership-alignment risks matter most. MSME lending barely overlaps with corporate clients, so cannibalisation is minor."
        },
        {
          kind: "mcq",
          title: "Recommendation",
          question: "What do you tell the board?",
          options: [
            { text: "Enter, via a funding partnership with a leading fintech lender. The market is ~Rp 600T/yr, we need only ~200k loans (<2% of target firms) to break even, and our funding cost advantage is a real edge. Start with a capped pilot book, with risk-sharing terms so the partner keeps skin in the game; scale after 12 months if losses stay below plan.", correct: true, feedback: "Clear go/no-go, the 'how', the numbers, the risk mitigation and the next step." },
            { text: "The market is big, so enter.", feedback: "Right direction but no entry mode, no numbers, no risks." },
            { text: "Build our own app over 24 months to keep full control.", feedback: "Contradicts the analysis on speed and capability." },
            { text: "We need more research.", feedback: "Give the best answer now; next steps can include research." }
          ]
        }
      ],
      modelAnswer: "Enter MSME digital lending through a funding partnership with an established fintech: large market (~Rp 600T/yr), achievable breakeven (~200k loans), and the bank's cheap deposit funding complements the fintech's scoring and UX. Mitigate credit and partner risk with risk-sharing and a capped pilot."
    },
    {
      id: "screen-protector",
      icon: "📱",
      title: "Screen Protector Market",
      type: "Market Sizing",
      difficulty: 1,
      client: "Accessories manufacturer",
      prompt: "A phone-accessories manufacturer is considering entering a country with 100 million people. Before anything else, they want to know: how big is the annual market for smartphone screen protectors, in dollars?",
      steps: [
        {
          kind: "mcq",
          title: "Approach",
          question: "Which approach is the cleanest?",
          options: [
            { text: "Top-down: population → smartphone users → % using protectors → replacements per year → price", correct: true, feedback: "Logical demand-side chain with easy-to-estimate assumptions." },
            { text: "Count every phone shop in the country", feedback: "Possible (supply side) but much harder to estimate here." },
            { text: "Take GDP and assume 0.01% goes to screen protectors", feedback: "No logic behind the 0.01% — the interviewer will push back." },
            { text: "Guess $1 billion", feedback: "Show your structure; a guess isn't an answer." }
          ]
        },
        {
          kind: "math",
          title: "Units",
          exhibit: { caption: "Your assumptions (agreed with the interviewer)", headers: ["Driver", "Assumption"], rows: [["Population", "100M"], ["Smartphone users", "70% of population"], ["Users who use a screen protector", "50%"], ["Protectors bought per user per year", "1.5"]] },
          question: "How many screen protectors are sold per year? (in millions)",
          answer: 52.5,
          tolerance: 0.5,
          unit: "M units",
          explain: "100M × 70% = 70M users × 50% = 35M × 1.5 = 52.5M units per year."
        },
        {
          kind: "math",
          title: "Value",
          question: "The average price is $5. What's the market value in $ millions?",
          answer: 262.5,
          tolerance: 3,
          unit: "$M",
          explain: "52.5M × $5 ≈ $260M per year. Round it: 'roughly a quarter of a billion dollars'."
        },
        {
          kind: "mcq",
          title: "Sanity check",
          question: "How would you best sanity-check the ~$260M figure?",
          options: [
            { text: "It's ~$2.6 per person per year — plausible for a cheap, frequently replaced accessory", correct: true, feedback: "Per-capita checks are fast and convincing." },
            { text: "Redo the same calculation", feedback: "Repeating the math doesn't test the assumptions." },
            { text: "Ask the interviewer if it's right", feedback: "Own your number; show a sanity check instead." },
            { text: "No need to check", feedback: "Always sanity-check — it catches order-of-magnitude errors." }
          ]
        },
        {
          kind: "multi",
          title: "Refine",
          question: "Which refinements would most improve the estimate? (Select all that apply.)",
          options: [
            { text: "Segment by premium vs budget phones (different protector prices and usage)", correct: true },
            { text: "Split urban vs rural adoption", correct: true },
            { text: "Account for protectors pre-installed by phone makers", correct: true },
            { text: "Add the price of the phone itself", correct: false }
          ],
          explain: "Segmenting where behaviour differs makes the estimate sharper. The phone's price isn't part of this market."
        }
      ],
      modelAnswer: "≈ 52.5M units/yr × $5 ≈ $260M/yr (≈ $2.6 per person — plausible). Refine by phone tier, urban/rural split, and OEM pre-installed protectors."
    },
    {
      id: "gym-pe",
      icon: "🏋️",
      title: "FitNation Buyout",
      type: "M&A / Private Equity",
      difficulty: 3,
      client: "Private-equity fund",
      prompt: "A private-equity fund is considering acquiring FitNation, a chain of 150 mid-price gyms. The seller is asking $600M. The fund wants to know whether to buy and at what price.",
      steps: [
        {
          kind: "mcq",
          title: "Structure",
          question: "What's the best set of buckets?",
          options: [
            { text: "Market attractiveness → FitNation's standalone performance → Value-creation plan (synergies / operational improvements) → Valuation vs price → Risks & exit", correct: true, feedback: "Covers the market, the asset, how PE adds value, the price, and the exit." },
            { text: "Customers, Company, Competitors", feedback: "3Cs is for marketing; it misses valuation and exit." },
            { text: "Revenue minus costs", feedback: "Too narrow — misses price, value creation and exit." },
            { text: "Five Forces only", feedback: "Useful for one branch (market) but not the decision." }
          ]
        },
        {
          kind: "math",
          title: "Implied multiple",
          exhibit: { caption: "FitNation financials", headers: ["Item", "Value"], rows: [["Revenue", "$300M"], ["EBITDA", "$50M"], ["Comparable gym deals (EV / EBITDA)", "9× – 11×"]] },
          question: "What EV/EBITDA multiple does the $600M asking price imply? (e.g. 10.5)",
          answer: 12,
          tolerance: 0.05,
          unit: "×",
          explain: "$600M ÷ $50M = 12× — above the 9–11× range of comparable deals. At a 10× midpoint, standalone value ≈ $500M."
        },
        {
          kind: "math",
          title: "Value-creation plan",
          exhibit: { caption: "Operational improvements identified", headers: ["Initiative", "Annual EBITDA uplift"], rows: [["Centralise procurement (equipment, energy)", "$4M"], ["Dynamic membership pricing", "$6M"], ["Close 10 loss-making clubs", "$2M"]] },
          question: "If all improvements are achieved, what's the EBITDA (in $M)? At a 10× multiple, what is the value in $M? Enter the value.",
          answer: 620,
          tolerance: 1,
          unit: "$M",
          explain: "50 + 4 + 6 + 2 = $62M EBITDA × 10 = $620M. But that's only if everything works — and the fund would be paying the seller for value the fund itself has to create."
        },
        {
          kind: "mcq",
          title: "Price discipline",
          question: "Should the fund pay $600M?",
          options: [
            { text: "Yes — post-improvement value is $620M, which is above $600M", feedback: "That pays away almost all the upside for value you still need to create, with execution risk. Little margin for error." },
            { text: "Bid around standalone value (~$500–550M), sharing only part of the improvement upside; walk away above ~$560M", correct: true, feedback: "Price discipline: pay for what exists, keep most of what you'll create." },
            { text: "Offer $650M to make sure we win", feedback: "Overpaying is the #1 way PE funds lose money." },
            { text: "Walk away — gyms are a bad business", feedback: "Too absolute — at the right price the deal can work." }
          ]
        },
        {
          kind: "multi",
          title: "Risks",
          question: "Select ALL the risks that matter most for this deal.",
          options: [
            { text: "Membership churn rises if dynamic pricing is perceived as unfair", correct: true },
            { text: "Low-cost and boutique competitors squeezing mid-price gyms", correct: true },
            { text: "Exit multiple contracts from 10× to 8× by the time the fund sells", correct: true },
            { text: "Leverage: debt service if a downturn cuts memberships", correct: true },
            { text: "Gym equipment colour schemes", correct: false }
          ],
          explain: "Pricing backlash, competitive squeeze, multiple contraction and leverage are the real swing factors in a gym buyout."
        },
        {
          kind: "mcq",
          title: "Recommendation",
          question: "Your final answer to the investment committee?",
          options: [
            { text: "Pursue, but not at $600M (12×, above the 9–11× comps). Bid ~$525M (10.5×). Our plan lifts EBITDA from $50M to ~$62M via procurement, pricing and closing 10 clubs. Key risks: churn from pricing, mid-market squeeze, exit multiple. Next: diligence on churn data and the 10 clubs' leases.", correct: true, feedback: "Decision + price + value logic + risks + next steps. That's a partner-level answer." },
            { text: "Buy at $600M, the gyms are great", feedback: "Ignores valuation discipline." },
            { text: "Gyms are interesting. There are many factors.", feedback: "No decision." },
            { text: "Don't buy — the multiple is high", feedback: "Partly right, but you can negotiate rather than walk." }
          ]
        }
      ],
      modelAnswer: "Asking price implies 12× EBITDA vs 9–11× comps. The value-creation plan could lift EBITDA to ~$62M (≈ $620M at 10×), but the fund shouldn't pay that away. Bid ~$500–550M, walk away above ~$560M, and diligence churn and club leases."
    },
    {
      id: "stream-pricing",
      icon: "📺",
      title: "StreamCo Price Hike",
      type: "Pricing",
      difficulty: 2,
      client: "Video-streaming service",
      prompt: "StreamCo has 10 million subscribers paying $10/month. Management wants to raise the price to $12. Marketing research estimates 12% of subscribers would cancel. Should they do it?",
      steps: [
        {
          kind: "math",
          title: "Current revenue",
          question: "What is StreamCo's current monthly revenue, in $M?",
          answer: 100,
          tolerance: 0.5,
          unit: "$M / mo",
          explain: "10M × $10 = $100M per month."
        },
        {
          kind: "math",
          title: "Revenue after the hike",
          question: "If 12% cancel, what's monthly revenue at $12, in $M?",
          answer: 105.6,
          tolerance: 0.3,
          unit: "$M / mo",
          explain: "10M × 88% = 8.8M subscribers × $12 = $105.6M — up $5.6M (+5.6%)."
        },
        {
          kind: "math",
          title: "Breakeven churn",
          question: "What % of subscribers could cancel before revenue falls below today's level? (one decimal)",
          answer: 16.7,
          tolerance: 0.2,
          unit: "%",
          explain: "Breakeven when (1 − x) × 12 = 10 → x = 1 − 10/12 = 16.7%. The 12% estimate gives a cushion of ~4.7 points."
        },
        {
          kind: "mcq",
          title: "Look beyond the math",
          question: "What's the most important thing the simple math misses?",
          options: [
            { text: "Lifetime value: cancellers may never return, and fewer subscribers can mean less content leverage and word-of-mouth", correct: true, feedback: "Yes — a one-month snapshot ignores long-term subscriber value and network effects." },
            { text: "The colour of the 'subscribe' button", feedback: "Not a strategic issue." },
            { text: "Nothing — the math settles it", feedback: "Revenue up today doesn't guarantee value up over time." },
            { text: "Exchange rates", feedback: "Not relevant for a single-market price decision." }
          ]
        },
        {
          kind: "mcq",
          title: "Better option?",
          question: "Which pricing design likely captures more value than a flat increase?",
          options: [
            { text: "Tiered plans: an ad-supported $8 tier, Standard at $12, Premium 4K at $16", correct: true, feedback: "Segmentation lets price-sensitive users stay (with ad revenue) while high-value users pay more." },
            { text: "Lower the price to $8 for everyone", feedback: "Needs 25%+ more subscribers just to break even — risky." },
            { text: "Make it free", feedback: "Not without a different business model." },
            { text: "Raise to $20 for everyone", feedback: "Breakeven churn would be 50% — but research suggests elasticity rises sharply." }
          ]
        },
        {
          kind: "mcq",
          title: "Recommendation",
          question: "What do you recommend?",
          options: [
            { text: "Raise the price, but via tiers: keep a cheaper ad-supported plan to retain price-sensitive users, move the standard plan to $12, add a premium tier. Even a flat hike adds ~$5.6M/month with 4.7 pts of churn cushion. Pilot in one region and track churn and re-subscriptions for 3 months.", correct: true, feedback: "Clear, quantified, and de-risked." },
            { text: "Don't raise prices, customers will be upset", feedback: "The numbers show headroom; manage the risk instead of avoiding it." },
            { text: "Raise to $12 immediately for everyone, no testing", feedback: "Leaves value on the table and skips de-risking." },
            { text: "It depends", feedback: "Take a position." }
          ]
        }
      ],
      modelAnswer: "A flat hike to $12 lifts revenue ~5.6% even with 12% churn (breakeven churn 16.7%). Better: tiered pricing (ad-supported / standard / premium) to retain price-sensitive users and capture high-value ones. Pilot regionally and monitor churn and lifetime value."
    }
  ],

  /* ------------------------------------------------------------------ */
  behavioral: {
    star: [
      { k: "S", name: "Situation", tip: "1–2 sentences of context: where, when, what was at stake. Keep it short." },
      { k: "T", name: "Task", tip: "Your specific responsibility or goal. What did YOU need to achieve?" },
      { k: "A", name: "Action", tip: "60% of your answer. What did YOU do, step by step, and why? Use 'I', not 'we'." },
      { k: "R", name: "Result", tip: "Quantified outcome + what you learned. Numbers make it memorable." }
    ],
    rubric: [
      "I stated the situation in under ~20 seconds",
      "My personal role and goal were clear",
      "I used 'I' for my actions (not just 'we')",
      "I explained WHY I chose my actions, not just what I did",
      "There was tension or a real obstacle",
      "The result was quantified (%, $, time, people)",
      "I shared a reflection / what I learned",
      "The whole answer fits in about 2 minutes"
    ],
    categories: [
      { id: "fit", name: "Fit & motivation" },
      { id: "leadership", name: "Leadership" },
      { id: "teamwork", name: "Teamwork & conflict" },
      { id: "impact", name: "Drive & impact" },
      { id: "resilience", name: "Failure & resilience" },
      { id: "influence", name: "Persuasion & ethics" }
    ],
    questions: [
      { id: "tmay", cat: "fit", q: "Walk me through your resume / Tell me about yourself.", tests: "Communication, structure, and whether your story leads logically to consulting.", tips: ["Use Present → Past → Future: who you are now, 2–3 highlights that shaped you, why consulting next.", "Keep it to 90 seconds.", "Plant hooks (an interesting project) the interviewer will want to ask about."], sample: "I'm a final-year finance student at X and currently intern in credit risk at a bank, where I built a model that cut loan-review time by 30%. Two experiences shaped me: leading a 12-person student consulting project for a local SME, and running my family's small business finances during COVID. Both taught me I love solving messy business problems with data and with people. Consulting is the natural next step: I want breadth across industries and to learn from the best problem-solvers — which is why I'm here." },
      { id: "why-consulting", cat: "fit", q: "Why consulting?", tests: "Genuine, specific motivation — not 'learning curve' clichés alone.", tips: ["Give 2–3 reasons, each backed by a personal experience.", "Mention the nature of the work (problem solving, variety, impact, people).", "Avoid sounding like consulting is just a stepping stone."] },
      { id: "why-firm", cat: "fit", q: "Why our firm?", tests: "Research, fit, and that you've spoken to people there.", tips: ["Name people you spoke to and what struck you.", "Mention specific practices, offices, or values that match your experience.", "Avoid generic reasons that fit every firm ('prestige', 'great people')."] },
      { id: "lead-team", cat: "leadership", q: "Tell me about a time you led a team.", tests: "Inclusive leadership: setting direction, bringing people along, handling under-performance.", tips: ["Pick a situation with a challenge (unmotivated members, tight deadline).", "Show how you adapted your style to different people.", "Quantify the result and the team's growth."], sample: "S: In my 3rd year I led a 6-person team in a national case competition; two weeks before the final, our analysis was scattered and two members had stopped contributing. T: As captain I had to get us to a coherent recommendation and re-engage the team. A: I met each disengaged member 1:1 — one felt her ideas were ignored, the other was overloaded with exams. I gave the first ownership of the market-sizing section and rebalanced the second's workload. I then ran a 1-hour 'storyline' session to agree on our answer first and work backwards to the analysis. R: We submitted 2 days early, placed 2nd of 40 teams, and the member who'd felt ignored presented our strongest section. I learned that disengagement is usually a signal, not a personality trait." },
      { id: "lead-no-authority", cat: "leadership", q: "Describe a time you led without formal authority.", tests: "Influence, initiative, and earning trust.", tips: ["Show how you built credibility before asking for buy-in.", "Highlight listening and finding others' motivations."] },
      { id: "conflict", cat: "teamwork", q: "Tell me about a conflict with a teammate. How did you handle it?", tests: "Maturity, empathy, and solving the issue rather than winning the argument.", tips: ["Pick a real disagreement, not a trivial one — but don't bash the other person.", "Show you sought to understand their view first.", "End with the relationship intact and the outcome improved."] },
      { id: "difficult-person", cat: "teamwork", q: "Describe working with someone very different from you.", tests: "Inclusiveness and adaptability.", tips: ["Highlight what you learned from the difference.", "Show concrete adjustments you made."] },
      { id: "achievement", cat: "impact", q: "What is your proudest achievement?", tests: "Entrepreneurial drive and scale of ambition.", tips: ["Choose something with a high bar where YOU drove the result.", "Explain why it matters to you personally.", "Quantify the impact."] },
      { id: "initiative", cat: "impact", q: "Tell me about a time you went beyond what was expected.", tests: "Ownership and drive.", tips: ["Show you spotted an opportunity others missed.", "Explain obstacles and how you persisted."] },
      { id: "failure", cat: "resilience", q: "Tell me about a time you failed.", tests: "Self-awareness, accountability, and learning.", tips: ["Pick a real failure with real consequences — not a disguised strength.", "Own it without blaming others.", "Spend the most time on what you learned and how you applied it later."] },
      { id: "pressure", cat: "resilience", q: "Describe a time you worked under intense pressure.", tests: "Prioritisation and composure.", tips: ["Explain how you prioritised (what you chose NOT to do).", "Show how you kept quality and communicated with stakeholders."] },
      { id: "ambiguity", cat: "resilience", q: "Tell me about a time you faced a very ambiguous problem.", tests: "Structuring and comfort with uncertainty — daily life in consulting.", tips: ["Show how you broke the problem down and formed a hypothesis.", "Explain how you decided with incomplete information."] },
      { id: "persuade", cat: "influence", q: "Tell me about a time you persuaded someone to change their mind.", tests: "Courageous change, communication, using data and empathy.", tips: ["Show the other person's initial position fairly.", "Explain how you used data AND understood their concerns.", "Quantify the outcome of the change."] },
      { id: "ethics", cat: "influence", q: "Describe a situation where you faced an ethical dilemma.", tests: "Integrity and judgment.", tips: ["Be clear about the trade-off.", "Show you acted on principle, even at a cost.", "Keep it professional and specific."] },
      { id: "feedback", cat: "influence", q: "Tell me about a time you received tough feedback.", tests: "Coachability — consultants get feedback constantly.", tips: ["Show you listened without getting defensive.", "Give concrete evidence that you changed."] }
    ],
    tips: [
      { t: "Build a story bank", d: "Prepare 6–8 strong stories that can flex across many questions (leadership, conflict, failure, impact). One story can answer several questions with a different emphasis." },
      { t: "Expect deep dives", d: "Some interviews (e.g. McKinsey's PEI) drill 10–15 minutes into ONE story: 'What exactly did you say? How did he react? What would you do differently?' Pick stories you remember in detail." },
      { t: "Common dimensions", d: "Firms commonly assess leadership, personal impact, entrepreneurial drive, teamwork and inclusiveness, and the courage to drive change. Map each story to 1–2 of these." },
      { t: "Ask good questions", d: "Prepare 2–3 thoughtful questions for the end — about the interviewer's projects, what surprised them, or how the firm develops people." }
    ]
  },

  /* ------------------------------------------------------------------ */
  // Extra general-knowledge questions for the Daily Challenge (framework quizzes are pooled in too).
  extraQuiz: [
    { q: "CAGR from $100M to $121M over 2 years?", options: ["10%", "10.5%", "21%", "11%"], answer: 0, explain: "1.1² = 1.21 → 10% per year." },
    { q: "Rule of 72: at 8% growth, roughly how long to double?", options: ["6 years", "9 years", "12 years", "8 years"], answer: 1, explain: "72 ÷ 8 = 9 years." },
    { q: "Contribution margin is…", options: ["Revenue − fixed costs", "Price − variable cost per unit", "Profit ÷ revenue", "EBITDA − tax"], answer: 1, explain: "Contribution per unit = price − variable cost per unit; it 'contributes' to fixed costs." },
    { q: "EBITDA stands for earnings before…", options: ["Interest, Taxes, Depreciation and Amortisation", "Investment, Tax, Debt and Assets", "Interest, Treasury, Dividends and Assets", "Income, Taxes, Debt and Amortisation"], answer: 0, explain: "A proxy for operating cash profit." },
    { q: "In a case, the interviewer gives you a chart. What do you do first?", options: ["Start calculating immediately", "Read the title, axes, units and legend, then say the key takeaway", "Ask for a different chart", "Describe every data point"], answer: 1, explain: "Orient yourself, then deliver the 'so what'." },
    { q: "A 20% increase followed by a 20% decrease gives…", options: ["0%", "−4%", "+4%", "−2%"], answer: 1, explain: "1.2 × 0.8 = 0.96 → −4%." },
    { q: "Net Interest Margin (NIM) for a bank measures…", options: ["Fees ÷ assets", "(Interest income − interest expense) ÷ earning assets", "Loans ÷ deposits", "Profit ÷ equity"], answer: 1, explain: "NIM captures the spread between what a bank earns on assets and pays on funding." },
    { q: "In the case interview, when should you ask for a moment to structure?", options: ["Never — it looks weak", "After clarifying questions, before presenting your framework", "Only at the end", "Before the interviewer finishes the prompt"], answer: 1, explain: "Taking 30–90 seconds to structure is expected and looks professional." },
    { q: "Fixed costs $2M, price $50, variable cost $30. Breakeven units?", options: ["40,000", "66,667", "100,000", "200,000"], answer: 2, explain: "$2M ÷ ($50 − $30) = 100,000 units." },
    { q: "ROE = Net income ÷ …", options: ["Total assets", "Shareholders' equity", "Revenue", "Total debt"], answer: 1, explain: "Return on Equity = net income ÷ shareholders' equity." }
  ]
};
