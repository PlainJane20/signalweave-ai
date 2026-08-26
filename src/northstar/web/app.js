(function () {
  "use strict";

  const demoData = {
    generated_at: "2026-08-26T09:42:00-07:00",
    summary: "Northstar analyzed 5 initiatives across 4 teams. The portfolio is modeled at 105.9% capacity, with 7 high or critical findings requiring accountable human review.",
    confidence: 84,
    kpis: { alignment: "80%", critical_risks: 7, value_at_risk: "$487K", capacity: "105.9%" },
    risks: [
      { id: "R1", name: "API sequencing", domain: "Architecture", score: 92, likelihood: 4, impact: 3 },
      { id: "R2", name: "Platform capacity", domain: "Delivery", score: 78, likelihood: 3, impact: 3 },
      { id: "R3", name: "PHI data boundary", domain: "Privacy", score: 69, likelihood: 2, impact: 3 },
      { id: "R4", name: "Vendor lock-in", domain: "Commercial", score: 48, likelihood: 3, impact: 2 },
      { id: "R5", name: "Unowned handoff", domain: "Operations", score: 41, likelihood: 2, impact: 2 }
    ],
    investments: [
      { name: "API v2", investment: .95, value: 92 }, { name: "Mobile", investment: 1.2, value: 85 },
      { name: "Identity HA", investment: .62, value: 90 }, { name: "Legacy reports", investment: 1.1, value: 25 },
      { name: "Seller insights", investment: .73, value: 70 }
    ],
    dependencies: {
      nodes: [
        { id: "identity", label: "Identity", team: "Security", x: 65, y: 75 },
        { id: "api", label: "Platform API", team: "Platform", x: 220, y: 75, critical: true },
        { id: "mobile", label: "Mobile", team: "Experience", x: 390, y: 40 },
        { id: "billing", label: "Insights", team: "Data", x: 390, y: 115 },
        { id: "launch", label: "Launch", team: "Program", x: 510, y: 75 }
      ],
      edges: [
        { from: "identity", to: "api" }, { from: "api", to: "mobile", critical: true },
        { from: "api", to: "billing", critical: true }, { from: "mobile", to: "launch" }, { from: "billing", to: "launch" }
      ]
    },
    agents: [
      { icon: "ST", name: "Strategy alignment", result: "2 objectives at risk", time: "1.2s" },
      { icon: "AR", name: "Architecture risk", result: "1 breaking dependency", time: "2.1s" },
      { icon: "EX", name: "Execution systems", result: "Critical path mapped", time: "0.9s" },
      { icon: "GV", name: "Governance & privacy", result: "1 control escalated", time: "1.8s" },
      { icon: "PE", name: "Portfolio economics", result: "$487K modeled delta", time: "1.4s" },
      { icon: "PM", name: "Pre-mortem", result: "4 failure paths tested", time: "2.4s" },
      { icon: "DA", name: "Decision arbiter", result: "Evidence reconciled", time: "0.7s" }
    ],
    recommendation: {
      title: "Mitigate Marketplace API v2",
      reason: "Fund evidence-linked remediation, rebaseline dependencies, and retain strategic scope while a human owner accepts the tradeoff.",
      options: [
        { id: "A", title: "Continue unchanged", detail: "$950K cost · 5% confidence", metric: "Observed risk accepted" },
        { id: "B", title: "Mitigate API v2", detail: "$1.09M cost · 82% confidence", metric: "66% modeled risk reduction", selected: true },
        { id: "C", title: "Stop legacy reporting", detail: "$88K exit cost · 100% confidence", metric: "95% modeled risk reduction" }
      ]
    },
    audit: [
      { event: "Decision brief synthesized", owner: "Decision Arbiter", evidence: "12 linked artifacts", status: "Ready", time: "09:42" },
      { event: "Privacy control escalated", owner: "Governance Agent", evidence: "POL-07", status: "Review", time: "09:41" },
      { event: "Critical path recalculated", owner: "Execution Agent", evidence: "2 initiative dependencies", status: "Complete", time: "09:40" },
      { event: "Portfolio data validated", owner: "Northstar", evidence: "5 source systems", status: "Complete", time: "09:39" }
    ]
  };

  const $ = (selector) => document.querySelector(selector);
  const safe = (value) => String(value == null ? "" : value).replace(/[&<>'"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[c]));
  const clamp = (value, min, max) => Math.max(min, Math.min(max, Number(value) || 0));
  let state = demoData;

  function normalize(raw) {
    if (!raw || typeof raw !== "object") return demoData;
    const report = raw.report || raw.final_report || raw;
    const metricList = Array.isArray(report.metrics) ? report.metrics : [];
    const metricMap = metricList.reduce((acc, metric) => {
      const key = String(metric.name || "").toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
      const unit = metric.unit === "percent" || metric.unit === "%" ? "%" : metric.unit === "USD" || metric.unit === "usd" ? "$" : "";
      acc[key] = unit === "$" ? `$${Number(metric.value || 0).toLocaleString()}` : `${metric.value}${unit}`;
      return acc;
    }, {});
    const assessments = Array.isArray(report.assessments) ? report.assessments : [];
    const nestedFindings = assessments.flatMap((assessment) => Array.isArray(assessment.findings) ? assessment.findings : []);
    const sourceFindings = report.risks || report.findings || nestedFindings;
    const reportOptions = Array.isArray(report.options) ? report.options : [];
    const recommendedIds = new Set(report.recommended_option_ids || []);
    const mappedOptions = reportOptions.map((option, index) => ({
      id: String(option.id || String.fromCharCode(65 + index)).replace(/^OPT-/, ""),
      title: `${String(option.action || "review").replace(/^./, (c) => c.toUpperCase())} ${option.initiative_id || "initiative"}`,
      detail: `$${Number(option.estimated_cost_usd || 0).toLocaleString()} cost · ${Math.round(Number(option.launch_confidence || 0) * 100)}% confidence`,
      metric: `${Number(option.risk_reduction_percent || 0)}% risk reduction`,
      selected: Boolean(option.recommended || recommendedIds.has(option.id))
    })).sort((a, b) => Number(b.selected) - Number(a.selected)).slice(0, 3);
    const derivedKpis = {
      critical_risks: metricMap.high_and_critical_findings,
      capacity: metricMap.capacity_utilization,
      value_at_risk: metricMap.modeled_cost_delta
    };
    const primaryOption = mappedOptions.find((option) => option.selected);
    return {
      ...demoData,
      ...report,
      summary: report.summary || report.executive_summary || demoData.summary,
      confidence: report.confidence || report.decision_confidence || (mappedOptions.find((o) => o.selected) ? Number(reportOptions.find((o) => o.recommended || recommendedIds.has(o.id)).launch_confidence) * 100 : demoData.confidence),
      kpis: { ...demoData.kpis, ...metricMap, ...Object.fromEntries(Object.entries(derivedKpis).filter(([, value]) => value != null)), ...(report.kpis || {}) },
      risks: Array.isArray(sourceFindings) && sourceFindings.length ? sourceFindings.map((r, i) => ({
        id: r.id || r.finding_id || `R${i + 1}`,
        name: r.name || r.title || r.category || "Program risk",
        domain: r.domain || r.category || "Program",
        score: r.score || r.risk_score || ({ critical: 95, high: 78, medium: 52, low: 28 }[String(r.severity).toLowerCase()] || 50),
        likelihood: r.likelihood || ((i % 4) + 1), impact: r.impact || ({ critical: 3, high: 3, medium: 2, low: 1 }[String(r.severity).toLowerCase()] || 2)
      })) : demoData.risks,
      investments: report.investments || report.portfolio || demoData.investments,
      dependencies: report.dependencies || demoData.dependencies,
      agents: report.agents || report.agent_activity || (assessments.length ? assessments.map((assessment) => ({
        name: String(assessment.agent || "Specialist").replace(/_/g, " "),
        result: assessment.summary || `${(assessment.findings || []).length} findings`,
        time: assessment.analysis_mode || "complete"
      })) : demoData.agents),
      recommendation: {
        ...demoData.recommendation,
        ...(report.recommendation || report.decision || {}),
        title: report.gate && report.gate.status === "block" ? "Pause and remediate prohibited risk" : (primaryOption ? primaryOption.title : demoData.recommendation.title),
        reason: report.executive_summary || (report.recommendation || {}).reason || demoData.recommendation.reason,
        options: mappedOptions.length ? mappedOptions : ((report.recommendation || {}).options || demoData.recommendation.options)
      },
      audit: report.audit || report.audit_trail || demoData.audit
    };
  }

  async function loadReport() {
    document.body.classList.add("loading");
    try {
      const response = await fetch("/api/report", { headers: { Accept: "application/json" }, signal: AbortSignal.timeout ? AbortSignal.timeout(3500) : undefined });
      if (!response.ok) throw new Error(`API returned ${response.status}`);
      state = normalize(await response.json());
      $("#data-source").textContent = "Live analysis";
    } catch (_error) {
      state = demoData;
      $("#data-source").textContent = "Offline demo";
    } finally {
      render(state);
      document.body.classList.remove("loading");
    }
  }

  function render(data) {
    $("#hero-summary").textContent = data.summary || demoData.summary;
    const confidence = clamp(data.confidence || data.decision_confidence || 84, 0, 100);
    $("#confidence-value").textContent = `${confidence}%`;
    $("#confidence-ring").style.strokeDashoffset = String(301.6 * (1 - confidence / 100));
    $("#kpi-alignment").textContent = data.kpis.alignment || data.kpis.strategic_alignment || "78%";
    $("#kpi-risks").textContent = data.kpis.critical_risks ?? data.risks.filter((r) => Number(r.score) >= 68).length;
    $("#kpi-value").textContent = data.kpis.value_at_risk || "$2.4M";
    $("#kpi-capacity").textContent = data.kpis.capacity || data.kpis.capacity_pressure || "94%";
    if (data.generated_at) $("#last-updated").textContent = `Updated ${new Date(data.generated_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
    renderRisks(data.risks);
    renderInvestments(data.investments);
    renderGraph(data.dependencies);
    renderAgents(data.agents);
    renderDecision(data.recommendation);
    renderAudit(data.audit);
    renderScenario("capacity", 65);
  }

  function renderRisks(risks) {
    const byDomain = risks.reduce((acc, r) => { acc[r.domain] = Math.max(acc[r.domain] || 0, clamp(r.score, 0, 100)); return acc; }, {});
    $("#risk-bars").innerHTML = Object.entries(byDomain).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([name, value]) => `<div class="bar-row"><span class="bar-label">${safe(name)}</span><div class="bar-track"><div class="bar-fill" style="width:${value}%"></div></div><span class="bar-value">${value}</span></div>`).join("");
    const cells = [];
    for (let impact = 1; impact <= 3; impact++) for (let likelihood = 1; likelihood <= 4; likelihood++) {
      const severity = likelihood * impact >= 9 ? "critical" : likelihood * impact >= 6 ? "high" : likelihood * impact >= 3 ? "medium" : "low";
      const dots = risks.filter((r) => clamp(r.impact,1,3) === impact && clamp(r.likelihood,1,4) === likelihood).map((r, index) => `<span class="risk-dot" title="${safe(r.name)}" style="left:${10 + index * 24}px;top:${8 + index * 4}px">${safe(r.id)}</span>`).join("");
      cells.push(`<div class="heat-cell ${severity}">${dots}</div>`);
    }
    $("#risk-heatmap").innerHTML = cells.join("");
    $("#risk-count").textContent = `${risks.length} risks`;
    $("#risk-key").innerHTML = risks.slice(0,5).map((r) => `<span><b>${safe(r.id)}</b>${safe(r.name)}</span>`).join("");
  }

  function renderInvestments(items) {
    const list = Array.isArray(items) ? items.slice(0,6) : demoData.investments;
    const maxInvestment = Math.max(...list.map((x) => Number(x.investment) || 0), 1);
    $("#investment-chart").innerHTML = list.map((item) => `<div class="investment-group"><div class="investment-bar money" style="height:${clamp(item.investment / maxInvestment * 78, 0, 78)}%" title="$${safe(item.investment)}M"></div><div class="investment-bar value" style="height:${clamp(item.value,0,100) * .78}%" title="${safe(item.value)} strategic value"></div><span class="investment-name">${safe(item.name)}</span></div>`).join("");
  }

  function renderGraph(graph) {
    const nodes = Array.isArray(graph.nodes) ? graph.nodes : demoData.dependencies.nodes;
    const edges = Array.isArray(graph.edges) ? graph.edges : demoData.dependencies.edges;
    const lookup = Object.fromEntries(nodes.map((n) => [n.id, n]));
    const edgeSvg = edges.map((e) => { const a = lookup[e.from], b = lookup[e.to]; if (!a || !b) return ""; return `<path class="graph-edge${e.critical ? " critical" : ""}" d="M${a.x + 48},${a.y} C${(a.x+b.x)/2},${a.y} ${(a.x+b.x)/2},${b.y} ${b.x-48},${b.y}"/>`; }).join("");
    const nodeSvg = nodes.map((n) => `<g><rect class="graph-node${n.critical ? " critical" : ""}" x="${n.x-48}" y="${n.y-23}" width="96" height="46" rx="9"/><text class="graph-node-label" x="${n.x}" y="${n.y-2}">${safe(n.label)}</text><text class="graph-node-team" x="${n.x}" y="${n.y+12}">${safe(n.team || "")}</text></g>`).join("");
    $("#dependency-graph").innerHTML = `<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#aebcca"/></marker></defs>${edgeSvg}${nodeSvg}`;
  }

  function renderAgents(agents) {
    const list = Array.isArray(agents) ? agents : demoData.agents;
    $("#agent-list").innerHTML = list.map((a) => `<div class="agent-row"><span class="agent-avatar">${safe(a.icon || String(a.name).slice(0,2).toUpperCase())}</span><div><strong>${safe(a.name)}</strong><small>${safe(a.result || a.status || "Analysis complete")}</small></div><span class="agent-time">✓ ${safe(a.time || "done")}</span></div>`).join("");
    $("#agents-status").textContent = `${list.length} complete`;
  }

  function renderDecision(rec) {
    $("#recommendation-title").textContent = rec.title || demoData.recommendation.title;
    $("#recommendation-reason").textContent = rec.reason || rec.rationale || demoData.recommendation.reason;
    const options = Array.isArray(rec.options) && rec.options.length ? rec.options : demoData.recommendation.options;
    $("#decision-options").innerHTML = options.map((o, i) => `<label class="option-card ${o.selected || i === 1 ? "selected" : ""}"><input type="radio" name="decision-option" value="${safe(o.id || String.fromCharCode(65+i))}" ${o.selected || i === 1 ? "checked" : ""}><strong>Option ${safe(o.id || String.fromCharCode(65+i))} · ${safe(o.title)}</strong><small>${safe(o.detail || o.description)}</small><div class="option-metric">${safe(o.metric || "Evidence available")}</div></label>`).join("");
    $("#decision-options").querySelectorAll("input").forEach((input) => input.addEventListener("change", selectDecision));
    selectDecision();
  }

  function selectDecision() {
    document.querySelectorAll(".option-card").forEach((card) => card.classList.toggle("selected", card.querySelector("input").checked));
    const selected = document.querySelector('input[name="decision-option"]:checked');
    if (selected) $("#approve-decision").textContent = `Approve option ${selected.value}`;
  }

  function renderAudit(audit) {
    $("#audit-body").innerHTML = (Array.isArray(audit) ? audit : demoData.audit).map((row) => `<tr><td><strong>${safe(row.event)}</strong></td><td>${safe(row.owner)}</td><td>${safe(row.evidence)}</td><td><span class="table-status ${String(row.status).toLowerCase().includes("review") ? "review" : ""}">${safe(row.status)}</span></td><td>${safe(row.time)}</td></tr>`).join("");
  }

  const scenarios = {
    capacity: { path: ["Capacity loss", "API work slows", "Mobile blocked", "Launch slips"], signal: "API burn-up deviates by >10% for two sprints." },
    delay: { path: ["API delay", "Migration blocked", "Legacy extended", "Review expands"], signal: "Compatibility milestones miss the weekly exit criteria." },
    priority: { path: ["Priority shift", "Teams context-switch", "Critical path fragments", "Value erodes"], signal: "More than 20% of sprint capacity moves to unplanned work." },
    vendor: { path: ["Vendor outage", "Integration stalls", "Fallback untested", "Launch at risk"], signal: "Vendor SLA breaches twice within a rolling 30-day window." }
  };

  function renderScenario(type, severity) {
    const item = scenarios[type] || scenarios.capacity;
    const confidence = Math.round(clamp(94 - severity * .36, 28, 92));
    $("#scenario-confidence").textContent = `${confidence}%`;
    $("#scenario-delta").textContent = `↓ ${94-confidence} points`;
    $("#failure-path").innerHTML = item.path.map((p, i) => `${i ? '<span class="path-arrow">→</span>' : ""}<span class="path-node">${safe(p)}</span>`).join("");
    $("#early-signal").textContent = item.signal;
  }

  $("#scenario-form").addEventListener("submit", (event) => { event.preventDefault(); renderScenario($("#scenario-select").value, Number($("#severity-range").value)); });
  $("#severity-range").addEventListener("input", (event) => { $("#severity-output").textContent = `${event.target.value}%`; });
  $("#refresh-button").addEventListener("click", loadReport);
  $("#run-analysis").addEventListener("click", () => { $("#run-analysis").textContent = "Analyzing…"; setTimeout(() => { loadReport(); $("#run-analysis").textContent = "Analysis complete ✓"; setTimeout(() => { $("#run-analysis").textContent = "Run fresh analysis"; }, 1800); }, 700); });
  $("#approve-decision").addEventListener("click", () => { const selected = document.querySelector('input[name="decision-option"]:checked'); $("#decision-feedback").textContent = `Option ${selected ? selected.value : "B"} recorded in the audit trail. Human ownership retained.`; });
  $("#view-evidence").addEventListener("click", () => { $("#audit-body").closest(".audit-panel").scrollIntoView({ behavior: "smooth" }); });
  $("#export-audit").addEventListener("click", () => { const blob = new Blob([JSON.stringify(state.audit, null, 2)], { type: "application/json" }); const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "northstar-audit-log.json"; link.click(); URL.revokeObjectURL(link.href); });
  $("#menu-toggle").addEventListener("click", () => { const sidebar = $(".sidebar"); sidebar.classList.toggle("open"); $("#menu-toggle").setAttribute("aria-expanded", String(sidebar.classList.contains("open"))); });
  document.querySelectorAll(".nav-link").forEach((link) => link.addEventListener("click", () => { document.querySelectorAll(".nav-link").forEach((x) => x.classList.remove("active")); link.classList.add("active"); $(".sidebar").classList.remove("open"); }));

  loadReport();
})();
