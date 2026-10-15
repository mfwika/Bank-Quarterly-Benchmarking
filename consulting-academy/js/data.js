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
        { q: "Profit = Revenue − Costs is a good first split because…", options: ["It is the split interviewers are trained to expect first", "It is a mathematical identity, so it is MECE by definition", "Most profit problems turn out to be on the cost side", "It lets you skip segmenting by product or customer"], answer: 1, explain: "Equation-based splits can't overlap and can't miss anything — that's why consultants love them." },
        { q: "You list causes of churn as: price, service quality, customer service, competitor offers. What's wrong?", options: ["Nothing: four buckets is the ideal number", "'Service quality' and 'customer service' overlap", "It is missing a bucket for internal causes", "It mixes customer-side and company-side causes"], answer: 1, explain: "Customer service is part of service quality — that's an overlap. Fix by defining the buckets more precisely (e.g. product, price, experience, competitive pull)." }
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
        { q: "Being 'hypothesis-driven' in a case means…", options: ["Stating the answer early and defending it through the case", "Forming an early best guess, then testing and revising it", "Collecting all relevant data before forming any view", "Testing every branch of the tree with equal depth"], answer: 1, explain: "A hypothesis focuses your analysis; data either confirms it or tells you to pivot." },
        { q: "Which is the best leaf for an issue tree?", options: ["How attractive is the overall market for our client?", "What should the client's long-term strategy be?", "What % of revenue was lost with churned customers?", "Why are customers less happy with the brand?"], answer: 2, explain: "A good leaf is specific and answerable with data." },
        { q: "You've drawn a 3-branch tree. What do you do first?", options: ["Work through every branch from left to right", "Ask the interviewer which branch to start with", "Go to the most likely branch and say why", "Add a level of detail so the tree is complete"], answer: 2, explain: "Prioritising (and explaining why) shows judgment — a core consulting skill." }
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
        { q: "The interviewer says 'The CEO just walked in — what do you tell her?' Your first sentence should be…", options: ["'We started by analysing revenue, then moved to costs…'", "'Close the 40 loss-making stores: profit returns to $35M.'", "'There are three key factors we need to consider today…'", "'Our analysis isn't complete, but early signs are good.'"], answer: 1, explain: "Answer first. The CEO wants the decision and the impact in one sentence." },
        { q: "In the Pyramid Principle, the supporting arguments should be…", options: ["Exhaustive, covering every analysis you ran", "MECE and logically grouped (ideally 3)", "In the order you did the analysis", "Quantitative only, with no qualitative points"], answer: 1, explain: "Grouped, MECE, and few — so the listener can hold them in memory." },
        { q: "Which is the best slide title?", options: ["Revenue analysis by region and channel, Q1–Q3", "Asia drove 80% of the decline via lost distributors", "Revenue fell in Asia, Europe and the Americas in Q3", "Key questions on regional revenue performance"], answer: 2, explain: "Action titles state the takeaway — the 'so what'." }
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
        { q: "Revenue is up 10%, profit is down 30%. Where do you look first?", options: ["Price per unit, to see if discounts rose", "Costs: which line grew faster than revenue", "Market share versus the main competitors", "Volume by segment, to find weak products"], answer: 1, explain: "If revenue grew yet profit fell, costs grew faster. Find the line item that outpaced revenue." },
        { q: "Average margin dropped though every product's margin is unchanged. Most likely cause?", options: ["Fixed costs rose faster than revenue did", "Mix shifted toward lower-margin products", "Prices fell across most of the portfolio", "Variable costs per unit rose for most lines"], answer: 1, explain: "If each product's margin is stable, only the weights (mix) can move the average." },
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
        { q: "Value = $300M standalone + $50M synergies. Seller asks $360M. Best response?", options: ["Accept: $360M is close to the $350M total value", "Negotiate down: $360M gives away all synergies", "Walk away: any premium over $300M destroys value", "Accept, then raise synergy targets to compensate"], answer: 2, explain: "Above $350M you destroy value. Negotiate to share the synergies, or walk." }
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
        { q: "Which approach sizes 'number of taxi rides per day in a city' from the supply side?", options: ["City population × taxi trips per person per day", "# taxis × rides per taxi per shift × shifts per day", "Transport spending × taxi share ÷ average fare", "Daily visitors × share who take a taxi × trips"], answer: 1, explain: "Supply side = number of taxis × rides each can do per shift." },
        { q: "The most important thing in a market-sizing question is…", options: ["Landing within 10% of the true market size", "A logical structure with explicit assumptions", "Using the most precise data points you can recall", "Covering as many customer segments as possible"], answer: 1, explain: "Interviewers grade the approach and communication, not the decimal." }
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
        { q: "A machine saves a factory $100k/yr for 5 years. Competitors' machines cost $200k. Cost to make is $80k. Value-based ceiling?", options: ["~$200k (competitor price)", "~$100k (one year of savings)", "~$500k (before discounting)", "~$96k (cost + 20% margin)"], answer: 2, explain: "Customer value is ~5 × $100k = $500k (less with discounting). That's the ceiling; competitor price and cost are lower anchors." },
        { q: "Raising price from $10 to $12. Max % of customers you can lose before revenue falls?", options: ["10.0%", "16.7%", "20.0%", "25.0%"], answer: 1, explain: "Breakeven: 1 − 10/12 = 16.7%." },
        { q: "Launching a new tech product to grab share fast before competitors arrive suggests…", options: ["Skimming pricing", "Penetration pricing", "Cost-plus pricing", "Value-based pricing"], answer: 1, explain: "Penetration pricing: low price to win share quickly." }
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
        { q: "First step in a growth case?", options: ["Screen acquisition targets that add revenue fast", "Size the growth gap vs the baseline trajectory", "Map the Ansoff quadrants and pick the safest", "Benchmark growth rates against main competitors"], answer: 1, explain: "Know how much growth is needed versus where you're heading anyway." }
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
        { q: "Banking licences are hard to get. This lowers…", options: ["Threat of new entrants", "Rivalry among competitors", "Bargaining power of suppliers", "Threat of substitutes"], answer: 0, explain: "Regulatory barriers protect incumbents from new entrants." }
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
        { q: "Which of these is one of the 3Cs?", options: ["Cost structure", "Competitors", "Channels", "Capabilities"], answer: 1, explain: "Customers, Company, Competitors." },
        { q: "'Sell via supermarkets or online only?' is a decision about…", options: ["Product", "Price", "Place", "Promotion"], answer: 2, explain: "Place = distribution channels." },
        { q: "What should you define first in a launch case?", options: ["The launch price point", "The target customer segment", "The distribution channels", "The launch marketing budget"], answer: 1, explain: "Everything else (product, price, channel, message) depends on who you're targeting." }
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
        { q: "'Use less' cost levers include…", options: ["Renegotiating prices with key suppliers", "Reducing waste through process redesign", "Consolidating suppliers for volume discounts", "Moving production to a lower-wage country"], answer: 1, explain: "Using less = lower quantity consumed; renegotiating = paying less per unit." }
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
      prompt: "Our client, Brewed Awakening, grew from 200 to 220 coffee shops over the last two years. Revenue rose from $400M to $440M, yet operating profit fell from $40M to $28M. The CEO wants to understand why and wants a plan to get back to a 10% operating margin within 18 months.",
      steps: [
        {
          kind: "mcq",
          title: "Clarify",
          question: "You may ask one clarifying question before structuring. Which one is most valuable right now?",
          options: [
            { text: "Have competitors' operating margins moved the same way over these two years?", correct: true, feedback: "Best first question: it tells you whether you're solving a company problem or an industry problem, which changes the whole structure." },
            { text: "Which of our 220 stores have the lowest operating margin today, and where are they?", feedback: "Useful later, but segmenting by store before you know whether the issue is revenue, cost or industry-wide is premature." },
            { text: "How much have coffee bean and dairy prices moved since the start of 2023?", feedback: "This tests one specific hypothesis (input inflation) before you have a structure. Keep it for when you're inside the cost branch." },
            { text: "What is the average ticket size, and how has it changed over the two years?", feedback: "A reasonable data request, but it doesn't help you frame the problem yet. Ask it inside the revenue branch." }
          ],
          reveal: "Interviewer: Peers' margins have been broadly stable at ~10%, so this looks specific to our client."
        },
        {
          kind: "mcq",
          title: "Structure",
          question: "Which structure would you lay out for the interviewer?",
          options: [
            { text: "Market vs company: market size, growth and share; then brand, operations and talent inside the company", feedback: "Too vague for a profit problem. It doesn't separate revenue from cost, so you can't quantify where the $12M went." },
            { text: "Revenue (store count × revenue per store) vs costs (each line as % of revenue), then segment the moving pieces", correct: true, feedback: "Quantitative and MECE. It also separates growth from new stores and growth from existing stores." },
            { text: "Value chain: sourcing, roasting, logistics, in-store operations and sales, benchmarking each step against peers", feedback: "Strong for a cost-cutting case, but it ignores revenue and pricing, and that is where part of this answer turns out to be." },
            { text: "Customers, competitors and company, then a 4Ps review of product, price, place and promotion", feedback: "A marketing lens. It may surface ideas, but it can't explain a 3.6-point margin drop in numbers." }
          ]
        },
        {
          kind: "math",
          title: "Exhibit 1: How bad is it?",
          exhibit: { caption: "Brewed Awakening P&L ($M)", headers: ["Line", "2023", "2025"], rows: [["Stores (#)", "200", "220"], ["Revenue", "400", "440"], ["Cost of goods (ingredients, cups)", "120", "143"], ["Store labour", "120", "138"], ["Rent", "80", "90"], ["Marketing & other", "40", "41"], ["Operating profit", "40", "28"]] },
          question: "By how many percentage points did operating margin fall from 2023 to 2025? (one decimal)",
          answer: 3.6,
          tolerance: 0.1,
          unit: "pts",
          explain: "2023: 40/400 = 10.0%. 2025: 28/440 = 6.4%. That's a drop of ~3.6 points. Also notice revenue per store is flat at $2.0M (400/200 vs 440/220), so all the growth came from new stores."
        },
        {
          kind: "mcq",
          title: "Read the exhibit",
          question: "Using the same exhibit, which reading of the cost lines is correct?",
          options: [
            { text: "Store labour is the main problem: it rose $18M, almost as much as revenue grew, and drives most of the decline", feedback: "Absolute dollars mislead here. As a % of revenue, labour rose 1.4 pts while cost of goods rose 2.5 pts." },
            { text: "Rent is the hidden problem: twenty new leases signed at peak prices pushed rent up by $10M in two years", feedback: "Rent went from 20.0% to 20.5% of revenue, only +0.5 pts. It grew roughly in line with the store count." },
            { text: "Cost of goods rose 2.5 pts of revenue and labour 1.4 pts; together they explain more than the whole decline", correct: true, feedback: "Right. COGS 30.0% → 32.5%, labour 30.0% → 31.4%, rent +0.5, other −0.7. COGS is the biggest driver, with labour second." },
            { text: "Every cost line grew at about the same rate as revenue, so the drop must come from one-off items", feedback: "Not true. COGS grew 19% and labour 15% against 10% revenue growth, while marketing & other barely moved." }
          ]
        },
        {
          kind: "math",
          title: "Exhibit 2: Inside cost of goods",
          exhibit: { caption: "Revenue mix and ingredient cost by category", headers: ["Category", "Mix 2023", "Mix 2025", "COGS % of price 2023", "COGS % of price 2025", "Avg price 2023 → 2025"], rows: [["Hot coffee & tea", "85%", "65%", "28%", "28%", "$4.10 → $4.10"], ["Iced specialty", "15%", "35%", "40%", "40%", "$4.40 → $4.40"]] },
          question: "Holding each category's COGS % constant, what blended COGS % does the 2025 mix predict? (one decimal)",
          answer: 32.2,
          tolerance: 0.15,
          unit: "%",
          explain: "0.65 × 28% + 0.35 × 40% = 18.2% + 14.0% = 32.2%. That's almost all of the actual 32.5%. Category costs and prices are flat, so this is a mix effect, not input inflation."
        },
        {
          kind: "mcq",
          title: "Labour",
          exhibit: { caption: "Store labour drivers", headers: ["Driver", "2023", "2025"], rows: [["Avg hourly wage", "$15.00", "$15.60"], ["Labour hours per store per year", "40,000", "40,200"], ["Avg menu price (blended)", "$4.15", "$4.21"], ["Prep time: hot vs iced drink", "40s vs 90s", "40s vs 90s"]] },
          question: "Labour rose 1.4 pts of revenue. What is the best explanation?",
          options: [
            { text: "Iced drinks take twice as long to make, so the mix shift is driving a large increase in hours per store", feedback: "It's a reasonable hypothesis, but hours per store are almost flat (+0.5%). Something absorbed the extra prep time." },
            { text: "The new stores are over-staffed during ramp-up, which inflates labour hours across the network", feedback: "Hours per store barely moved, so over-staffing isn't visible in the data." },
            { text: "Wages rose 4% while prices stayed nearly flat: inflation the company absorbed instead of passing on", correct: true, feedback: "Yes. The blended price rose only because of the mix. Peers stayed at ~10% margins, which suggests they repriced and we didn't." },
            { text: "Labour productivity collapsed because staff turnover rose, so more hours are needed for the same sales", feedback: "Hours per store and revenue per store are both roughly flat, so productivity is broadly stable." }
          ]
        },
        {
          kind: "multi",
          title: "Brainstorm levers",
          question: "Select ALL the levers that address the root causes without hurting the growth engine.",
          options: [
            { text: "Re-price iced specialty drinks so their margin is closer to hot drinks", correct: true },
            { text: "Re-engineer iced recipes (syrup dosing, cup and lid spec) to cut unit cost", correct: true },
            { text: "Take a modest menu-wide price increase to recover wage inflation", correct: true },
            { text: "Discount hot coffee to steer the mix back toward lower-cost drinks", correct: false },
            { text: "Pause new store openings until the chain's margin recovers", correct: false },
            { text: "Cut store marketing to offset the higher ingredient bill", correct: false }
          ],
          explain: "Fix the margin of the growing product (price and recipe) and pass on wage inflation like peers did. Discounting hot coffee lowers margin on 65% of sales. New stores perform like old ones (flat revenue per store), so pausing openings stops growth for no reason. Marketing already fell as a % of revenue and isn't the root cause."
        },
        {
          kind: "math",
          title: "Size the fix",
          question: "If price and recipe changes bring iced-drink COGS from 40% to 34% of price, what's the blended COGS % at the 2025 mix? (one decimal)",
          answer: 30.1,
          tolerance: 0.15,
          unit: "%",
          explain: "0.65 × 28% + 0.35 × 34% = 18.2% + 11.9% = 30.1%. That recovers ~2.1–2.4 pts. Add a ~1.5% menu-wide price rise and the 10% margin target is within reach."
        },
        {
          kind: "mcq",
          title: "Synthesis",
          question: "The CEO has 60 seconds. Which synthesis do you give?",
          options: [
            { text: "Margin fell 3.6 pts because the 20 new stores diluted it. Pause openings, fix the weakest 20 existing stores, and revisit growth in 2027.", feedback: "The data doesn't support this. Revenue per store is flat and every category's economics are unchanged, so new stores aren't the issue." },
            { text: "Margin fell 3.6 pts: the mix shifted to iced drinks (40% COGS) and wages rose unpriced. Re-price and re-cost iced drinks, plus a small menu-wide rise.", correct: true, feedback: "Answer first, both root causes, quantified levers and a de-risking step." },
            { text: "Margin fell 3.6 pts because labour grew by $18M. Cut 5% of store hours, renegotiate rents, and pause all marketing until margin is back above 10%.", feedback: "This chases absolute dollars. Labour is the second driver, and the plan ignores the mix effect behind 2.5 pts." },
            { text: "Margin fell 3.6 pts because coffee input costs rose. Lock in long-term bean contracts and shift the mix back toward hot drinks with promotions.", feedback: "Category COGS % didn't change, so input prices aren't the story. Promotions on hot drinks would cut margin further." }
          ]
        }
      ],
      modelAnswer: "Margin fell from 10.0% to 6.4%. About 2.5 pts came from a mix shift to iced specialty drinks (40% COGS vs 28%), with prices barely above hot drinks. About 1.4 pts came from 4% wage inflation that wasn't passed on to prices. Re-price and re-engineer iced drinks (COGS 40% → ~34%, blended ~30%), take a modest menu-wide price rise, keep opening stores, and pilot in a subset of stores before rolling out."
    },
    {
      id: "bank-digital",
      icon: "🏦",
      title: "Nusantara Bank Goes Digital",
      type: "Market Entry",
      difficulty: 2,
      client: "Mid-size Indonesian commercial bank",
      prompt: "Nusantara Bank is a mid-size Indonesian bank focused on corporate clients, funded by a large, cheap deposit base. Its board is considering a digital lending app for micro and small businesses (MSMEs). Should they enter, and if so, how? (All figures are illustrative.)",
      steps: [
        {
          kind: "mcq",
          title: "Structure",
          question: "Which structure best fits the board's question?",
          options: [
            { text: "Market size and growth, the competitor landscape, regulation, and the needs of each MSME customer segment", feedback: "All about the market. It never asks whether the bank can win or how it would enter, so it can't produce a decision." },
            { text: "Revenue potential, cost to build the platform, credit losses, and the risk-adjusted NPV of the investment", feedback: "Only the economics. Without the bank's right to win and the entry mode, the NPV inputs are guesses." },
            { text: "Market attractiveness, our right to win, entry mode (build, buy or partner), then economics and risks", correct: true, feedback: "Covers whether to enter, whether we can win, how, and whether it pays, so it ends in a decision." },
            { text: "The bank's current capabilities, potential partners, an implementation roadmap and KPIs for the launch", feedback: "This assumes the answer is 'yes' and jumps to execution." }
          ]
        },
        {
          kind: "math",
          title: "Size the opportunity",
          exhibit: { caption: "MSME segments", headers: ["Segment", "# businesses", "% digitally active & need credit", "Avg loan / yr"], rows: [["Micro", "60.0M", "15%", "Rp 20M"], ["Small", "3.5M", "40%", "Rp 300M"], ["Medium*", "0.5M", "70%", "Rp 4B"]] },
          question: "*Medium businesses are already served by the bank's commercial team. What is annual addressable loan demand for micro + small only, in Rp trillion?",
          answer: 600,
          tolerance: 2,
          unit: "Rp T",
          explain: "Micro: 60M × 15% = 9M × Rp 20M = Rp 180T. Small: 3.5M × 40% = 1.4M × Rp 300M = Rp 420T. Total = Rp 600T. Leaving medium out is the trap: it would add Rp 1,400T that isn't part of this decision."
        },
        {
          kind: "math",
          title: "How much is unserved?",
          question: "Banks and fintechs already lend about Rp 450T a year to these two segments. What % of addressable demand is unmet?",
          answer: 25,
          tolerance: 0.5,
          unit: "%",
          explain: "(600 − 450) ÷ 600 = 25%, a Rp 150T gap. It's large, but most of the market is already contested, so entering is about taking share as much as filling the gap."
        },
        {
          kind: "math",
          title: "Unit economics",
          exhibit: { caption: "Micro-loan economics (per active loan, per year)", headers: ["Item", "% of loan balance"], rows: [["Average loan balance", "Rp 20M"], ["Interest + fee yield", "24%"], ["Funding cost (bank deposits)", "6%"], ["Expected credit loss", "7%"], ["Servicing & acquisition", "5%"], ["Platform & team fixed cost", "Rp 240B / year"]] },
          question: "How many active micro-loans does the bank need to break even? (in thousands)",
          answer: 200,
          tolerance: 1,
          unit: "k loans",
          explain: "Contribution = 24 − 6 − 7 − 5 = 6% of Rp 20M = Rp 1.2M per loan per year. Breakeven = Rp 240B ÷ Rp 1.2M = 200,000 loans, or 2.2% of the 9M micro-businesses in scope."
        },
        {
          kind: "math",
          title: "Stress test",
          question: "First-time MSME borrowers often default more than planned. If expected credit loss is 10% instead of 7%, what's the new breakeven? (in thousands of loans)",
          answer: 400,
          tolerance: 2,
          unit: "k loans",
          explain: "Contribution drops to 24 − 6 − 10 − 5 = 3%, or Rp 0.6M per loan, so breakeven doubles to 400,000 loans. Three points of credit loss halve the margin. Credit scoring is the make-or-break capability."
        },
        {
          kind: "mcq",
          title: "Entry mode",
          exhibit: { caption: "What diligence tells us", headers: ["Fact", "Detail"], rows: [["Bank's MSME credit-scoring track record", "None"], ["Time to build app + scoring in-house", "~24 months"], ["Vendor (white-label) scoring engine", "9 months; trained on other markets' data"], ["Leading fintech lenders", "5M active MSME users; strong data; funding cost ~12%"], ["Fintech valuations", "8–10× revenue"], ["Bank's funding cost", "~6%"]] },
          question: "Which entry mode do you recommend?",
          options: [
            { text: "Build in-house: keep full control of customer data and use the deposit base, accepting a two-year launch", feedback: "Slow, and the bank has no scoring track record. The stress test shows that's exactly where losses come from." },
            { text: "Acquire a leading fintech outright to get its scoring, users and team on the bank's balance sheet quickly", feedback: "Fast, but at 8–10× revenue it's expensive. Integrating a fintech culture into a corporate bank is a big risk too." },
            { text: "Partner: we fund at ~6%, a fintech originates and scores, with shared losses and an equity option", correct: true, feedback: "Each side brings what the other lacks: cheap funding plus proven scoring and distribution. It's fast, and the equity option keeps upside." },
            { text: "License a white-label scoring engine and launch under the bank's own brand within about nine months", feedback: "Faster than building, but the models weren't trained on Indonesian MSMEs and the bank still has no way to acquire customers." }
          ]
        },
        {
          kind: "multi",
          title: "Risks",
          question: "Select ALL risks that belong in the board memo.",
          options: [
            { text: "Credit losses above plan: each extra point of loss sharply raises breakeven", correct: true },
            { text: "Adverse selection: the partner keeps its best borrowers and passes on weaker ones", correct: true },
            { text: "Regulatory change on digital-lending rates, fees or bank–fintech partnerships", correct: true },
            { text: "Cannibalisation of the bank's existing corporate loan book and fee income", correct: false },
            { text: "Deposit outflows as corporate clients move cash to the new MSME app", correct: false }
          ],
          explain: "Credit risk, misaligned incentives and regulation decide whether this works. Corporate and MSME lending barely overlap, and corporate treasurers won't move deposits to a micro-loan app."
        },
        {
          kind: "mcq",
          title: "Recommendation",
          question: "What do you tell the board?",
          options: [
            { text: "Enter via a fintech funding partnership: Rp 600T demand, ~200k-loan breakeven, and 6% funding is our edge. Require risk-sharing, cap the pilot, scale if losses stay ≤7%.", correct: true, feedback: "A decision, the how, the numbers, the main risk and a scaling trigger." },
            { text: "Enter by building our own app. Rp 600T demand and our 6% funding mean we can win alone. Hire a scoring team now and launch in 24 months, with full ownership of the customer and the data.", feedback: "This contradicts the diligence: no scoring track record, a slow build, and credit loss is the swing factor." },
            { text: "Enter by acquiring the leading fintech. Rp 600T demand justifies paying 8–10× revenue, and owning its 5M users gives us instant scale, with the deal financed from our deposit base.", feedback: "The size of the market doesn't justify any price. Paying 8–10× when a partnership gets the same capability is poor capital discipline." },
            { text: "Don't enter. 75% of demand is already served, credit losses could double breakeven, and MSME lending sits outside our corporate DNA, so we stay focused on what we do best.", feedback: "Too cautious. The risks can be managed with a partnership and a capped pilot, and the funding edge is real." }
          ]
        }
      ],
      modelAnswer: "Enter MSME digital lending through a funding partnership with an established fintech. Addressable demand is ~Rp 600T/yr (25% unmet), breakeven is ~200k micro-loans, and the bank's ~6% deposit funding is a real edge against fintechs' ~12%. Credit loss is the swing factor (7% → 10% doubles breakeven), so require risk-sharing, cap the pilot, and scale only if losses track plan."
    },
    {
      id: "screen-protector",
      icon: "📱",
      title: "Screen Protector Market",
      type: "Market Sizing",
      difficulty: 2,
      client: "Accessories manufacturer",
      prompt: "A phone-accessories maker is considering entering a country of 100 million people. They want the annual market for smartphone screen protectors, in units and in dollars, and a view on which assumptions matter most.",
      steps: [
        {
          kind: "mcq",
          title: "Approach",
          question: "Which approach do you propose?",
          options: [
            { text: "Supply side: add up the annual import volumes and local production reported by accessory distributors", feedback: "Valid in principle, but you can't estimate it in an interview and it misses grey-market imports." },
            { text: "New phones sold per year × the share of buyers who add a protector at purchase × average price", feedback: "A classic trap: this only counts the protector bought with a new phone and misses replacements during the phone's life." },
            { text: "Smartphone users by age group, split by phone tier, × protector usage, replacements per year and price", correct: true, feedback: "Demand-side and segmented where behaviour differs. Premium and budget users buy very different protectors." },
            { text: "Household spending on phone accessories × the share of that spending that goes to screen protectors", feedback: "Both inputs are hard to anchor, so the answer would rest on two guesses." }
          ]
        },
        {
          kind: "math",
          title: "Smartphone users",
          exhibit: { caption: "Population & penetration", headers: ["Age group", "% of population", "Smartphone penetration"], rows: [["0–14", "25%", "20%"], ["15–64", "68%", "85%"], ["65+", "7%", "40%"]] },
          question: "How many smartphone users are there, in millions? (one decimal)",
          answer: 65.6,
          tolerance: 0.3,
          unit: "M users",
          explain: "25M × 20% = 5.0M; 68M × 85% = 57.8M; 7M × 40% = 2.8M. Total = 65.6M."
        },
        {
          kind: "math",
          title: "Units",
          exhibit: { caption: "Usage by phone tier", headers: ["Tier", "% of users", "% using a protector", "Protectors / user / yr", "Avg price"], rows: [["Premium", "30%", "80%", "1.5", "$12"], ["Budget", "70%", "40%", "1.0", "$3"]] },
          question: "How many protectors are sold per year, in millions? (one decimal)",
          answer: 42.0,
          tolerance: 0.4,
          unit: "M units",
          explain: "Premium: 65.6M × 30% = 19.7M × 80% = 15.7M users × 1.5 = 23.6M units. Budget: 65.6M × 70% = 45.9M × 40% = 18.4M × 1.0 = 18.4M units. Total ≈ 42.0M units."
        },
        {
          kind: "math",
          title: "Value",
          question: "What's the market value, in $ millions?",
          answer: 338.5,
          tolerance: 4,
          unit: "$M",
          explain: "Premium: 23.6M × $12 ≈ $283M. Budget: 18.4M × $3 ≈ $55M. Total ≈ $339M. Premium is 56% of units but ~84% of value."
        },
        {
          kind: "mcq",
          title: "Triangulate",
          question: "The client says an industry report puts the market at about $120M. What's the most likely reason for the gap?",
          options: [
            { text: "The report counts only protectors sold with a new phone, missing mid-life replacements", correct: true, feedback: "Likely. Count only attach-at-purchase over a ~3-year phone life and you get roughly a third of our figure, which is close to $120M." },
            { text: "The report values the market at retail prices while our estimate uses lower wholesale prices", feedback: "That would make the report higher than ours, not lower. Our prices are retail." },
            { text: "Our estimate double-counts children, who share phones with their parents in most households", feedback: "Children are only 5M of 65.6M users. Removing them changes the total by under 10%." },
            { text: "The report is likely in another currency, so the two numbers can't be compared directly", feedback: "Possible, but you'd check it rather than assume it. A structural difference in scope is the more insightful hypothesis." }
          ]
        },
        {
          kind: "mcq",
          title: "Sensitivity",
          question: "A 10% error in which assumption moves the dollar estimate the most?",
          options: [
            { text: "The share of children aged 0–14 who own a smartphone", feedback: "A 10% change moves ~0.5M users, or about $2.6M. Small." },
            { text: "The replacement rate for budget-tier protector users", feedback: "Budget is only ~$55M of value, so a 10% change moves about $5.5M." },
            { text: "The average price of a premium-tier screen protector", correct: true, feedback: "Premium is ~$283M of value, so a 10% price change moves ~$28M. Validate this one first." },
            { text: "Smartphone penetration among people aged 65 and over", feedback: "2.8M users. A 10% change moves ~0.3M users, about $1.4M." }
          ]
        }
      ],
      modelAnswer: "≈ 65.6M smartphone users → ≈ 42M protectors/yr → ≈ $340M/yr, of which ~84% is premium-tier. The gap to the $120M industry figure is most likely a scope difference (attach-at-purchase only). The estimate is most sensitive to premium protector price and usage, so validate those first."
    },
    {
      id: "gym-pe",
      icon: "🏋️",
      title: "FitNation Buyout",
      type: "M&A / Private Equity",
      difficulty: 3,
      client: "Private-equity fund",
      prompt: "A private-equity fund is considering buying FitNation, a chain of 150 mid-price gyms, for $600M. The fund's investment committee requires at least a 2.0× money multiple (MOIC) over a 5-year hold. Should they buy, and at what price?",
      steps: [
        {
          kind: "mcq",
          title: "Structure",
          question: "Which structure fits a PE investment committee?",
          options: [
            { text: "Market attractiveness, FitNation's standalone position, a value-creation plan, then price, returns and exit", correct: true, feedback: "It mirrors how PE decides: is it a good business, can we make it better, and do the returns clear the hurdle at this price?" },
            { text: "FitNation's customers, its competitors and the company itself, followed by a review of its marketing mix", feedback: "This might explain the gyms' performance, but it never reaches price, leverage, returns or exit." },
            { text: "Revenue drivers (members × fee) against fixed and variable club costs, segmented by club and region", feedback: "Useful for one branch (the operational plan), but it can't answer whether $600M is the right price." },
            { text: "Strategic fit with the fund's other holdings, revenue and cost synergies, and post-merger integration risks", feedback: "A corporate-buyer lens. A stand-alone PE fund usually has no synergies; returns come from operations, leverage and exit." }
          ]
        },
        {
          kind: "math",
          title: "Implied multiple",
          exhibit: { caption: "FitNation today", headers: ["Item", "Value"], rows: [["Revenue", "$300M"], ["EBITDA", "$50M"], ["Recent gym deals (EV / EBITDA)", "9× – 11×"]] },
          question: "What EV/EBITDA multiple does the $600M price imply?",
          answer: 12,
          tolerance: 0.05,
          unit: "×",
          explain: "$600M ÷ $50M = 12×, above every comparable deal (9–11×)."
        },
        {
          kind: "math",
          title: "Value-creation plan",
          exhibit: { caption: "Initiatives (run-rate by year 3)", headers: ["Initiative", "EBITDA impact"], rows: [["Centralised procurement (equipment, energy)", "+$4M"], ["Dynamic membership pricing", "+$6M"], ["Close 10 loss-making clubs", "+$2M"], ["Extra churn caused by the pricing change", "−$2M"]] },
          question: "What is run-rate EBITDA in year 3, in $M?",
          answer: 60,
          tolerance: 0.5,
          unit: "$M",
          explain: "50 + 4 + 6 + 2 − 2 = $60M. Remember the churn side-effect: it's easy to add up only the positives."
        },
        {
          kind: "math",
          title: "Returns at the asking price",
          exhibit: { caption: "Deal structure", headers: ["Item", "Assumption"], rows: [["Debt at entry", "50% of price"], ["Debt repaid over 5 years", "$100M"], ["Exit multiple", "10× EBITDA"], ["Exit EBITDA", "$60M"]] },
          question: "If the fund pays $600M, what MOIC does it earn? (two decimals)",
          answer: 1.33,
          tolerance: 0.02,
          unit: "×",
          explain: "Equity in = $300M; debt = $300M. Exit EV = 10 × 60 = $600M. Debt at exit = 300 − 100 = $200M. Equity out = 600 − 200 = $400M. MOIC = 400 ÷ 300 = 1.33×, far below the 2.0× hurdle."
        },
        {
          kind: "math",
          title: "Maximum price",
          question: "Keeping the same structure (50% debt, $100M repaid, $600M exit EV), what's the highest price that still delivers 2.0×? ($M, no decimals)",
          answer: 467,
          tolerance: 3,
          unit: "$M",
          explain: "Price P: equity in = 0.5P; equity out = 600 − (0.5P − 100) = 700 − 0.5P. Set (700 − 0.5P) = 2 × 0.5P → 700 = 1.5P → P ≈ $467M, about 9.3× today's EBITDA."
        },
        {
          kind: "mcq",
          title: "Negotiating stance",
          question: "What stance should the fund take?",
          options: [
            { text: "Accept $600M: the year-5 exit value equals the price, so the downside is protected even if returns are thin", feedback: "Equal exit and entry value gives a 1.33× MOIC, below the hurdle and with all the execution risk on the fund." },
            { text: "Offer about $500M with 70% debt, so the higher leverage lifts the equity multiple above the hurdle", feedback: "It's tempting, but it borrows returns from risk. More debt on a cyclical, membership-driven business raises the chance of default." },
            { text: "Bid about $440–465M (8.8–9.3×), and walk away above ~$467M unless diligence improves the plan", correct: true, feedback: "Disciplined: anchored on the 2.0× maximum, inside comparable multiples, and keeping the plan's upside for the fund." },
            { text: "Walk away now: a 12× ask against 9–11× comparables shows the seller won't be reasonable", feedback: "Too early. An asking price is an opening position, and at the right price the deal clears the hurdle." }
          ]
        },
        {
          kind: "multi",
          title: "Risks",
          question: "Select ALL risks that could break the investment case.",
          options: [
            { text: "Members see dynamic pricing as unfair, and churn exceeds the $2M assumption", correct: true },
            { text: "Budget and boutique chains squeeze the mid-price segment from both sides", correct: true },
            { text: "Exit multiples fall from 10× to 8× by the time the fund sells", correct: true },
            { text: "A downturn cuts memberships just as debt payments are due", correct: true },
            { text: "Two regional club managers resign during the ownership transition", correct: false },
            { text: "Seller warranties expire before the first annual audit is complete", correct: false }
          ],
          explain: "Pricing backlash, the competitive squeeze, a lower exit multiple and leverage in a downturn can each wipe out the returns. Losing two managers is a hiring problem, and warranty timing is a legal detail. Neither breaks the thesis."
        },
        {
          kind: "mcq",
          title: "Recommendation",
          question: "Your recommendation to the investment committee?",
          options: [
            { text: "Proceed at up to $600M. The plan lifts EBITDA to $60M, the gyms are a quality asset, and the sector is consolidating, so we risk losing a scarce platform.", feedback: "That's fear of missing out, not a return case. At $600M the deal returns 1.33×." },
            { text: "Proceed at ~$450M, max ~$467M (≤9.3×). The plan takes EBITDA to $60M; at 50% debt and 10× exit that's ≥2.0×. Diligence churn and the 10 clubs' leases first.", correct: true, feedback: "The decision, the price logic tied to the hurdle, the plan and what to diligence next." },
            { text: "Proceed at $500M with 70% debt. That keeps the price close to the ask, wins the auction, and still delivers the 2.0× hurdle through extra financial leverage.", feedback: "It hits the multiple only by adding risk. If memberships dip, the extra debt hurts most." },
            { text: "Decline. The ask is 12×, mid-price gyms face pressure from both sides, and the plan relies on pricing that members may reject, so the risks outweigh the reward.", feedback: "The risks are real, but they're a reason to price carefully, not to walk away. At ~$450M the deal works." }
          ]
        }
      ],
      modelAnswer: "At $600M (12×) the deal returns only ~1.33×, even after the plan lifts EBITDA from $50M to ~$60M. The highest price that still delivers the 2.0× hurdle with 50% debt and a 10× exit is ~$467M (≈9.3×). Bid ~$440–465M, walk away above that, and diligence churn under dynamic pricing and the leases on the 10 clubs to be closed."
    },
    {
      id: "stream-pricing",
      icon: "📺",
      title: "StreamCo Price Hike",
      type: "Pricing",
      difficulty: 3,
      client: "Video-streaming service",
      prompt: "StreamCo has 10 million subscribers paying $10/month. Each subscriber costs $2/month in bandwidth and payment fees. Management wants to raise the price to $12, and a headline survey says 12% of subscribers would cancel. Should they?",
      steps: [
        {
          kind: "math",
          title: "Contribution after the hike",
          question: "Today monthly contribution is 10M × ($10 − $2) = $80M. What is it after the hike if 12% cancel? ($M)",
          answer: 88,
          tolerance: 0.3,
          unit: "$M / mo",
          explain: "8.8M × ($12 − $2) = $88M, up 10%. If you used revenue you'd get +5.6%, which understates the gain because cancellers also take their costs away."
        },
        {
          kind: "math",
          title: "Breakeven churn",
          question: "What % of subscribers could cancel before monthly contribution falls below $80M?",
          answer: 20,
          tolerance: 0.2,
          unit: "%",
          explain: "(1 − x) × $10 = $8 → x = 20%. The revenue-based shortcut (1 − 10/12 = 16.7%) ignores variable costs. Using contribution is the correct measure."
        },
        {
          kind: "math",
          title: "Segment the churn",
          exhibit: { caption: "Churn at $12 by usage segment", headers: ["Segment", "% of subscribers", "Churn at $12"], rows: [["Light (< 5 hrs/mo)", "40%", "25%"], ["Regular", "45%", "6%"], ["Power (> 40 hrs/mo)", "15%", "2%"]] },
          question: "What's the subscriber-weighted churn implied by the segment data? (%)",
          answer: 13,
          tolerance: 0.2,
          unit: "%",
          explain: "0.40 × 25 + 0.45 × 6 + 0.15 × 2 = 10 + 2.7 + 0.3 = 13%. That's slightly worse than the 12% headline, but the bigger insight is that churn is very concentrated among light users."
        },
        {
          kind: "mcq",
          title: "So what?",
          question: "What does the segment data tell you about pricing design?",
          options: [
            { text: "One price can't fit all: light users are very price-sensitive while regular and power users barely react", correct: true, feedback: "Right. That's the textbook case for segmenting the offer, for example with a cheaper tier for light users." },
            { text: "The survey is unreliable because churn ranges from 2% to 25%, so management should run a new survey first", feedback: "Different segments reacting differently is normal and useful information, not a sign that the survey is broken." },
            { text: "Light users bring little value and cost the same to serve, so the company should let them churn at $12", feedback: "They still contribute $8 each a month. Losing a million of them on purpose gives up value you could keep with a cheaper tier." },
            { text: "Power users clearly value the product most, so only their price should go up while everyone else stays at $10", feedback: "They're only 15% of the base. You'd leave most of the regular users' low price sensitivity unused." }
          ]
        },
        {
          kind: "math",
          title: "Tiered design",
          exhibit: { caption: "Proposed tiers", headers: ["Tier", "Who", "Price", "Ad revenue / user", "Churn"], rows: [["Basic with ads", "Light users", "$7", "$4", "5%"], ["Standard", "Regular", "$12", "—", "6%"], ["Premium 4K", "Power", "$12*", "—", "2%"]] },
          question: "*Assume Premium stays at $12 for now. Variable cost is $2 per user. What's total monthly contribution under the tiers? ($M, one decimal)",
          answer: 91.2,
          tolerance: 0.3,
          unit: "$M / mo",
          explain: "Light: 4.0M × 95% = 3.8M × (7 + 4 − 2) = $34.2M. Regular: 4.5M × 94% = 4.23M × 10 = $42.3M. Power: 1.5M × 98% = 1.47M × 10 = $14.7M. Total ≈ $91.2M, against $87M for a flat hike at 13% churn. A real Premium price would add more."
        },
        {
          kind: "mcq",
          title: "What the math misses",
          question: "Before recommending, what's the most important risk the monthly math ignores?",
          options: [
            { text: "Light users moving to an ad tier could cut viewing time and weaken the content flywheel", feedback: "A real second-order effect, but light users watch less than 5 hrs/month, so their engagement matters least." },
            { text: "Regular users might trade down to the cheaper ad tier, eroding the $12 Standard revenue", correct: true, feedback: "Cannibalisation is the classic risk of tiering. Fence the tiers (ads, resolution, devices) and track trade-down closely." },
            { text: "Competitors may follow with similar increases, which would make the price rise look less bold", feedback: "Competitors following would actually reduce churn risk. It isn't a risk to StreamCo's plan." },
            { text: "Bandwidth cost per user may fall over time, so today's $2 understates future contribution", feedback: "That would be good news, not a risk, and it doesn't change the decision." }
          ]
        },
        {
          kind: "mcq",
          title: "Recommendation",
          question: "What do you recommend to management?",
          options: [
            { text: "Raise everyone to $12 now. Contribution rises from $80M to ~$87M even at 13% churn, which is well within the 20% breakeven, and it's the simplest change to run and explain.", feedback: "The numbers work, but this leaves ~$4M/month on the table and loses a million light users who could have stayed." },
            { text: "Hold the price at $10. Churn reaches 25% in the light-user segment, and losing a million subscribers would hurt the brand and the content flywheel more than $7M a month helps.", feedback: "Too cautious. There's a design that captures most of the upside and keeps light users." },
            { text: "Launch tiers ($7 with ads, $12 Standard, Premium): contribution ~$91M vs ~$87M flat. Fence tiers against trade-down and pilot in one region first.", correct: true, feedback: "Decision, numbers compared with the alternative, the key risk and how to test it." },
            { text: "Raise only Premium to $16 and keep everyone else at $10. Power users barely churn, so the risk is near zero, though the gain is modest. Revisit broader pricing next year.", feedback: "It's safe but small: about 1.5M users × $4. It ignores the regular users' low price sensitivity." }
          ]
        }
      ],
      modelAnswer: "A flat $12 hike works (contribution $80M → ~$87M at 13% churn; breakeven churn is 20%), but churn is concentrated among light users. Tiered pricing ($7 with ads, $12 Standard, Premium) yields ~$91M by keeping light users through ad revenue. The main risk is trade-down from Standard, so fence the tiers and pilot in one region before rolling out."
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
    { q: "Contribution margin is…", options: ["Price − total cost per unit", "Price − variable cost per unit", "Revenue − fixed costs, per unit", "Gross profit ÷ revenue"], answer: 1, explain: "Contribution per unit = price − variable cost per unit; it 'contributes' to fixed costs." },
    { q: "EBITDA stands for earnings before…", options: ["Interest, Taxes, Depreciation and Amortisation", "Investment, Taxes, Debt service and Acquisitions", "Interest, Treasury, Dividends and Amortisation", "Income tax, Debt and Asset write-downs"], answer: 0, explain: "A proxy for operating cash profit." },
    { q: "In a case, the interviewer gives you a chart. What do you do first?", options: ["Start computing the growth rates it shows", "Read title, axes and units, then the takeaway", "Walk the interviewer through every data point", "Ask what the interviewer wants you to find"], answer: 1, explain: "Orient yourself, then deliver the 'so what'." },
    { q: "A 20% increase followed by a 20% decrease gives…", options: ["0%", "−4%", "+4%", "−2%"], answer: 1, explain: "1.2 × 0.8 = 0.96 → −4%." },
    { q: "Net Interest Margin (NIM) for a bank measures…", options: ["Interest income ÷ total loans", "Net interest income ÷ earning assets", "Net interest income ÷ total equity", "(Interest + fee income) ÷ total assets"], answer: 1, explain: "NIM captures the spread between what a bank earns on assets and pays on funding." },
    { q: "In the case interview, when should you ask for a moment to structure?", options: ["Right after the prompt, before any questions", "After clarifying, before presenting a framework", "Only if the case turns out to be unusual", "After the first exhibit, once you have data"], answer: 1, explain: "Taking 30–90 seconds to structure is expected and looks professional." },
    { q: "Fixed costs $2M, price $50, variable cost $30. Breakeven units?", options: ["40,000", "66,667", "100,000", "200,000"], answer: 2, explain: "$2M ÷ ($50 − $30) = 100,000 units." },
    { q: "ROE = Net income ÷ …", options: ["Total assets", "Shareholders' equity", "Total liabilities", "Risk-weighted assets"], answer: 1, explain: "Return on Equity = net income ÷ shareholders' equity." }
  ]
};
