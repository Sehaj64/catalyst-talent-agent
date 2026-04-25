const jdInput = document.querySelector("#jdInput");
const analyzeBtn = document.querySelector("#analyzeBtn");
const loadSampleBtn = document.querySelector("#loadSampleBtn");
const loadSampleResumesBtn = document.querySelector("#loadSampleResumesBtn");
const exportBtn = document.querySelector("#exportBtn");
const topK = document.querySelector("#topK");
const simulateOutreach = document.querySelector("#simulateOutreach");
const includeSampleMarket = document.querySelector("#includeSampleMarket");
const resumeInput = document.querySelector("#resumeInput");
const resumeFile = document.querySelector("#resumeFile");
const statusText = document.querySelector("#statusText");
const summaryGrid = document.querySelector("#summaryGrid");
const recruiterBrief = document.querySelector("#recruiterBrief");
const parsedSpec = document.querySelector("#parsedSpec");
const searchStrategy = document.querySelector("#searchStrategy");
const candidateResults = document.querySelector("#candidateResults");
const stageStrip = document.querySelector("#stageStrip");

let latestRun = null;

async function loadSample() {
  const response = await fetch("/api/sample-jd");
  const data = await response.json();
  jdInput.value = data.job_description;
}

async function loadSampleResumes() {
  const response = await fetch("/api/sample-resumes");
  const data = await response.json();
  resumeInput.value = data.candidate_resumes;
  setStatus("Sample resumes loaded.");
}

function setStatus(text) {
  statusText.textContent = text;
}

function setStages(activeIndex = -1, done = false) {
  [...stageStrip.children].forEach((stage, index) => {
    stage.className = "stage";
    if (done || index < activeIndex) stage.classList.add("is-done");
    else if (index === activeIndex) stage.classList.add("is-active");
    else stage.classList.add("is-idle");
  });
}

async function analyze() {
  const job_description = jdInput.value.trim();
  if (job_description.length < 80) {
    setStatus("Add a fuller job description first.");
    jdInput.focus();
    return;
  }

  analyzeBtn.disabled = true;
  setStatus("Running agent...");
  setStages(0);
  summaryGrid.innerHTML = "";
  candidateResults.className = "empty-state large";
  candidateResults.textContent = "Parsing and scouting...";

  try {
    for (let i = 1; i <= 4; i += 1) {
      await new Promise((resolve) => setTimeout(resolve, 120));
      setStages(i);
    }

    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job_description,
        candidate_resumes: resumeInput.value.trim(),
        include_sample_market: includeSampleMarket.checked,
        top_k: Number(topK.value),
        simulate_outreach: simulateOutreach.checked,
      }),
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || "Analysis failed");
    }

    latestRun = await response.json();
    renderRun(latestRun);
    setStages(5, true);
    setStatus(`Ranked ${latestRun.ranked_shortlist.length} candidates.`);
  } catch (error) {
    setStatus("Run failed. Check the terminal.");
    candidateResults.className = "empty-state large";
    candidateResults.textContent = error.message;
  } finally {
    analyzeBtn.disabled = false;
  }
}

function renderRun(run) {
  renderSummary(run);
  renderRecruiterBrief(run.recruiter_brief);
  renderParsedSpec(run.job_spec);
  renderSearchStrategy(run.search_strategy, run.audit_log);
  renderCandidates(run.ranked_shortlist);
}

function renderSummary(run) {
  const summary = run.summary;
  summaryGrid.innerHTML = [
    metric("Shortlisted", summary.total_shortlisted),
    metric("Avg Match", summary.average_match_score),
    metric("Avg Interest", summary.average_interest_score),
    metric("Avg Confidence", summary.average_confidence_score),
  ].join("");
}

function renderRecruiterBrief(brief) {
  recruiterBrief.className = "brief-panel ready";
  recruiterBrief.innerHTML = `
    <h3>Recruiter Brief</h3>
    <p>${escapeHtml(brief.hiring_thesis)}</p>
    <div class="brief-grid">
      <div>
        <h4>Strategy</h4>
        <p>${escapeHtml(brief.shortlist_strategy)}</p>
      </div>
      <div>
        <h4>Sequence</h4>
        <ul>${brief.recommended_sequence.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div>
        <h4>Trade-offs</h4>
        <ul>${brief.top_tradeoffs.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
      <div>
        <h4>Compliance Audit</h4>
        <ul>${brief.compliance_audit.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>
    </div>
  `;
}

