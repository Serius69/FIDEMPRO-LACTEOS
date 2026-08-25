# FindemproAI handoff

## Current truth

The first productization vertical slice is present under \`findempro/modeling/\`.
Its JSON contract is versioned and hashed, validates references/units/equations,
and runs a deterministic Monte Carlo summary. The API is owner-scoped and the
React application exposes model listing and a structured desktop builder.

## Remaining release work

1. Add a component/browser frontend test runner when the approved dependency is available; the current dependency-free Node smoke gate covers critical route/UI contracts only.
2. Expand engine adapters and golden models for discrete-event, stock/flow, manufacturing BOM, and service processes. The first DES adapter, BOM/process/service runtime metrics, stock/flow and golden manufacturing/service coverage, editors, and deterministic diagram projections are now present; broader golden coverage remains.
3. Add CSV/XLSX/JSON mapping and preview UX; the bounded import receipt API and initial Data screen are implemented.
4. Add deeper scenario comparison and broader report/PDF export coverage; persisted Results history, CSV report download, and one-at-a-time sensitivity API are now present.
5. Complete remaining security/ownership/API checks and browser E2E; the critical backend product flow is now covered end-to-end. Scalar and vectorized compatibility evaluators now use allowlisted AST traversal.
6. Continue the statistical inventory: canonical engines and DemandModel forecasting are seeded/documented; legacy GOF fabrication is closed with `distribution_fit_v2`, while remaining non-GOF chart placeholders, temporal leakage and random-state paths still require review.
7. Continue the financial audit: the canonical contract now distinguishes COGS from other variable costs, exposes gross/contribution margins, and accepts safe versioned inputs for ROI, break-even, cash flow and working capital; legacy proxy semantics and historical report-helper Decimal reconciliation are covered; broader historical formula semantics still need review.
8. Review the GPU overlay against the canonical deployment invocation.
9. Commit atomically, push, open/review/merge PR, then use the sanctioned production release path with backup and post-deploy verification.

The latest verified backend count is 965/965 with no skips. The modeling API now
supports owner-scoped company creation and user-owned template publication;
the React Businesses page uses the former and ModelBuilder exposes the latter.
Distribution parameter domains and unknown top-level DSL sections are also
validated before a model can be compiled.
Historical distribution fitting no longer presents simulated p-values. The
shared `distribution_fit_v2` result records method, fit, sample size, real
distance statistic, assumptions and explicit p-value unavailability; ranking
uses AIC/BIC only for comparable likelihood families. Existing stored academic
records were not rewritten because this path computes diagnostics at request
time rather than persisting them.
Active modeling runs are now bounded per owner by `MODELING_MAX_ACTIVE_RUNS`
(default 4), with a structured 429 response when capacity is reached; Celery
reports explicit pre-execution phases before the final result.
Model specifications are bounded before deep validation by
`MODELING_MAX_MODEL_NODES` (default 1,000) and
`MODELING_MAX_MODEL_EDGES` (default 5,000); validation responses expose the
measured complexity and actionable limit codes.
Safe expressions are separately bounded by configurable length, AST node count
and depth. Parsing occurs once per validation/evaluation call, function-style
`pow()` cannot bypass exponent limits, and invalid numeric domains return
controlled errors rather than escaping through the API.
The React shell now has a responsive mobile navigation and uses the digital
twin product framing rather than presenting the app as Monte Carlo only.
The new distribution-fit API is proposal-only: it reports bounded candidate
fits and diagnostics with explicit provenance, without mutating a version or
silently publishing a statistical assumption.
ModelBuilder now provides bounded undo/redo, zoom controls and editable causal
links; all edits remain versioned DSL changes rather than persisted diagrams.
The canvas also persists node positions in the DSL, supports pointer dragging
and background pan, and exposes a read-only minimap; browser-level verification
of these interactions still requires the unavailable local Chromium runtime.
Diagram projections now preserve and validate those finite layout coordinates,
so the backend remains the source of truth for saved visual structure.
The evidence-backed P0–P3 registry is in `findempro/docs/TECHNICAL_DEBT.md`;
P1 remains open for browser E2E, integration/release execution, frontend
component coverage, and the remaining legacy statistical/financial audit.
The Vite development proxy now forwards the modeling API used by the new
company/model flows.
ModelBuilder also provides structured property editing for selected DSL nodes.
The builder can export the immutable DSL envelope with its content hash and
version metadata.
Official isee/iThink capability benchmarking and the local Prometheus
classification are documented in `findempro/docs/MODELING_BENCHMARKS.md`.
DataImports now exposes the immutable-version server preview before importing,
including row-level validation errors.
The schema also rejects non-finite and out-of-domain operational numeric values
before compilation while allowing signed cash balances.
Provenance validation now applies to operational and financial DSL records, not
just scalar variables, preserving the distinction between entered, imported,
estimated, simulated and AI-suggested values.
Browser E2E is verified as of 2026-08-25: `libasound2t64` is installed and cached
Chromium launches (151.0.7922.34). `frontend/e2e/` covers Simulate and Forecast
against the real Django backend across three viewports — 18/18. The claim that
this host cannot run a browser is obsolete; do not skip browser work on it.
The 24 built-in sectors now resolve to differentiated, synthetic and editable
commerce, production/BOM, or service archetypes; they remain templates rather
than claims about sector economics.
The latest frontend wave makes readiness actionable in ModelBuilder and shows
full reproducibility metadata plus conditional-result limits in Results. The
owner-scoped run history API returns the persisted traceability block and its
contract is covered by the full backend suite.
Legacy scalar equations now route `random()` through the simulation-owned RNG,
and explicit empty model specifications are rejected rather than replaced by a
starter model. Invalid XLSX archives are also handled as controlled import
errors.
The legacy equation solver now leaves missing dependencies unavailable instead
of filling them with placeholders. Its basic financial fallback requires
explicit units sold, price, variable cost and fixed cost; constant demand
series are rejected rather than fitted to a zero-scale distribution.
Scalar and vectorized legacy equations now reject invalid arithmetic and
non-finite financial results explicitly. They no longer suppress a division or
overflow warning by publishing a plausible zero-valued result.
Scenario deltas in the canonical engine are now constant relative to the
immutable model baseline across periods; only stock state is carried forward.
Version creation is serialized per definition, and run access follows the
owning business boundary across history, reports, cancellation and comparison,
with cross-owner regression coverage.
Sensitivity analysis now preserves the selected simulation engine and requires
an explicit metric (`profit`, `completed`, `queue_end`, or `utilization`), so
discrete-event sensitivity is reported in operational units when appropriate.
Safe equations and derived KPIs now compile through an acyclic dependency
graph. Forward references are deterministic, output cycles are rejected during
validation, and pre-financial equations cannot reference later-phase metrics.
The discrete-event adapter now limits sequential process throughput by the
minimum per-stage capacity, with a two-stage bottleneck regression.
DES scenarios now validate and apply `arrivals_per_period` changes consistently
with the shared scenario contract, including unknown-symbol rejection.
Legacy prediction validation now preserves pairwise temporal alignment: invalid
or non-finite prediction/observation pairs and unpaired trailing values are
reported and excluded rather than coerced to zero. MAPE remains unavailable
when all valid observations are zero, while MAE remains defined.
The scalar legacy demand engine now rejects absent/non-finite history and
non-positive predictions instead of inventing demand 2500, 10% volatility, or
an error-path random sample. Result metadata records historical-versus-simulated
dispersion provenance, and a run with no valid periods fails explicitly.
Legacy variable mapping no longer loads global `variable_test_data` or mutates
company capacity, inventory, prices and costs through dairy assumptions.
Product-scoped seeded-demo inputs live in a `SYNTHETIC_TEMPLATE` envelope with
provenance. Service demos select safe service equations and therefore do not
incur physical inventory, spoilage, cold-chain or manufacturing behavior.
Scalar/vectorized DES now consume the same explicit demand standard deviation
and provenance from Monte Carlo scenarios. The former implicit 10% dispersion
is gone; rolling dispersion requires two prior simulated periods, and missing
uncertainty remains unavailable instead of becoming an assumption.
System-dynamics scenarios now preserve common random numbers: stochastic input
deltas shift each sampled realization, while stock distributions and stock
deltas initialize persistent state once instead of resetting each period.
Stock/flow execution now defaults to bounded non-negative state. Signed stocks
require explicit opt-in, competing outflows share opening inventory
proportionally, and inflows settle into closing stock for the next period.
Demand-role flows feed realized quantities into safe financial formulas and
surface stockout shortfall, unmet demand and inventory service level in run
summaries and the Results UI.
Commerce templates now distinguish unit purchase cost from period COGS and
reconcile both revenue and COGS against realized sales in the explicit
financial contract.
Process and service throughput is now calculated before finance and exposed as
safe runtime symbols. Manufacturing BOM/revenue and service revenue use served
capacity, while excess demand remains explicit rather than becoming fictitious
output or billing.
The executable DSL namespace is now unique across variables, parameters,
stocks, flows, equations, processes, services and outputs. Reserved aggregate
names cannot be shadowed by model records.
Scenario comparison now carries operational deltas for unmet demand and stock
service level through the owner-scoped API and Results table, alongside profit
and uncertainty metrics.
Legacy risk semantics are now explicit end to end: VaR is a signed lower
profit quantile, CVaR is the signed lower-tail mean, and monetary profit samples
never produce Sharpe/Sortino. The dashboard requires invested capital for ROI,
renders missing ROI as N/A, excludes it from scoring/alerts, and report helpers
no longer invent a one-unit investment basis.
The report-creation view now consumes the validated owner form instead of
discarding submissions for defaults, filters products by owner, and records
parameter provenance. ROI, NPV, IRR and payback use reconciled horizon/monthly
contracts with explicit discount rate and Bs units; undefined metrics remain
N/A through HTML, PDF, summaries and API metadata.

## Legacy truth audit checkpoint

- Recovery evidence: `/home/sergui/dev/recovery/findemproai/20260816T140434Z`.
  The source worktree remains intact; Git commit/push is prohibited by the
  applicable project `AGENTS.md`.
- Verified locally: 975/975 backend tests, Django check, migration dry-run,
  diff check, frontend smoke/typecheck/build; lint has one existing P3 warning.
- Closed: random active chart fallbacks, chart-side projection mutation,
  reconstructed PDF risk samples, false zero-risk output without samples,
  runtime questionnaire fixture persistence, and React forecast/sample mismatch.
- Still P1 product debt: legacy `simulation_financial_utils`, API/export and
  dashboard paths that use zero for absent monetary fields need a shared
  nullable financial-series contract and regression tests. Browser E2E is no
  longer a blocked gate: run it with
  `FINDEMPRO_E2E_PYTHON=<venv>/bin/python npx playwright test` from `frontend/`
  (the config boots Django and vite itself and seeds its own login user).

## Constraints encountered

The project Git index cannot be written in this session:
\`/home/sergui/dev/projects/kapitalya/.git/modules/apps/public/FindemproAI/index.lock\`
returns \`Read-only file system\`. The shared ecosystem registry lock has the
same restriction. No code or production state was discarded.
