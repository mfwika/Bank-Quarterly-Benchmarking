/* Consulting Academy — MECE Practice content.
 * Each prompt can be scored against several valid structures ("frames"); the best-matching frame wins,
 * so there is no single right answer, only sound logic.
 * Pillar: { id, label, kw: general terms, alt: driver terms that also cover the pillar, subs: [{ label, kw }], opt }
 * Keywords match the start of a word ("pric" matches "price", "pricing"). Some Bahasa Indonesia terms are included.
 */
(function () {
  const K = {
    revenue: ["revenue", "sales", "top line", "topline", "turnover", "pendapatan", "penjualan", "omzet"],
    price: ["pric", "fare", "yield", "tarif", "harga", "discount", "arpu", "average ticket", "ticket price"],
    cost: ["cost", "expense", "opex", "spend", "biaya", "beban", "pengeluaran"],
    market: ["market", "industr", "pasar", "external", "eksternal", "macro", "economy", "environment"],
    competition: ["competit", "rival", "peer", "market share", "pesaing", "kompetitor"],
    regulation: ["regulat", "law", "licen", "policy", "government", "compliance", "ojk", "regulasi", "izin", "pemerintah"],
    risk: ["risk", "risiko", "downside", "mitigat", "uncertaint"]
  };
  const J = function () { return Array.prototype.concat.apply([], arguments); };

  window.CA_DATA.mece = {
    vague: ["analysis", "factors", "issues", "things", "strategy", "general", "misc", "miscellaneous", "faktor", "aspects", "considerations", "problems", "topics", "points"],
    solutionWords: ["solution", "recommendation", "idea", "action plan", "next step", "rekomendasi", "solusi", "initiative"],
    overlapPairs: [
      ["marketing", "promotion"], ["marketing", "advertis"], ["customer service", "service quality"],
      ["brand", "reputation"], ["staff", "employee"], ["staff", "people"], ["competitor", "competition"],
      ["people", "labour"], ["people", "labor"], ["salar", "wage"], ["customer", "client"]
    ],
    prompts: [
      /* ------------------------------------------------------------ */
      {
        id: "airline",
        icon: "✈️",
        title: "SkyNusa's falling profit",
        type: "Profitability",
        difficulty: 1,
        prompt: "SkyNusa, an Indonesian low-cost airline, saw net profit fall 30% last year even though passenger numbers rose 8%. Fuel and other costs per seat moved in line with competitors, while competitors raised their fares by about 5%. The CEO asks: why are profits falling?",
        question: "Why did SkyNusa's profit fall 30%?",
        frames: [
          { name: "Profit = Revenue − Costs", pillars: [
            { id: "rev", label: "Revenue", kw: J(K.revenue, ["income"]), alt: J(K.price, ["passenger", "load factor", "volume", "ancillar", "penumpang"]), subs: [
              { label: "Fare / yield per passenger", kw: K.price },
              { label: "Passenger volume / load factor", kw: ["passenger", "load factor", "volume", "seat", "occupanc", "penumpang"] },
              { label: "Ancillary revenue (bags, seats, food)", kw: ["ancillar", "bag", "food", "seat selection", "bagasi"] },
              { label: "Route / segment mix", kw: ["route", "mix", "segment", "domestic", "international", "rute"] }
            ] },
            { id: "cost", label: "Costs", kw: K.cost, alt: ["fuel", "avtur", "fixed", "variable"], subs: [
              { label: "Fuel", kw: ["fuel", "avtur", "jet"] },
              { label: "Aircraft leases / ownership", kw: ["lease", "aircraft", "fleet", "depreciat", "sewa", "pesawat"] },
              { label: "Crew & staff", kw: ["crew", "staff", "labour", "labor", "salar", "pilot", "gaji", "wage"] },
              { label: "Airport, handling & maintenance fees", kw: ["airport", "landing", "maintenance", "handling", "navigation", "bandara"] },
              { label: "Distribution & sales costs", kw: ["distribution", "commission", "booking", "travel agent", "ota"] }
            ] },
            { id: "ext", label: "Market & competitors", opt: true, kw: J(K.market, K.competition), alt: ["currency", "exchange", "rupiah", "kurs"], subs: [
              { label: "Competitor fares & capacity", kw: K.competition },
              { label: "FX / fuel price environment", kw: ["exchange", "currency", "rupiah", "kurs", "fx", "dollar"] }
            ] }
          ] }
        ],
        priority: { kw: J(K.price, ["revenue per passenger", "revenue per seat"]), why: "Costs per seat are in line with peers and volume is up, so the gap must be in what each passenger pays: competitors raised fares ~5% while SkyNusa apparently didn't." },
        offs: [
          { kw: ["mission", "vision", "culture", "csr", "employer brand"], why: "Mission, culture or CSR don't explain a 30% profit drop in one year. Keep the tree on profit drivers." }
        ],
        builder: {
          buckets: [
            { t: "Revenue", ok: true }, { t: "Costs", ok: true }, { t: "Market & competitors", ok: true },
            { t: "Marketing", ok: false, why: "Marketing overlaps with Revenue (it drives demand) and Costs (it's a spend line). It isn't a separate driver." },
            { t: "Fuel", ok: false, why: "Fuel is one line inside Costs. As a top-level bucket it mixes levels." },
            { t: "Customer satisfaction", ok: false, why: "A symptom or input, not a profit driver on its own. It acts through volume and price." }
          ],
          cards: [
            { t: "Average fare per passenger", b: "Revenue" },
            { t: "Load factor (share of seats filled)", b: "Revenue" },
            { t: "Baggage and seat-selection fees", b: "Revenue" },
            { t: "Jet fuel cost per flight hour", b: "Costs" },
            { t: "Aircraft lease payments", b: "Costs" },
            { t: "Crew salaries and training", b: "Costs" },
            { t: "Airport landing and handling fees", b: "Costs" },
            { t: "Competitors' fare changes", b: "Market & competitors" },
            { t: "Rupiah–dollar exchange rate", b: "Market & competitors" },
            { t: "Launch a loyalty app campaign", b: null, why: "That's a solution, not a driver. Park ideas until you know the cause." },
            { t: "Company mission and values", b: null, why: "It doesn't explain a profit drop." }
          ],
          priority: ["Revenue"]
        },
        takeaway: "Use the clues: volume up and costs in line with peers means the problem is price per passenger. A strong candidate says so in the first minute and goes straight to yield."
      },
      /* ------------------------------------------------------------ */
      {
        id: "sme-loans",
        icon: "🏦",
        title: "Shrinking SME loan book",
        type: "Revenue diagnosis",
        difficulty: 2,
        prompt: "Bank Sentosa's SME loan book shrank 15% last year, while the SME lending market grew 10% and peer banks grew their SME books. Management wants to know why the book is shrinking.",
        question: "Why did Bank Sentosa's SME loan book shrink 15%?",
        frames: [
          { name: "Stock & flow (balance = new loans − outflows)", pillars: [
            { id: "in", label: "New lending (inflows)", kw: ["new loan", "new lending", "inflow", "origination", "disburs", "new business", "pencairan", "acquisition"], alt: ["application", "approv", "pipeline", "lead", "pengajuan"], subs: [
              { label: "Leads & applications", kw: ["lead", "application", "pipeline", "pengajuan", "demand"] },
              { label: "Approval rate / credit policy", kw: ["approv", "reject", "credit policy", "risk appetite", "underwrit", "scoring", "persetujuan"] },
              { label: "Turnaround time & process", kw: ["turnaround", "speed", "process", "sla", "time to", "proses", "document"] },
              { label: "Pricing & product terms", kw: J(K.price, ["interest rate", "bunga", "tenor", "collateral", "agunan", "rate"]) },
              { label: "Sales channels / RM capacity", kw: ["channel", "rm", "relationship manager", "branch", "sales force", "cabang"] }
            ] },
            { id: "out", label: "Outflows (repayments, run-off, write-offs)", kw: ["outflow", "run-off", "runoff", "repay", "exist", "pelunasan"], alt: ["prepay", "refinanc", "write", "npl", "maturit", "churn", "attrition"], subs: [
              { label: "Scheduled repayments / maturities", kw: ["repay", "maturit", "amortis", "runoff", "run-off", "jatuh tempo"] },
              { label: "Prepayments / refinancing elsewhere", kw: ["prepay", "refinanc", "switch", "churn", "attrition", "pindah"] },
              { label: "Write-offs / NPL", kw: ["write", "npl", "default", "bad loan", "macet", "hapus"] }
            ] },
            { id: "ext", label: "Market context", opt: true, kw: K.market, alt: J(K.competition, K.regulation), subs: [
              { label: "SME credit demand", kw: ["demand", "economy", "permintaan"] },
              { label: "Competitor offers", kw: K.competition },
              { label: "Regulation", kw: K.regulation }
            ] }
          ] },
          { name: "Internal vs external", pillars: [
            { id: "ext", label: "External", kw: ["external", "eksternal", "market", "macro", "pasar"], alt: J(K.competition, K.regulation, ["economy", "demand"]), subs: [
              { label: "SME credit demand / economy", kw: ["demand", "economy", "gdp", "permintaan"] },
              { label: "Competitor offers", kw: K.competition },
              { label: "Regulation", kw: K.regulation }
            ] },
            { id: "int", label: "Internal", kw: ["internal", "our ", "bank's", "own ", "company", "sentosa"], alt: ["credit policy", "risk appetite", "process", "product", "offer", "sales force", "rm "], subs: [
              { label: "Pricing & product", kw: J(K.price, ["interest rate", "bunga", "product", "tenor", "collateral"]) },
              { label: "Credit policy / approval rate", kw: ["approv", "credit policy", "risk appetite", "underwrit", "scoring"] },
              { label: "Process speed", kw: ["turnaround", "speed", "process", "sla", "proses"] },
              { label: "Channels / RM capacity", kw: ["channel", "rm", "relationship manager", "branch", "sales force"] },
              { label: "Retention of existing clients", kw: ["retention", "prepay", "refinanc", "churn", "attrition"] }
            ] }
          ] }
        ],
        priority: { kw: ["internal", "approv", "credit policy", "risk appetite", "process", "pric", "interest rate", "offer", "rm", "turnaround", "refinanc", "prepay", "origination", "new loan", "new lending", "inflow", "outflow"], why: "The market grew 10% and peers grew, so external demand isn't the cause. Start inside the bank: are fewer new loans going out (approval, pricing, speed), or are existing clients leaving?" },
        offs: [
          { kw: ["rebrand", "logo", "head office", "headquarter"], why: "Branding and head-office topics don't explain a 15% book decline while peers grow." }
        ],
        builder: {
          buckets: [
            { t: "New lending (inflows)", ok: true }, { t: "Repayments & run-off (outflows)", ok: true }, { t: "Market context", ok: true },
            { t: "Interest rates", ok: false, why: "Pricing is one driver of new lending. As a top-level bucket it mixes levels." },
            { t: "Customers", ok: false, why: "Too vague: customers drive both inflows and outflows, so it overlaps with both." },
            { t: "Digital transformation", ok: false, why: "That's a solution theme, not a driver of the loan balance." }
          ],
          cards: [
            { t: "Number of SME loan applications", b: "New lending (inflows)" },
            { t: "Approval rate after a credit-policy change", b: "New lending (inflows)" },
            { t: "Days from application to disbursement", b: "New lending (inflows)" },
            { t: "Loan pricing quoted to new applicants", b: "New lending (inflows)" },
            { t: "Scheduled repayments and maturities", b: "Repayments & run-off (outflows)" },
            { t: "Clients refinancing with other banks", b: "Repayments & run-off (outflows)" },
            { t: "Loans written off as uncollectable", b: "Repayments & run-off (outflows)" },
            { t: "SME credit demand in the economy", b: "Market context" },
            { t: "Competitors' new SME products", b: "Market context" },
            { t: "OJK rules on SME lending", b: "Market context" },
            { t: "Launch a new mobile banking app", b: null, why: "That's a solution, not a diagnosis of why the book shrank." },
            { t: "Head-office renovation budget", b: null, why: "It has no link to the size of the loan book." }
          ],
          priority: ["New lending (inflows)", "Repayments & run-off (outflows)"]
        },
        takeaway: "A balance (loan book, subscribers, inventory) is a stock: stock = start + inflows − outflows. That split is mathematically MECE. Combine it with the clue (market and peers growing) to point at internal causes first."
      },
      /* ------------------------------------------------------------ */
      {
        id: "vietnam",
        icon: "☕",
        title: "Kopi Kita goes to Vietnam",
        type: "Market entry",
        difficulty: 2,
        prompt: "Kopi Kita, a profitable Indonesian coffee chain with 300 stores, is considering opening in Vietnam. Vietnam has a strong home-grown coffee culture and several large local chains. The founder asks: should we enter, and if so, how?",
        question: "Should Kopi Kita enter Vietnam, and how?",
        frames: [
          { name: "Market · Ability to win · Entry mode · Economics", pillars: [
            { id: "mkt", label: "Market attractiveness", kw: J(K.market, ["attractiv"]), alt: ["size", "growth", "margin", "profitab"], subs: [
              { label: "Size & growth", kw: ["size", "growth", "grow", "volume", "ukuran"] },
              { label: "Profitability / margins", kw: ["margin", "profitab"] },
              { label: "Competition & local chains", kw: J(K.competition, ["local chain", "incumbent"]) },
              { label: "Customer preferences", kw: ["customer", "consumer", "taste", "preference", "habit", "culture", "konsumen"] }
            ] },
            { id: "win", label: "Ability to win", kw: ["ability", "right to win", "capabilit", "can we win", "competitive advantage", "fit", "kemampuan", "company", "kopi kita", "internal"], alt: ["brand", "supply chain", "sourcing", "management", "strength", "differentiat"], subs: [
              { label: "Product fit with local tastes", kw: ["taste", "menu", "product", "fit", "differentiat"] },
              { label: "Capabilities & cost advantages", kw: ["supply chain", "sourcing", "cost advantage", "operation", "capabilit"] },
              { label: "Management bandwidth & resources", kw: ["management", "bandwidth", "talent", "resource", "capital", "team"] }
            ] },
            { id: "mode", label: "Entry mode", kw: ["entry mode", "how to enter", "mode of entry", "entry option"], alt: ["build", "buy", "acqui", "partner", "joint venture", "jv", "franchis", "licens", "organic", "akuisisi"], subs: [
              { label: "Build own stores (organic)", kw: ["build", "organic", "own store", "greenfield"] },
              { label: "Acquire a local chain", kw: ["acqui", "buy", "akuisisi"] },
              { label: "Partner / franchise / JV", kw: ["partner", "franchis", "joint venture", "jv", "licens"] }
            ] },
            { id: "eco", label: "Economics & risks", kw: J(["economics", "financial", "return", "roi", "npv", "payback", "breakeven", "break-even", "investment"], K.risk), alt: J(K.regulation, ["currency", "fx"]), subs: [
              { label: "Investment, breakeven, payback", kw: ["investment", "breakeven", "break-even", "payback", "roi", "npv", "capex", "return"] },
              { label: "Risks: FX, regulation, competitor reaction", kw: J(K.risk, K.regulation, ["currency", "fx", "reaction"]) }
            ] }
          ] },
          { name: "3Cs + economics", pillars: [
            { id: "cust", label: "Customers", kw: ["customer", "consumer", "konsumen", "demand"], alt: ["taste", "preference", "segment", "willingness"], subs: [
              { label: "Segments & needs", kw: ["segment", "need", "taste", "preference", "habit"] },
              { label: "Market size & growth", kw: ["size", "growth", "volume"] },
              { label: "Willingness to pay", kw: ["willingness", "pric", "spend"] }
            ] },
            { id: "comp", label: "Competitors", kw: K.competition, alt: ["local chain", "incumbent"], subs: [
              { label: "Local chains' strength", kw: ["local chain", "incumbent", "share", "position"] },
              { label: "Likely reaction", kw: ["reaction", "respond", "retaliat"] }
            ] },
            { id: "co", label: "Company (Kopi Kita)", kw: ["company", "kopi kita", "our ", "internal", "capabilit"], alt: ["brand", "supply chain", "management", "resource"], subs: [
              { label: "Capabilities & advantages", kw: ["capabilit", "supply chain", "sourcing", "brand", "cost advantage"] },
              { label: "Resources & bandwidth", kw: ["resource", "capital", "management", "bandwidth", "talent"] },
              { label: "Entry mode options", kw: ["build", "acqui", "partner", "franchis", "jv", "joint venture"] }
            ] },
            { id: "eco", label: "Economics & risks", kw: J(["economics", "financial", "return", "roi", "npv", "payback", "breakeven", "investment"], K.risk), alt: K.regulation, subs: [
              { label: "Investment & payback", kw: ["investment", "payback", "breakeven", "roi", "npv", "return"] },
              { label: "Risks", kw: J(K.risk, K.regulation, ["currency", "fx"]) }
            ] }
          ] }
        ],
        priority: { kw: ["ability", "right to win", "capabilit", "differentiat", "competit", "local chain", "incumbent", "can we win", "fit", "taste"], why: "Vietnam is a coffee-loving market with strong local chains, so the market is clearly attractive but crowded. The real question is whether Kopi Kita has a right to win against established local players." },
        offs: [
          { kw: ["indonesian market", "indonesia's market", "domestic store"], why: "The question is about Vietnam. Kopi Kita's Indonesian stores matter only as a source of capabilities." }
        ],
        builder: {
          buckets: [
            { t: "Market attractiveness", ok: true }, { t: "Ability to win", ok: true }, { t: "Entry mode", ok: true }, { t: "Economics & risks", ok: true },
            { t: "Vietnamese coffee culture", ok: false, why: "That's a detail inside Market attractiveness (customer preferences)." },
            { t: "Marketing plan", ok: false, why: "Too early: a launch plan comes after the go / no-go decision." },
            { t: "Store design", ok: false, why: "An execution detail, not part of the entry decision." }
          ],
          cards: [
            { t: "Size and growth of Vietnam's café market", b: "Market attractiveness" },
            { t: "Strength of local chains' positions", b: "Market attractiveness" },
            { t: "Typical café margins in Vietnam", b: "Market attractiveness" },
            { t: "Fit of our menu with Vietnamese tastes", b: "Ability to win" },
            { t: "Our sourcing and supply-chain advantage", b: "Ability to win" },
            { t: "Management bandwidth for a new country", b: "Ability to win" },
            { t: "Own stores vs a franchise partner", b: "Entry mode" },
            { t: "Acquire an existing local chain", b: "Entry mode" },
            { t: "Investment needed and payback period", b: "Economics & risks" },
            { t: "Currency and regulatory risks", b: "Economics & risks" },
            { t: "Indonesian coffee bean export volumes", b: null, why: "That's about Indonesia's market, not whether Vietnam is attractive or whether we can win there." },
            { t: "Choose the logo colour for Vietnam", b: null, why: "A cosmetic execution detail." }
          ],
          priority: ["Ability to win"]
        },
        takeaway: "Every market-entry tree needs an 'Can WE win?' branch, not only 'Is the market good?'. Here the clue (strong local chains) makes that the branch to prioritise."
      },
      /* ------------------------------------------------------------ */
      {
        id: "er-wait",
        icon: "🏥",
        title: "Emergency-room waiting times",
        type: "Operations",
        difficulty: 2,
        prompt: "Average waiting time in the emergency room at RS Harapan, a 400-bed city hospital, rose from 45 to 110 minutes over 12 months. Patient arrivals rose only 5%, and the hospital's wards are now running at 98% occupancy. The director asks why waits have more than doubled.",
        question: "Why have ER waiting times more than doubled?",
        frames: [
          { name: "Demand · Capacity · Process", pillars: [
            { id: "dem", label: "Patient demand", kw: ["demand", "arrival", "patient volume", "inflow", "permintaan", "kedatangan"], alt: ["acuity", "case mix", "severity", "peak"], subs: [
              { label: "Number of arrivals", kw: ["arrival", "volume", "number of patient", "kedatangan"] },
              { label: "Case mix / severity", kw: ["mix", "severity", "acuity", "severe", "complex"] },
              { label: "Timing / peaks", kw: ["peak", "hour", "time of day", "weekend", "season"] }
            ] },
            { id: "cap", label: "Capacity", kw: ["capacity", "resource", "kapasitas"], alt: ["staff", "doctor", "nurse", "bed", "equipment", "dokter", "perawat"], subs: [
              { label: "Doctors & nurses per shift", kw: ["staff", "doctor", "nurse", "shift", "dokter", "perawat"] },
              { label: "ER beds / treatment rooms", kw: ["bed", "room", "cubicle", "tempat tidur"] },
              { label: "Diagnostics (lab, imaging)", kw: ["lab", "x-ray", "imaging", "ct", "radiolog", "diagnost"] }
            ] },
            { id: "proc", label: "Process & patient flow", kw: ["process", "flow", "proses", "alur"], alt: ["triage", "discharge", "admission", "boarding", "bottleneck", "turnaround"], subs: [
              { label: "Triage & prioritisation", kw: ["triage", "prioriti"] },
              { label: "Test turnaround times", kw: ["turnaround", "result", "test"] },
              { label: "Admission / waiting for a ward bed", kw: ["admission", "admit", "boarding", "ward", "occupancy", "rawat inap"] },
              { label: "Discharge speed", kw: ["discharg", "pulang"] }
            ] }
          ] },
          { name: "Patient journey stages", pillars: [
            { id: "arr", label: "Arrival & triage", kw: ["arrival", "triage", "registration", "front door", "pendaftaran"], alt: ["check-in", "intake"], subs: [
              { label: "Arrival volume & peaks", kw: ["volume", "peak", "arrival"] },
              { label: "Triage speed", kw: ["triage", "registration"] }
            ] },
            { id: "trt", label: "Assessment & treatment", kw: ["assessment", "treatment", "diagnos", "examination", "pemeriksaan"], alt: ["doctor", "lab", "imaging", "test"], subs: [
              { label: "Doctor availability", kw: ["doctor", "physician", "staff", "dokter"] },
              { label: "Tests & imaging turnaround", kw: ["lab", "test", "imaging", "x-ray", "result"] }
            ] },
            { id: "exit", label: "Exit (admit or discharge)", kw: ["exit", "disposition", "admission", "discharg", "admit", "outflow"], alt: ["ward", "boarding", "occupancy", "bed block"], subs: [
              { label: "Waiting for a ward bed", kw: ["ward", "boarding", "occupancy", "bed"] },
              { label: "Discharge process", kw: ["discharg", "pulang"] }
            ] }
          ] }
        ],
        priority: { kw: ["ward", "occupancy", "admission", "admit", "boarding", "discharg", "exit", "outflow", "bed block", "flow", "capacity"], why: "Arrivals rose only 5%, which can't double waits. Wards at 98% occupancy means admitted patients can't leave the ER, so they 'board' in ER beds and block new patients. Start with the exit or flow branch." },
        offs: [
          { kw: ["parking", "cafeteria", "canteen"], why: "Parking and food services don't drive clinical waiting times." },
          { kw: ["new wing", "new hospital", "build a hospital"], why: "Building capacity is a multi-year solution, not a diagnosis of why waits doubled." }
        ],
        builder: {
          buckets: [
            { t: "Patient demand", ok: true }, { t: "Capacity", ok: true }, { t: "Process & patient flow", ok: true },
            { t: "Doctors", ok: false, why: "Doctors are one part of Capacity. As a top-level bucket it mixes levels." },
            { t: "Patient complaints", ok: false, why: "A symptom of long waits, not a cause." },
            { t: "Hospital reputation", ok: false, why: "Not a driver of operational waiting time." }
          ],
          cards: [
            { t: "Number of daily arrivals", b: "Patient demand" },
            { t: "Share of severe vs minor cases", b: "Patient demand" },
            { t: "Peak arrival hours", b: "Patient demand" },
            { t: "Doctors and nurses on each shift", b: "Capacity" },
            { t: "Number of ER treatment beds", b: "Capacity" },
            { t: "Lab and X-ray staffing at night", b: "Capacity" },
            { t: "Triage rules and priority levels", b: "Process & patient flow" },
            { t: "Time for lab results to come back", b: "Process & patient flow" },
            { t: "Admitted patients waiting for a ward bed", b: "Process & patient flow" },
            { t: "Visitor parking fees", b: null, why: "Not related to clinical waiting time." },
            { t: "Build a new hospital wing", b: null, why: "A long-term solution, not a diagnosis." }
          ],
          priority: ["Process & patient flow"]
        },
        takeaway: "Queues follow from demand versus capacity, plus how smoothly patients move through. When demand barely moved, look at the flow out of the system. Here a full ward blocks the ER exit."
      },
      /* ------------------------------------------------------------ */
      {
        id: "uniforms",
        icon: "🎒",
        title: "School uniform market",
        type: "Market sizing",
        difficulty: 1,
        prompt: "A garment maker that sells mid-priced school uniforms wants to know: how big is the annual market for school uniforms in Indonesia, in Rupiah? Lay out how you'd structure the estimate.",
        question: "Annual school uniform market in Indonesia (Rp)",
        frames: [
          { name: "Demand side: students × uniforms × price", pillars: [
            { id: "stu", label: "Number of students", kw: ["student", "siswa", "pupil", "murid", "enrol", "children", "anak"], alt: ["population", "school-age", "penduduk"], subs: [
              { label: "School-age population", kw: ["population", "school-age", "age", "penduduk", "usia"] },
              { label: "Enrolment rate", kw: ["enrol", "participation", "partisipasi"] },
              { label: "Split by level (SD/SMP/SMA)", kw: ["level", "primary", "junior", "senior", "sd", "smp", "sma", "elementary", "high school"] }
            ] },
            { id: "qty", label: "Uniforms per student per year", kw: ["per student", "uniforms per", "sets per", "quantity", "frequency", "jumlah seragam"], alt: ["type", "replace", "replacement", "new entrant", "batik", "scout", "pramuka", "sport"], subs: [
              { label: "Uniform types (national, scout, batik, sport)", kw: ["type", "batik", "scout", "pramuka", "sport", "olahraga", "national"] },
              { label: "Replacement frequency", kw: ["replace", "frequency", "wear", "outgrow", "ganti"] },
              { label: "Extra sets for new entrants", kw: ["new entrant", "new student", "first year", "siswa baru"] }
            ] },
            { id: "pr", label: "Price per uniform", kw: ["price", "pric", "harga", "cost per set", "asp"], alt: ["premium", "budget", "quality"], subs: [
              { label: "Average price per set", kw: ["average price", "per set", "per uniform", "rata"] },
              { label: "Price by level / quality tier", kw: ["tier", "premium", "budget", "quality", "level"] }
            ] }
          ] },
          { name: "Supply side: schools × uniforms per school × price", pillars: [
            { id: "sch", label: "Number of schools", kw: ["school", "sekolah"], alt: ["sd", "smp", "sma"], subs: [
              { label: "Schools by level", kw: ["level", "sd", "smp", "sma", "primary", "secondary"] }
            ] },
            { id: "per", label: "Uniforms per school per year", kw: ["per school", "students per school", "class size"], alt: ["student", "siswa", "sets"], subs: [
              { label: "Students per school", kw: ["student", "siswa", "class"] },
              { label: "Sets per student", kw: ["set", "replace", "type"] }
            ] },
            { id: "pr", label: "Price per uniform", kw: ["price", "pric", "harga"], alt: ["premium", "budget"], subs: [
              { label: "Average price", kw: ["average", "per set", "per uniform"] }
            ] }
          ] }
        ],
        priority: { kw: ["student", "siswa", "enrol", "school-age", "population", "penduduk", "children"], why: "The student count is the anchor of the whole estimate: every later assumption multiplies it. Nail it first (≈ 50M+ students across levels) and sanity-check it." },
        offs: [
          { kw: ["competit", "market share", "profit", "margin", "brand"], why: "Market sizing asks how big the market is, not who wins it or how profitable it is. Keep competitors and margins out of the tree." }
        ],
        builder: {
          buckets: [
            { t: "Number of students", ok: true }, { t: "Uniforms per student per year", ok: true }, { t: "Price per uniform", ok: true },
            { t: "Uniform manufacturers", ok: false, why: "A supply-side view mixed into a demand-side chain. Pick one approach." },
            { t: "Fabric costs", ok: false, why: "Costs affect margins, not the size of the market." },
            { t: "Primary schools", ok: false, why: "One level inside the student count. As a top-level bucket it mixes levels." }
          ],
          cards: [
            { t: "Children aged 6–18", b: "Number of students" },
            { t: "School enrolment rate by level", b: "Number of students" },
            { t: "Split: primary / junior / senior high", b: "Number of students" },
            { t: "Uniform types (national, scout, batik, sport)", b: "Uniforms per student per year" },
            { t: "How often a uniform is replaced", b: "Uniforms per student per year" },
            { t: "Extra sets bought by first-year students", b: "Uniforms per student per year" },
            { t: "Average retail price per set", b: "Price per uniform" },
            { t: "Price difference by school level", b: "Price per uniform" },
            { t: "Profit margin of uniform makers", b: null, why: "Profitability isn't part of market size." },
            { t: "Leading brands' market share", b: null, why: "Who wins the market isn't part of how big it is." }
          ],
          priority: ["Number of students"]
        },
        takeaway: "A sizing tree is a multiplication chain: base × rate × frequency × price. Each branch is one factor, so the structure is MECE by construction."
      },
      /* ------------------------------------------------------------ */
      {
        id: "lab-deal",
        icon: "🧪",
        title: "Hospital group buys a lab chain",
        type: "M&A",
        difficulty: 3,
        prompt: "MediCare Group, which owns 12 hospitals in Java, is considering acquiring LabCepat, a chain of 80 diagnostic labs, for Rp 2 trillion. The seller is asking 15× EBITDA, while recent lab deals were done at 10–12×. Should MediCare buy?",
        question: "Should MediCare acquire LabCepat?",
        frames: [
          { name: "Rationale · Target · Synergies · Valuation · Risks", pillars: [
            { id: "why", label: "Strategic rationale", kw: ["rationale", "strateg", "why buy", "objective", "fit", "alasan"], alt: ["vertical", "integrat", "defen", "capabilit"], subs: [
              { label: "Why own labs vs outsourcing", kw: ["outsourc", "vertical", "integrat", "in-house", "own lab"] },
              { label: "Defensive / competitive logic", kw: ["defen", "competit", "rival", "pesaing"] }
            ] },
            { id: "tgt", label: "Target standalone", kw: ["target", "standalone", "stand-alone", "labcepat"], alt: ["growth", "margin", "quality", "management", "network"], subs: [
              { label: "Market position & growth", kw: ["growth", "market", "share", "position"] },
              { label: "Financials (revenue, margins)", kw: ["revenue", "margin", "ebitda", "financial", "cash"] },
              { label: "Quality, management, referrals", kw: ["quality", "management", "referral", "doctor", "accredit"] }
            ] },
            { id: "syn", label: "Synergies", kw: ["synerg", "sinergi"], alt: ["cross-sell", "procurement", "purchasing", "referral"], subs: [
              { label: "Revenue synergies", kw: ["revenue synerg", "cross-sell", "referral", "send test", "volume"] },
              { label: "Cost synergies", kw: ["cost synerg", "procurement", "purchasing", "reagent", "overhead"] }
            ] },
            { id: "val", label: "Valuation & price", kw: ["valuation", "valu", "price", "pric", "multiple", "harga"], alt: ["ebitda", "dcf", "comparable", "premium", "overpay"], subs: [
              { label: "Standalone value vs comparables", kw: ["comparable", "multiple", "ebitda", "dcf", "10", "12"] },
              { label: "Max price incl. share of synergies", kw: ["max", "walk away", "synerg", "premium", "overpay"] }
            ] },
            { id: "risk", label: "Risks & integration", kw: J(K.risk, ["integrat"]), alt: J(K.regulation, ["antitrust", "kppu", "culture", "retention"]), subs: [
              { label: "Integration & people", kw: ["integrat", "culture", "retention", "talent", "staff"] },
              { label: "Regulatory / antitrust", kw: J(K.regulation, ["antitrust", "kppu", "competition authority"]) }
            ] }
          ] }
        ],
        priority: { kw: ["valuation", "valu", "price", "pric", "multiple", "overpay", "15", "premium", "synerg"], why: "The prompt flags a 15× ask against 10–12× comparables. The deal hinges on whether synergies justify that premium, so test valuation against synergies first." },
        offs: [
          { kw: ["parking", "hospital bed", "new hospital"], why: "The decision is about the lab deal. Hospital expansion is a separate question." }
        ],
        builder: {
          buckets: [
            { t: "Strategic rationale", ok: true }, { t: "LabCepat standalone", ok: true }, { t: "Synergies", ok: true }, { t: "Valuation & price", ok: true }, { t: "Risks & integration", ok: true },
            { t: "Lab equipment", ok: false, why: "A detail of LabCepat's operations. As a top-level bucket it mixes levels." },
            { t: "Marketing", ok: false, why: "It isn't part of an acquisition decision." }
          ],
          cards: [
            { t: "Why own labs instead of outsourcing tests", b: "Strategic rationale" },
            { t: "Stop a rival hospital group buying it first", b: "Strategic rationale" },
            { t: "LabCepat's revenue growth and margins", b: "LabCepat standalone" },
            { t: "Quality and accreditation of its labs", b: "LabCepat standalone" },
            { t: "Send our hospitals' tests to LabCepat", b: "Synergies" },
            { t: "Joint purchasing of reagents", b: "Synergies" },
            { t: "15× EBITDA ask vs 10–12× comparables", b: "Valuation & price" },
            { t: "Maximum price including a share of synergies", b: "Valuation & price" },
            { t: "Retention of key lab staff after the deal", b: "Risks & integration" },
            { t: "Competition-authority approval", b: "Risks & integration" },
            { t: "New parking building at our hospitals", b: null, why: "Not part of the acquisition decision." }
          ],
          priority: ["Valuation & price", "Synergies"]
        },
        takeaway: "M&A questions are about price versus value. The prompt flags a premium multiple, so your structure must lead to the maximum price you'd pay, not just whether the target is a good business."
      },
      /* ------------------------------------------------------------ */
      {
        id: "5g-pricing",
        icon: "📶",
        title: "Pricing 5G home internet",
        type: "Pricing",
        difficulty: 2,
        prompt: "TelcoMax is launching a 5G home-internet plan in Surabaya. Fibre competitors charge about Rp 350k/month for similar speeds but make customers wait 2–3 weeks for installation; TelcoMax's plan works the same day with a plug-in router. What price should TelcoMax charge?",
        question: "What price should TelcoMax charge for 5G home internet?",
        frames: [
          { name: "Cost · Competition · Customer value · Strategy", pillars: [
            { id: "cost", label: "Cost (price floor)", kw: J(K.cost, ["floor", "cost-based", "cost-plus"]), alt: ["network", "equipment", "router", "acquisition cost", "cac"], subs: [
              { label: "Network & equipment cost per user", kw: ["network", "equipment", "router", "spectrum", "tower", "per user"] },
              { label: "Acquisition & servicing costs", kw: ["acquisition", "cac", "service", "support", "marketing cost"] },
              { label: "Breakeven / target margin", kw: ["breakeven", "break-even", "margin", "payback"] }
            ] },
            { id: "comp", label: "Competitors & substitutes", kw: J(K.competition, ["substitut", "alternative", "reference"]), alt: ["fibre", "fiber", "mobile data", "indihome"], subs: [
              { label: "Fibre providers' prices", kw: ["fibre", "fiber", "350", "competitor price"] },
              { label: "Substitutes (mobile data)", kw: ["mobile", "substitut", "data package", "kuota"] },
              { label: "Likely competitor reaction", kw: ["reaction", "respond", "retaliat", "price war"] }
            ] },
            { id: "val", label: "Customer value", kw: ["value", "willingness", "wtp", "customer", "pelanggan", "ceiling"], alt: ["segment", "installation", "convenience", "same day"], subs: [
              { label: "Value of instant setup / no wait", kw: ["install", "same day", "wait", "convenien", "instant"] },
              { label: "Willingness to pay by segment", kw: ["willingness", "wtp", "segment", "household", "renter"] }
            ] },
            { id: "strat", label: "Strategy & objectives", kw: ["strateg", "objective", "goal", "positioning", "tujuan"], alt: ["penetration", "skimming", "tier", "bundle", "share"], subs: [
              { label: "Share vs margin objective", kw: ["penetration", "skimming", "share", "margin", "objective"] },
              { label: "Tiers, bundles, promotions", kw: ["tier", "bundle", "promo", "plan", "paket"] }
            ] }
          ] }
        ],
        priority: { kw: ["value", "willingness", "wtp", "install", "same day", "wait", "convenien", "competitor", "fibre", "fiber", "350"], why: "There's a clear reference price (Rp 350k fibre) and a clear advantage (same-day setup, no 2–3 week wait). Start with customer value against that reference. It tells you whether a premium, parity or discount is justified." },
        offs: [
          { kw: ["brand ambassador", "celebrity", "logo"], why: "Promotional choices come after the price decision." }
        ],
        builder: {
          buckets: [
            { t: "Costs (price floor)", ok: true }, { t: "Competitors & substitutes", ok: true }, { t: "Customer value", ok: true }, { t: "Strategy & objectives", ok: true },
            { t: "Network towers", ok: false, why: "One cost item. As a top-level bucket it mixes levels." },
            { t: "Advertising", ok: false, why: "A launch activity, not a pricing input." },
            { t: "Customer service", ok: false, why: "It overlaps with Costs (servicing) and Customer value." }
          ],
          cards: [
            { t: "Network and equipment cost per user", b: "Costs (price floor)" },
            { t: "Customer acquisition cost", b: "Costs (price floor)" },
            { t: "Fibre providers' prices for similar speeds", b: "Competitors & substitutes" },
            { t: "Mobile data packages as a substitute", b: "Competitors & substitutes" },
            { t: "How rivals react to a low price", b: "Competitors & substitutes" },
            { t: "Value of no installation wait", b: "Customer value" },
            { t: "Willingness to pay by household segment", b: "Customer value" },
            { t: "Goal: grow share fast or maximise margin?", b: "Strategy & objectives" },
            { t: "Tiered speed plans and bundles", b: "Strategy & objectives" },
            { t: "Choose the brand ambassador", b: null, why: "Promotion, not pricing." },
            { t: "Next year's 6G research budget", b: null, why: "Not relevant to pricing this plan." }
          ],
          priority: ["Customer value", "Competitors & substitutes"]
        },
        takeaway: "Price sits between the cost floor and the customer-value ceiling, with competitors as a reference point. When the prompt hands you a differentiator (same-day setup), value it."
      },
      /* ------------------------------------------------------------ */
      {
        id: "fee-income",
        icon: "💳",
        title: "Doubling fee income",
        type: "Growth",
        difficulty: 2,
        prompt: "Bank Mandala wants to double its fee income from Rp 1T to Rp 2T in three years. It has 5 million customers, who hold on average just 1.3 products each (peers average 2.5). How could it get there?",
        question: "How can Bank Mandala double fee income in 3 years?",
        frames: [
          { name: "Fee income = customers × products per customer × fee per product", pillars: [
            { id: "cust", label: "Number of customers", kw: ["number of customer", "customer base", "customers", "nasabah", "new customer", "acquisition"], alt: ["churn", "retention", "new segment", "new region", "new market"], subs: [
              { label: "Acquire new customers / segments / regions", kw: ["acqui", "new customer", "segment", "region", "city", "payroll"] },
              { label: "Reduce churn", kw: ["churn", "retention", "attrition"] }
            ] },
            { id: "ppc", label: "Products per customer", kw: ["products per", "product holding", "cross-sell", "cross sell", "penetration"], alt: ["bundle", "insurance", "bancassurance", "investment", "wealth", "credit card", "new product"], subs: [
              { label: "Cross-sell existing products", kw: ["cross", "bundle", "insurance", "investment", "card", "wealth"] },
              { label: "Launch new fee products", kw: ["new product", "launch", "cash management", "fx", "remittance", "payment"] }
            ] },
            { id: "fee", label: "Fee per product", kw: ["fee per", "pricing", "pric", "fee level", "harga", "tarif"], alt: ["waiver", "reprice", "premium tier", "upsell"], subs: [
              { label: "Reprice underpriced services", kw: ["reprice", "pric", "fee level", "raise fee"] },
              { label: "Reduce fee waivers / leakage", kw: ["waiver", "leakage", "discount"] },
              { label: "Upsell to premium tiers", kw: ["premium", "tier", "upsell", "priority"] }
            ] }
          ] },
          { name: "Ansoff: core / new products / new markets / inorganic", pillars: [
            { id: "core", label: "Existing customers & products", kw: ["existing", "current customer", "core", "penetration"], alt: ["cross-sell", "reprice", "waiver", "upsell"], subs: [
              { label: "Cross-sell & upsell", kw: ["cross", "upsell", "bundle"] },
              { label: "Pricing & waivers", kw: ["pric", "waiver", "reprice"] }
            ] },
            { id: "newp", label: "New products", kw: ["new product", "product development", "launch"], alt: ["insurance", "wealth", "cash management", "fx", "payment"], subs: [
              { label: "Fee-earning products to launch", kw: ["insurance", "wealth", "cash management", "fx", "payment", "remittance"] }
            ] },
            { id: "newm", label: "New customers / markets", kw: ["new customer", "new market", "new segment", "market development", "new region"], alt: ["sme", "payroll", "city", "region"], subs: [
              { label: "New segments or regions", kw: ["segment", "region", "city", "sme", "payroll"] }
            ] },
            { id: "inorg", label: "Partnerships & acquisitions", kw: ["inorganic", "partner", "acqui", "alliance", "kemitraan", "akuisisi"], alt: ["fintech", "insurer", "e-commerce"], subs: [
              { label: "Partners (insurers, fintechs, e-commerce)", kw: ["insurer", "fintech", "e-commerce", "platform", "partner"] }
            ] }
          ] }
        ],
        priority: { kw: ["products per", "cross", "product holding", "existing customer", "bundle", "penetration", "1.3", "2.5"], why: "Customers hold 1.3 products against 2.5 at peers. Closing half that gap almost doubles fee income from the existing base, the cheapest and fastest lever." },
        offs: [
          { kw: ["cost cut", "reduce cost", "cut cost", "headcount", "efisiensi biaya"], why: "The goal is fee income. Cost cutting raises profit but not fees." },
          { kw: ["deposit rate", "interest rate on deposit"], why: "Deposit rates drive interest expense and margin, not fee income." }
        ],
        builder: {
          buckets: [
            { t: "Number of customers", ok: true }, { t: "Products per customer", ok: true }, { t: "Fee per product", ok: true },
            { t: "Credit cards", ok: false, why: "One product. As a top-level bucket it mixes levels." },
            { t: "Cost reduction", ok: false, why: "That answers a different question (profit, not fee income)." },
            { t: "Digital", ok: false, why: "Too vague. Digital can help every branch, so it overlaps with all of them." }
          ],
          cards: [
            { t: "Win new customers through payroll deals", b: "Number of customers" },
            { t: "Expand into new cities", b: "Number of customers" },
            { t: "Reduce customer churn", b: "Number of customers" },
            { t: "Cross-sell insurance and investments", b: "Products per customer" },
            { t: "Bundle current accounts with credit cards", b: "Products per customer" },
            { t: "Launch cash-management services for SMEs", b: "Products per customer" },
            { t: "Reprice underpriced transfer fees", b: "Fee per product" },
            { t: "Move customers to premium account tiers", b: "Fee per product" },
            { t: "Cut fee waivers granted by branches", b: "Fee per product" },
            { t: "Cut branch staff costs", b: null, why: "Cost cutting doesn't grow fee income." },
            { t: "Raise deposit interest rates", b: null, why: "That's an interest expense lever, not fee income." }
          ],
          priority: ["Products per customer"]
        },
        takeaway: "Turn the goal into an equation (customers × products per customer × fee per product) and the tree becomes MECE automatically. Then let the benchmark gap (1.3 vs 2.5) tell you where to start."
      },
      /* ------------------------------------------------------------ */
      {
        id: "trucking-costs",
        icon: "🚚",
        title: "Trucking cost reduction",
        type: "Cost reduction",
        difficulty: 2,
        prompt: "PT Logistik Nusantara, a trucking company, must cut total costs by 15% within 18 months without hurting on-time delivery. Fuel is 40% of its costs, drivers 25%, fleet ownership & maintenance 20%, and overheads 15%. Where should it look?",
        question: "How can Logistik Nusantara cut costs 15%?",
        frames: [
          { name: "By cost bucket", pillars: [
            { id: "fuel", label: "Fuel", kw: ["fuel", "diesel", "solar", "bbm", "bahan bakar"], alt: ["route", "idling", "empty km", "empty kilomet", "consumption"], subs: [
              { label: "Price paid for diesel", kw: ["contract", "purchas", "price", "hedg", "supplier"] },
              { label: "Litres used: routing, empty kms", kw: ["route", "routing", "empty", "km", "kilomet", "load"] },
              { label: "Driving behaviour & idling", kw: ["idl", "driving", "behaviour", "behavior", "speed", "eco"] }
            ] },
            { id: "drv", label: "Drivers & labour", kw: ["driver", "labour", "labor", "staff cost", "people", "sopir", "pengemudi", "wage", "salar"], alt: ["overtime", "turnover", "productivity"], subs: [
              { label: "Overtime hours", kw: ["overtime", "lembur", "hours"] },
              { label: "Turnover & hiring", kw: ["turnover", "hiring", "recruit", "attrition"] },
              { label: "Productivity per driver", kw: ["productiv", "utilis", "utiliz", "trips per"] }
            ] },
            { id: "fleet", label: "Fleet & maintenance", kw: ["fleet", "truck", "vehicle", "armada", "truk", "maintenance", "perawatan"], alt: ["lease", "tyre", "tire", "spare part", "depreciat"], subs: [
              { label: "Own vs lease", kw: ["lease", "own", "buy", "sewa"] },
              { label: "Maintenance & tyres", kw: ["maintenance", "tyre", "tire", "spare", "repair"] },
              { label: "Fleet size & utilisation", kw: ["utilis", "utiliz", "fleet size", "idle truck", "number of truck"] }
            ] },
            { id: "ovh", label: "Overheads", kw: ["overhead", "sg&a", "admin", "back office", "back-office", "g&a"], alt: ["depot", "rent", "it ", "office", "headcount"], subs: [
              { label: "Depots & rent", kw: ["depot", "rent", "warehouse", "sewa"] },
              { label: "Back-office headcount & IT", kw: ["headcount", "back office", "back-office", "it system", "technology", "admin"] }
            ] }
          ] },
          { name: "By lever: price · quantity · structure", pillars: [
            { id: "price", label: "Pay less per unit", kw: ["pay less", "price", "pric", "renegotiat", "procure", "purchas"], alt: ["contract", "supplier", "tender"], subs: [
              { label: "Renegotiate fuel, tyres, parts", kw: ["fuel", "tyre", "tire", "part", "supplier", "contract"] }
            ] },
            { id: "qty", label: "Use less", kw: ["use less", "quantity", "consumption", "efficien", "productiv"], alt: ["route", "idl", "empty", "overtime", "utilis", "utiliz"], subs: [
              { label: "Fewer litres: routing, idling", kw: ["route", "idl", "empty", "litre"] },
              { label: "Fewer hours: overtime, scheduling", kw: ["overtime", "schedul", "hours"] }
            ] },
            { id: "str", label: "Structural changes", kw: ["structur", "footprint", "outsourc", "consolidat"], alt: ["depot", "lease", "fleet size", "network"], subs: [
              { label: "Depot network & fleet size", kw: ["depot", "network", "fleet size", "consolidat"] },
              { label: "Outsource / lease vs own", kw: ["outsourc", "lease", "own"] }
            ] }
          ] }
        ],
        priority: { kw: ["fuel", "diesel", "solar", "bbm", "40%", "biggest", "largest"], why: "Fuel is 40% of costs: a 15% saving on fuel alone delivers 6 of the 15 points. Always start with the biggest bucket." },
        offs: [
          { kw: ["raise price", "increase price", "price increase", "revenue", "new customer", "naikkan harga"], why: "The task is cutting costs. Revenue levers answer a different question." },
          { kw: ["lower on-time", "reduce on-time", "relax on-time", "slower delivery"], why: "On-time delivery is a constraint you must protect, not a lever." }
        ],
        builder: {
          buckets: [
            { t: "Fuel", ok: true }, { t: "Drivers & labour", ok: true }, { t: "Fleet & maintenance", ok: true }, { t: "Overheads", ok: true },
            { t: "Revenue growth", ok: false, why: "That answers a different question: the brief is about cost." },
            { t: "Diesel price", ok: false, why: "One driver inside Fuel. As a top-level bucket it mixes levels." },
            { t: "On-time delivery", ok: false, why: "That's a constraint to protect, not a cost bucket." }
          ],
          cards: [
            { t: "Route planning to cut empty kilometres", b: "Fuel" },
            { t: "Diesel purchase contracts", b: "Fuel" },
            { t: "Engine idling time at depots", b: "Fuel" },
            { t: "Driver overtime hours", b: "Drivers & labour" },
            { t: "Driver turnover and hiring costs", b: "Drivers & labour" },
            { t: "Truck maintenance schedule", b: "Fleet & maintenance" },
            { t: "Lease vs own the trucks", b: "Fleet & maintenance" },
            { t: "Tyre purchasing and retreading", b: "Fleet & maintenance" },
            { t: "Depot rents", b: "Overheads" },
            { t: "Back-office headcount", b: "Overheads" },
            { t: "Raise delivery prices", b: null, why: "A revenue lever, but the brief is about cost." },
            { t: "Relax the on-time delivery target", b: null, why: "That breaks the constraint in the brief." }
          ],
          priority: ["Fuel"]
        },
        takeaway: "For cost cases, split the cost base the way it's reported, then size it: 5% off a 40% bucket beats 30% off a tiny one. Respect the constraint in the prompt."
      },
      /* ------------------------------------------------------------ */
      {
        id: "vaccination",
        icon: "💉",
        title: "Falling child vaccination",
        type: "Public sector",
        difficulty: 3,
        prompt: "Childhood vaccination coverage in Province X fell from 85% to 70% in two years. Vaccine stock at health centres stayed normal throughout, and the number of vaccinators is unchanged. The provincial health office asks why coverage is falling.",
        question: "Why is childhood vaccination coverage falling?",
        frames: [
          { name: "Supply · Access · Demand", pillars: [
            { id: "sup", label: "Vaccine supply & service capacity", kw: ["supply", "stock", "availab", "capacity", "pasokan", "stok"], alt: ["cold chain", "vaccinator", "staff", "nurse", "bidan"], subs: [
              { label: "Vaccine stock", kw: ["stock", "stok", "shortage"] },
              { label: "Cold chain", kw: ["cold chain", "fridge", "refrigerat"] },
              { label: "Vaccinators / staff", kw: ["vaccinator", "staff", "nurse", "bidan", "midwife", "health worker"] }
            ] },
            { id: "acc", label: "Access to services", kw: ["access", "reach", "akses", "convenien"], alt: ["distance", "travel", "opening hour", "transport", "posyandu", "location"], subs: [
              { label: "Distance / travel time", kw: ["distance", "travel", "location", "jarak", "remote", "rural"] },
              { label: "Opening hours", kw: ["hour", "schedule", "jam", "working parent"] },
              { label: "Cost of getting there", kw: ["transport", "cost", "fee", "biaya"] }
            ] },
            { id: "dem", label: "Parents' demand", kw: ["demand", "parent", "willingness", "orang tua", "permintaan", "acceptance"], alt: ["trust", "awareness", "hesitan", "misinformation", "hoax", "reminder", "belief"], subs: [
              { label: "Awareness of schedule", kw: ["aware", "knowledge", "reminder", "schedule", "information"] },
              { label: "Trust / vaccine hesitancy", kw: ["trust", "hesitan", "fear", "safety", "halal", "belief", "religio"] },
              { label: "Misinformation", kw: ["misinform", "hoax", "rumour", "rumor", "social media", "whatsapp"] }
            ] },
            { id: "data", label: "Measurement & data", opt: true, kw: ["data", "measure", "record", "reporting", "pencatatan"], alt: ["denominator", "registry"], subs: [
              { label: "Recording / reporting gaps", kw: ["record", "report", "registry", "denominator"] }
            ] }
          ] },
          { name: "Parent journey: aware → decide → reach → served", pillars: [
            { id: "aw", label: "Awareness", kw: ["aware", "know", "information", "reminder"], alt: ["campaign", "schedule"], subs: [
              { label: "Knowing what & when", kw: ["schedule", "reminder", "know"] }
            ] },
            { id: "dec", label: "Decision / willingness", kw: ["decision", "decide", "willing", "trust", "hesitan", "acceptance"], alt: ["fear", "misinform", "hoax", "belief"], subs: [
              { label: "Trust & fears", kw: ["trust", "fear", "safety", "halal", "belief"] },
              { label: "Misinformation", kw: ["misinform", "hoax", "rumour", "social media"] }
            ] },
            { id: "reach", label: "Reaching the service", kw: ["access", "reach", "distance", "travel"], alt: ["transport", "hour", "location"], subs: [
              { label: "Distance, hours, cost", kw: ["distance", "hour", "transport", "cost"] }
            ] },
            { id: "srv", label: "Being served", kw: ["served", "service", "supply", "stock", "staff"], alt: ["vaccinator", "cold chain", "queue"], subs: [
              { label: "Stock, staff, queues", kw: ["stock", "staff", "vaccinator", "queue", "cold chain"] }
            ] }
          ] }
        ],
        priority: { kw: ["demand", "parent", "trust", "hesitan", "misinform", "hoax", "awareness", "access", "willing", "belief", "decision"], why: "Stock was normal and vaccinators are unchanged, so supply is ruled out. Start with parents: demand (trust, misinformation) and access." },
        offs: [
          { kw: ["new hospital", "build hospital"], why: "A new hospital is a long-term capital project, not a cause of falling coverage." },
          { kw: ["obesity", "adult"], why: "Adult health issues aren't relevant to childhood vaccination coverage." }
        ],
        builder: {
          buckets: [
            { t: "Vaccine supply", ok: true }, { t: "Access to services", ok: true }, { t: "Parents' demand", ok: true },
            { t: "Nurses", ok: false, why: "One part of supply capacity. As a top-level bucket it mixes levels." },
            { t: "Hospitals", ok: false, why: "Too narrow: most child vaccinations happen at puskesmas and posyandu." },
            { t: "Social media", ok: false, why: "One channel of misinformation, which belongs inside Parents' demand." }
          ],
          cards: [
            { t: "Vaccine stock at health centres", b: "Vaccine supply" },
            { t: "Cold-chain fridge breakdowns", b: "Vaccine supply" },
            { t: "Vaccinators on duty", b: "Vaccine supply" },
            { t: "Travel time to the nearest posyandu", b: "Access to services" },
            { t: "Clinic hours vs parents' working hours", b: "Access to services" },
            { t: "Transport cost for rural families", b: "Access to services" },
            { t: "Parents' trust in vaccine safety", b: "Parents' demand" },
            { t: "Misinformation in WhatsApp groups", b: "Parents' demand" },
            { t: "Reminders for upcoming doses", b: "Parents' demand" },
            { t: "Build a new provincial hospital", b: null, why: "A capital project, not a cause." },
            { t: "Adult obesity rates", b: null, why: "Not related to child vaccination." }
          ],
          priority: ["Parents' demand", "Access to services"]
        },
        takeaway: "Supply · access · demand works for almost any 'why aren't people using X?' question, from vaccines to bank apps. Rule branches out with the facts given."
      },
      /* ------------------------------------------------------------ */
      {
        id: "repair-market",
        icon: "🔧",
        title: "Japan phone-repair market",
        type: "Market sizing",
        difficulty: 2,
        prompt: "A walk-in phone-repair chain wants to know the size of Japan's annual consumer market for smartphone repairs (iPhone and Android; repairs at official stores count if paid per repair; warranty plans and business customers are excluded). Structure the estimate, and say which axis you'd segment by.",
        question: "Annual consumer smartphone-repair market in Japan",
        frames: [
          { name: "Driver chain: phones in use × failures × share repaired × price", pillars: [
            { id: "use", label: "Phones in use", kw: ["phones in use", "installed base", "smartphone user", "users", "owner", "ownership", "number of phone", "pengguna"], alt: ["population", "penetration", "phones per", "units per", "penduduk"], subs: [
              { label: "Population", kw: ["population", "people", "penduduk"] },
              { label: "Ownership rate", kw: ["ownership", "penetration", "own"] },
              { label: "Phones per person", kw: ["per person", "phones per", "units per", "devices per"] }
            ] },
            { id: "fail", label: "Failures per phone per year", kw: ["failure", "break", "broken", "damage", "fault", "rusak", "kerusakan"], alt: ["accident", "crack", "drop", "battery wear"], subs: [
              { label: "Device price / type (cheap, Android)", kw: ["android", "cheap", "budget", "low-price", "low price", "device price", "brand"] },
              { label: "Usage intensity (e.g. young users)", kw: ["usage", "heavy", "young", "intensity"] },
              { label: "How long phones are kept", kw: ["older", "years", "kept", "lifespan", "old phone", "age of"] }
            ] },
            { id: "share", label: "Share of failures repaired", kw: ["share repaired", "repair rate", "% repaired", "repaired", "repair vs replace", "decide to repair"], alt: ["replace", "warranty cover", "carrier", "insurance", "afford"], subs: [
              { label: "Maker / carrier cover", kw: ["warrant", "carrier", "insurance", "cover", "applecare"] },
              { label: "Repair vs replace decision", kw: ["replace", "new phone", "upgrade"] },
              { label: "Ability to pay / urgency", kw: ["afford", "income", "urgen", "finances"] }
            ] },
            { id: "price", label: "Price per repair", kw: ["price", "pric", "harga", "fee", "cost per repair", "revenue per repair", "average ticket"], alt: ["express", "add-on"], subs: [
              { label: "Repair type mix (screen, battery…)", kw: ["screen", "battery", "repair type", "mix"] },
              { label: "Express and add-on services", kw: ["express", "add-on", "premium", "same-day"] }
            ] }
          ] },
          { name: "Supply side: shops × revenue per shop", pillars: [
            { id: "shops", label: "Number of repair shops", kw: ["number of shop", "number of store", "shops", "stores", "outlets", "toko"], alt: ["density", "official store"], subs: [
              { label: "Shop density per population", kw: ["density", "per 100", "per capita", "per resident"] },
              { label: "Official vs independent shops", kw: ["official", "independent", "apple store", "carrier shop"] }
            ] },
            { id: "rev", label: "Revenue per shop", kw: ["revenue per shop", "sales per shop", "revenue per store", "sales per store", "per shop"], alt: ["repairs per day", "tsubo", "throughput"], subs: [
              { label: "Repairs per day", kw: ["per day", "throughput", "capacity"] },
              { label: "Average ticket", kw: ["ticket", "price", "average"] }
            ] }
          ] }
        ],
        priority: { kw: ["income", "failure", "break", "repair rate", "share repaired", "warrant", "segment", "pendapatan"], why: "Ownership and phones per person barely vary, so the estimate turns on failures per year and the share repaired. Both move with income (cheaper phones break more; richer owners have cover and repair more), so segment by income." },
        offs: [
          { kw: ["competit", "market share", "profit", "margin"], why: "Sizing asks how big the market is, not who wins it or how profitable it is." },
          { kw: ["corporate", "business customer", "b2b", "enterprise", "company phone"], why: "Business customers are excluded by the prompt." },
          { kw: ["plan revenue", "subscription", "plan fee"], why: "Warranty plans are excluded: customers pay per repair." }
        ],
        builder: {
          buckets: [
            { t: "Phones in use", ok: true }, { t: "Failures per phone per year", ok: true }, { t: "Share of failures repaired", ok: true }, { t: "Price per repair", ok: true },
            { t: "Repair shops in Tokyo", ok: false, why: "Supply-side and Tokyo-only: it mixes approaches and misses the rest of Japan." },
            { t: "iPhone", ok: false, why: "One device type. It belongs inside the drivers, not as a bucket." },
            { t: "Profit margin", ok: false, why: "Margins don't change the size of the market." }
          ],
          cards: [
            { t: "Japan's population", b: "Phones in use" },
            { t: "Smartphone ownership by income", b: "Phones in use" },
            { t: "Phones owned per person", b: "Phones in use" },
            { t: "Cheaper phones break more often", b: "Failures per phone per year" },
            { t: "Heavy users wear out batteries faster", b: "Failures per phone per year" },
            { t: "Phones kept for years fail more often", b: "Failures per phone per year" },
            { t: "Maker or carrier repair cover", b: "Share of failures repaired" },
            { t: "Choosing to repair rather than replace", b: "Share of failures repaired" },
            { t: "Standard price of a screen repair", b: "Price per repair" },
            { t: "Express and add-on service fees", b: "Price per repair" },
            { t: "Top chain's share of the market", b: null, why: "Who wins the market isn't part of how big it is." },
            { t: "Repairs of company-issued phones", b: null, why: "Business customers are excluded by the prompt." }
          ],
          priority: ["Failures per phone per year", "Share of failures repaired"]
        },
        takeaway: "Rate each driver's impact before you segment, then split by the axis that moves the high-impact drivers. Here income drives both how often phones break and how many get repaired."
      },
      /* ------------------------------------------------------------ */
      {
        id: "repair-growth",
        icon: "🚀",
        title: "Accelerating a repair chain",
        type: "Growth",
        difficulty: 3,
        prompt: "Company A runs five walk-in phone-repair shops in Tokyo's busy districts, mostly serving office workers in their 20s–40s with iPhones. Growth has slowed. A typical customer needs a repair only once every few years. How can A accelerate revenue growth over the next five years? Structure your answer.",
        question: "How can Company A accelerate revenue growth?",
        frames: [
          { name: "Revenue = new customers × repairs per customer × revenue per repair", pillars: [
            { id: "cust", label: "New customers", kw: ["new customer", "customer acquisition", "acquisition", "number of customer", "customers", "pelanggan baru"], alt: ["reach", "awareness", "tie-up", "partner", "seo", "new shop", "new store"], subs: [
              { label: "Reach new segments or regions", kw: ["segment", "region", "residential", "osaka", "senior", "android", "women", "teen"] },
              { label: "Be found when a phone breaks", kw: ["tie-up", "partner", "retailer", "seo", "map", "search", "awareness"] },
              { label: "Remove friction (online, on-site)", kw: ["online", "on-site", "onsite", "visit", "pickup", "same-day", "booking"] }
            ] },
            { id: "freq", label: "Repairs per customer", kw: ["frequency", "repairs per customer", "repeat", "retention", "per customer", "usage"], alt: ["loyalty", "check-up", "checkup"], subs: [
              { label: "Repeat visits and retention", kw: ["repeat", "loyal", "retention", "check"] }
            ] },
            { id: "rev", label: "Revenue per repair", kw: ["revenue per repair", "price per", "per repair", "average ticket", "ticket", "spend per"], alt: ["upsell", "cross-sell", "cross sell", "premium", "express", "add-on"], subs: [
              { label: "Premium / express pricing", kw: ["premium", "express", "same-day", "priority"] },
              { label: "Cross-sell and add-ons (battery, backup)", kw: ["cross", "battery", "add-on", "backup", "cleaning", "bundle"] }
            ] }
          ] },
          { name: "Where to play / How to win", pillars: [
            { id: "where", label: "Where to play", kw: ["where to play", "target", "where", "new market", "target market"], alt: ["region", "residential", "osaka", "senior", "teen", "android", "segment"], subs: [
              { label: "Regions (residential Tokyo, other cities)", kw: ["region", "residential", "osaka", "nagoya", "city", "area", "location"] },
              { label: "Customer profiles (seniors, teens, women, companies)", kw: ["senior", "teen", "women", "female", "student", "compan", "corporate", "profile", "demographic"] },
              { label: "Devices (Android)", kw: ["android", "device"] },
              { label: "Core vs new targets", kw: ["core", "existing", "new target", "current"] }
            ] },
            { id: "how", label: "How to win", kw: ["how to win", "win", "differentiat", "value proposition", "competitive advantage"], alt: ["pain point", "needs", "4p", "convenien", "speed"], subs: [
              { label: "Customer needs and pain points", kw: ["need", "pain", "speed", "fast", "time", "convenien"] },
              { label: "Competitors' offers", kw: ["competit", "rival", "official store", "peer"] },
              { label: "Our strengths", kw: ["strength", "capabilit", "advantage"] },
              { label: "Moves across the 4Ps", kw: ["price", "product", "promotion", "place", "same-day", "on-site", "online", "battery", "partner", "tie-up", "seo"] }
            ] }
          ] }
        ],
        priority: { kw: ["new customer", "revenue per repair", "price per", "ticket", "acquisition", "pain point", "same-day", "on-site", "online", "speed", "convenien", "where to play", "target", "rarely", "rare"], why: "Repairs are rare, so repairs per customer has little room. The upside is in new customers (be there, fast and convenient, when a phone breaks) and revenue per repair (express service, battery add-ons). Agree the target first." },
        offs: [
          { kw: ["cut cost", "reduce cost", "cost reduction", "lower rent", "headcount"], why: "The question is revenue growth. Cost cuts raise profit, not revenue." }
        ],
        builder: {
          buckets: [
            { t: "New customers", ok: true }, { t: "Repairs per customer", ok: true }, { t: "Revenue per repair", ok: true },
            { t: "Marketing", ok: false, why: "Marketing can lift every driver, so it overlaps with all three." },
            { t: "Ginza shop", ok: false, why: "One shop is a detail, not a growth driver." },
            { t: "Cost reduction", ok: false, why: "That answers a different question: profit, not revenue growth." }
          ],
          cards: [
            { t: "Tie-ups with big electronics retailers", b: "New customers" },
            { t: "Search and map-listing optimisation", b: "New customers" },
            { t: "Fully online booking for busy workers", b: "New customers" },
            { t: "Open shops in residential areas", b: "New customers" },
            { t: "Free yearly device check-up", b: "Repairs per customer" },
            { t: "Discount on a customer's next repair", b: "Repairs per customer" },
            { t: "Premium fee for same-day express repair", b: "Revenue per repair" },
            { t: "Battery replacement added to each repair", b: "Revenue per repair" },
            { t: "Paid data backup and cleaning add-ons", b: "Revenue per repair" },
            { t: "Negotiate lower rent in Ginza", b: null, why: "A cost lever, not revenue growth." },
            { t: "Cut technician headcount", b: null, why: "A cost lever, and it would reduce repair capacity." }
          ],
          priority: ["New customers", "Revenue per repair"]
        },
        takeaway: "Split growth into where to play and how to win, then tie each move to a revenue driver. Deprioritise the driver with no room: here, how often a customer needs a repair."
      }
    ]
  };
})();