function metric(label, value) {
  return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`;
}

function renderParsedSpec(spec) {
  parsedSpec.className = "";
  parsedSpec.innerHTML = `
    <ul class="spec-list">
      <li><strong>Title:</strong> ${escapeHtml(spec.title)}</li>
      <li><strong>Seniority:</strong> ${escapeHtml(spec.seniority)} ${spec.min_years ? `(${spec.min_years}+ yrs)` : ""}</li>
      <li><strong>Location:</strong> ${escapeHtml(spec.location || "Not specified")} / ${escapeHtml(spec.remote_policy)}</li>
      <li><strong>Must-have:</strong> ${chips(spec.must_have_skills)}</li>
      <li><strong>Nice-to-have:</strong> ${chips(spec.nice_to_have_skills)}</li>
      <li><strong>Domains:</strong> ${chips(spec.domains)}</li>
    </ul>
  `;
}

function renderSearchStrategy(strategy, auditLog) {
  searchStrategy.className = "";
  searchStrategy.innerHTML = `
    <ul class="strategy-list">
      ${strategy.queries.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
    <div class="section-heading tight lower">
      <div>
        <p class="eyebrow">Audit</p>
        <h2>Trace</h2>
      </div>
    </div>
    <ul class="audit-list">
      ${auditLog.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
    </ul>
  `;
}

function renderCandidates(candidates) {
  candidateResults.className = "candidate-stack";
  candidateResults.innerHTML = candidates.map(renderCandidate).join("");
}

function renderCandidate(item) {
  const c = item.candidate;
  return `
    <article class="candidate-card">
      <div class="candidate-head">
        <div class="rank-badge">${item.rank}</div>
        <div class="candidate-title">
          <h3>${escapeHtml(c.name)}</h3>
          <p>${escapeHtml(c.headline)}</p>
          <p>${escapeHtml(c.location)} · ${c.years_experience} yrs · ${escapeHtml(c.current_title)}</p>
        </div>
        <span class="decision">${escapeHtml(item.decision)}</span>
      </div>
      <div class="candidate-body">
        <div class="score-row">
          ${scoreBox("Match", item.match_score, "match")}
          ${scoreBox("Interest", item.interest_score, "interest")}
          ${scoreBox("Combined", item.combined_score, "combined")}
          ${scoreBox("Confidence", item.confidence_score, "confidence")}
        </div>
        <p class="explanation">${escapeHtml(item.match_explanation)}</p>
        <div class="chip-row">${chips(item.matched_skills)}${chips(item.missing_skills, "warn")}</div>
        <details>
          <summary>Evidence, outreach, and next action</summary>
          <div class="detail-grid">
            <div class="detail-block">
              <h4>Outreach Hook</h4>
              <p>${escapeHtml(item.outreach_hook)}</p>
            </div>
            <div class="detail-block">
              <h4>Counterfactual</h4>
              <p>${escapeHtml(item.counterfactual)}</p>
            </div>
            <div class="detail-block">
              <h4>Score Breakdown</h4>
              <ul class="plain-list">
                ${Object.entries(item.score_breakdown)
                  .map(([key, value]) => `<li>${escapeHtml(labelize(key))}: ${escapeHtml(String(value))}</li>`)
                  .join("")}
              </ul>
            </div>
            <div class="detail-block">
              <h4>Next Steps</h4>
              <ul class="plain-list">${item.next_steps.map((step) => `<li>${escapeHtml(step)}</li>`).join("")}</ul>
            </div>
            <div class="detail-block full">
              <h4>Evidence Paths</h4>
              <ul class="plain-list">
                ${item.evidence_paths
                  .map((path) => `<li><strong>${escapeHtml(path.claim)}</strong> (${escapeHtml(String(Math.round(path.confidence * 100)))}%): ${escapeHtml(path.evidence)}</li>`)
                  .join("")}
              </ul>
            </div>
            <div class="detail-block">
              <h4>Risk Signals</h4>
              ${renderRisks(item.risk_signals)}
            </div>
            <div class="detail-block">
              <h4>Interview Questions</h4>
              <ul class="plain-list">${item.interview_questions.map((question) => `<li>${escapeHtml(question)}</li>`).join("")}</ul>
            </div>
            <div class="detail-block">
              <h4>Candidate Evidence</h4>
              <ul class="plain-list">${c.evidence.slice(0, 3).map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>
            </div>
            <div class="detail-block">
              <h4>Transcript</h4>
              <div class="transcript">
                ${item.transcript.map(renderTurn).join("")}
              </div>
            </div>
          </div>
        </details>
      </div>
    </article>
  `;
}

function renderRisks(risks) {
  if (!risks || risks.length === 0) {
    return "<p>No major first-pass risk detected.</p>";
  }
  return risks
    .map(
      (risk) => `
        <p><span class="risk-pill ${escapeHtml(risk.severity)}">${escapeHtml(risk.severity)}</span><strong>${escapeHtml(risk.label)}</strong></p>
        <p>${escapeHtml(risk.rationale)} ${escapeHtml(risk.mitigation)}</p>
      `,
    )
    .join("");
}

function scoreBox(label, value, className) {
  return `
    <div class="score-box">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
      <div class="bar ${className}"><i style="width: ${Math.max(0, Math.min(100, value))}%"></i></div>
    </div>
  `;
}

function renderTurn(turn) {
  return `
    <div class="turn ${turn.speaker}">
      <strong>${escapeHtml(turn.speaker)} · ${escapeHtml(turn.intent)}</strong>
      <span>${escapeHtml(turn.message)}</span>
    </div>
  `;
}

function chips(items, type = "") {
  if (!items || items.length === 0) return `<span class="chip">None</span>`;
  return items.map((item) => `<span class="chip ${type}">${escapeHtml(item)}</span>`).join("");
}

function labelize(key) {
  return key.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function exportLatest() {
  if (!latestRun) {
    setStatus("Run the agent before exporting.");
    return;
  }
  const blob = new Blob([JSON.stringify(latestRun, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "talent-signal-agent-output.json";
  link.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadSampleBtn.addEventListener("click", loadSample);
loadSampleResumesBtn.addEventListener("click", loadSampleResumes);
analyzeBtn.addEventListener("click", analyze);
exportBtn.addEventListener("click", exportLatest);
resumeFile.addEventListener("change", async () => {
  const file = resumeFile.files && resumeFile.files[0];
  if (!file) return;
  resumeInput.value = await file.text();
  setStatus(`Imported ${file.name}.`);
});
loadSample();
loadSampleResumes();
