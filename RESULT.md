# FindemproAI implementation result

Status: RUNNING / UNVERIFIED FOR RELEASE

## Verified in this wave

- Canonical branch: \`ecosystem/findemproai/fase1\`
- Existing Prometheus alias commit preserved at \`379c38c43\`
- Backend: 965 collected, 965 passed, 0 failed, 0 skipped
- Django check and migration drift check pass with \`findempro.settings.testing\`
- Frontend typecheck, lint, and production build pass; lint retains one pre-existing warning in \`TooltipSimple.tsx\`
- Development and production compose configurations validate; the GPU file is a valid production override when composed with `docker-compose.prod.yml` and is intentionally invalid as a standalone file
- New versioned \`BusinessModelDefinition\`/template/scenario/run domain
- Safe expression and unit validation with no \`eval\`/\`exec\`
- Deterministic model hashing, immutable versions, owner-scoped API
- Monte Carlo execution with injected seed and persisted run metadata
- Scenario creation/selection in the builder and bounded JSON/CSV/XLSX import receipts
- Sector starter registry with 23 editable synthetic templates
- BOM, service blueprint, process, stock/flow, distribution, scenario, and readiness validation
- Versioned BOM editor and process/service editor in the frontend
- Critical owner API flow test covers template → model → BOM/process → import → validation → scenario → simulation → result
- Persisted results history with owner isolation and uncertainty summary UI
- Traceable CSV report export includes business, model version/hash, scenario, engine, seed, summary metrics, and limitations
- Sharpe/Sortino are marked not applicable for monetary profit samples; VaR/CVaR confidence is explicit
- Legacy VaR/CVaR payloads now identify their signed lower-profit-quantile/lower-tail-mean semantics consistently across engine, API, report and UI
- The legacy dashboard no longer mislabels return on operating cost as ROI: invested capital is required, unavailable ROI renders as N/A, and it is excluded from health scoring and alerts
- Historical report ROI/payback/IRR helpers no longer inject a one-unit investment when invested capital is missing
- The legacy report POST path now preserves owner-submitted assumptions instead of discarding them for template defaults, and its product selector is owner-scoped
- Report ROI now reconciles net horizon cash return to investment; NPV uses an explicit annual nominal discount rate; IRR solves the monthly NPV root and reports annual effective rate; payback is explicit in months
- Report HTML/PDF/API metadata consistently use Bs, month/units/percentage semantics and preserve unavailable metrics as N/A rather than zero or infinity
- Decimal financial contract covers revenue, COGS, variable/fixed costs, gross/contribution margins, break-even and ROI; cash flow and working capital remain explicit-input-only
- DSL unit compatibility rejects incompatible additive expressions and keeps count neutral in common price × quantity formulas
- One-at-a-time sensitivity endpoint reuses immutable model versions and seeded engine runs; changes are explicit additive values, not invented elasticities
- One-at-a-time sensitivity now accepts the selected Monte Carlo, System Dynamics, or Discrete Event engine and an explicit target metric; event models can measure completed work, queue end, or utilization instead of receiving a misleading profit-only result
- Legacy context projection noise now uses the simulation seed through an isolated RNG; regression coverage added
- Remaining production/report direct `np.random.normal`/`uniform` calls are eliminated; only test fixtures use global random helpers
- Demand forecasting holdout MAPE now uses the selected forecasting method, and prediction intervals use model residuals rather than raw series dispersion
- Legacy Monte Carlo and financial analysis boundaries reject invalid confidence, demand, cost, price, and non-finite inputs before calculation
- Canonical Decimal financial snapshots now expose cash flow, ending cash, and working capital only when explicit inputs exist
- Legacy risk payloads now expose the configured VaR/CVaR confidence while retaining compatibility aliases
- Legacy financial analysis no longer labels net profit as EBITDA or operating cash flow without the required underlying inputs
- Historical report financial helpers now calculate monetary values with Decimal quantization while preserving their legacy float API; golden reconciliation tests pass
- Legacy scalar and vectorized equation evaluators now use allowlisted AST traversal; arithmetic-domain errors and non-finite outputs fail explicitly without Python eval, runtime warnings, or fabricated zero-valued financials
- Diagram projections are generated deterministically from each immutable model version for BOM, process/resource, causal, stock/flow, and financial views; the endpoint is owner-scoped and tested
- Scenario changes are validated against configurable model symbols and reject unknown, boolean, NaN, and infinite values before persistence or execution
- Scenario deltas now shift realized stochastic inputs without being overwritten by sampling; stock uncertainty and stock scenario deltas apply once to initial state, after which flows preserve the state transition semantics
- Runtime golden manufacturer coverage now reports process capacity/utilization/unmet demand and explicit opt-in BOM material costs without hidden financial allocation
- Runtime golden service coverage reports service-blueprint capacity/utilization/unmet demand and stock/flow cash transitions
- Stocks are non-negative by default, signed balances require explicit opt-in, competing outflows share opening stock proportionally, and period results expose realized flows without JSON-order bias
- Demand-role flows now reconcile requested versus realized sales, stockout shortfall, service level, unmet demand and revenue; Monte Carlo/system-dynamics summaries and Results UI expose the operational impact
- Commerce starters now model purchase unit cost as an explicit driver and calculate COGS from realized sales; a golden stockout fixture reconciles revenue, COGS, operating result and service level
- Process and service ids now expose realized capacity-constrained throughput to safe BOM/revenue/cost formulas; manufacturing and professional-service golden templates no longer bill requested demand that could not be produced or served
- Persisted scenario comparison is owner-scoped, same-model-version constrained, baseline-aware, and exposes KPI deltas in API and Results UI
- Scenario comparison now includes unmet-demand and inventory-service-level deltas beside profit and uncertainty metrics, making capacity and stockout trade-offs visible in the Results table
- Data imports validate mapping targets against the immutable model and support bounded server previews without persisting a receipt
- Simulation API now dispatches explicitly to Monte Carlo, System Dynamics, or Discrete Event engines; the selected engine is persisted and returned in the run result
- Frontend `npm test` now provides a dependency-free Node smoke gate for critical routes/UI contracts; component and browser E2E coverage remains explicitly unclaimed
- Simulation runs support cooperative owner-scoped cancellation; cancelled tasks cannot overwrite their state as completed or failed
- Owner-facing company creation now uses the modeling API with sector classification, duplicate protection, and an in-app form
- User-created templates are validated before persistence and isolated from other owners; built-in templates remain shared synthetic starting points
- Distribution parameters are domain-validated before compilation, and unknown top-level DSL sections are rejected rather than silently retained
- Vite development proxy now forwards `/modeling/*`, keeping the local React flow connected to the owner-scoped modeling API
- ModelBuilder now exposes a structured accessible property editor for selected nodes (name, unit, values, formulas, capacity and provenance), preserving the DSL as the source of truth
- Immutable model DSL export includes model/version identifiers, validation, content hash and exact spec; export is owner-scoped
- Official modeling benchmark documented: stock/flow, units, properties, sensitivity and import/export were used as capability references only; Prometheus classified as observability, not simulation
- DataImports now calls the bounded server-side preview endpoint before receipt persistence and displays row-level validation errors
- DSL numeric integrity gate rejects non-finite/non-numeric operational values and out-of-domain capacity, timing, cost and probability fields while preserving valid signed cash balances
- DSL runtime-coercion gate now validates horizon, DES arrivals, empirical observations and BOM yield before compilation
- Sector starter registry now provides differentiated synthetic archetypes for commerce, production/BOM, and service businesses; all 24 built-in sectors validate through the same DSL
- DES validation now preserves discrete arrival semantics and treats declared zero capacity as unavailable rather than silently replacing it with one unit
- The canonical DSL now includes optional supplier, sales-channel, employee-role, and inventory-node structures; BOM supplier references and runtime expression symbols are validated before compilation
- The discrete-event adapter now applies configured availability, downtime, failure, rework, and scrap probabilities and reports those outcomes explicitly
- Legacy validation no longer fabricates prices, total costs, or EBITDA/ROI when their required inputs are absent; missing financial metrics remain explicit `None`
- Demand fitting now preserves observations for candidates whose support permits them, rejects incompatible/degenerate candidates explicitly, and never reports an empty fallback distribution as a successful fit
- Model readiness now reports actionable missing-input guidance across demand, cost, revenue, capacity, inventory, process, finance, uncertainty, and data dimensions; completed runs persist full traceability metadata in results and CSV reports
- Sector starter templates now declare an explicit `demand.target`; unknown demand targets are rejected before versioning or simulation
- Modeling API now returns controlled 400 responses for malformed JSON, non-integral iterations, invalid seeds, invalid scenario IDs and invalid scenario labels instead of leaking conversion errors
- Simulation failures now use a safe structured envelope (`code`, `where`, `message`, `how_to_fix`) in the API and results UI; internal exception text is logged server-side only
- A Celery failure-path regression test verifies the persisted and owner-scoped runtime response, including suppression of internal exception text
- Explicit financial summaries now flow through system-dynamics and Monte Carlo results with Decimal-string monetary values; unclassified cost lines remain visibly incomplete
- The versioned DSL now accepts an optional `financial` contract for explicit units, pricing, investment, cash, and working-capital inputs; safe expressions are checked against model symbols and golden runtime coverage verifies ROI, break-even and cash metrics
- Legacy financial ROI no longer uses operating costs as an investment proxy; absent investment returns `None`, and the Canvas fallback/adapters now return explicit incomplete results instead of fabricated monetary outputs
- Sensitivity OAT now requires explicit price, variable cost and fixed cost inputs; historical tests and Canvas fixtures declare those inputs, and no fixed 30% profit proxy remains in that path
- Unsupported OAT distributions now fail explicitly instead of silently falling back to a Normal distribution with invented parameters
- Auto forecasting now selects its holdout evaluation method from the training prefix only; legacy forecast metrics no longer truncate unequal series or report zero for unavailable comparisons
- Version immutability now protects identity, parent, schema, creator, version number, spec and hash—not only the JSON payload
- CSV/JSON/XLSX import receipts now validate mapped row values for presence and finite numeric semantics before counting them as imported
- Declared DSL constraints are now safely validated and enforced per period, preventing invalid stock/resource states from producing financial outputs
- Declared `outputs` provide safe, chained KPI formulas over runtime values such as revenue, cost, profit, and unmet demand, with dimensional validation
- Equation and KPI dependencies are now cycle-checked and evaluated in stable topological order; forward references work without JSON list-order coupling, while equations cannot read financial metrics before that runtime phase exists
- All executable DSL sections now share a collision-free namespace, and aggregate names such as revenue, profit and unmet demand are reserved so runtime values cannot be silently shadowed
- Provenance validation now covers operational, financial and derived DSL records, so `ESTIMATED`, `IMPORTED`, `PUBLIC_SOURCE` and `AI_SUGGESTED` remain explicit metadata rather than implicit truth
- Frontend shell now presents the digital-twin product identity and an accessible horizontal mobile navigation while retaining the desktop sidebar
- Frontend API errors now preserve server-provided corrective guidance such as capacity limits and validation fixes
- ModelBuilder now supports bounded undo/redo, accessible zoom controls, and causal-link connect/remove operations that write back to the canonical DSL
- Canvas nodes now support pointer drag with versioned `position`, background pan, recentering and a derived minimap; camera state remains local view state
- Causal links now render as polarity-aware visible edges between positioned nodes, while the structured list remains the accessible alternative
- Visual `position` coordinates are validated as finite DSL data and preserved by backend diagram projections, keeping saved layouts and derived views consistent
- Distribution Lab now returns bounded, support-aware candidate fits with parameters, AIC, KS diagnostics and quantiles; proposals remain review-only and owner-scoped
- Flow validation now rejects incompatible source/target/unit combinations such as kg→Bs before compilation
- BOM validation now rejects component units incompatible with their material/product definition
- BOM runtime now resolves nested subassemblies recursively and retains cycle protection; a golden multi-level manufacturing model passes
- Modeling execution now enforces a configurable per-owner active-run limit and exposes truthful queued/running phase progress before completion
- Canonical model validation now enforces configurable node/edge complexity limits before deep graph validation or compilation and reports measured/effective limits to clients
- Safe formulas now enforce configurable length, AST-node and depth limits in one parse pass; function-style `pow()` shares the exponent guard and numeric/domain failures remain controlled expression errors
- JSON API boundaries now reject array bodies and invalid version states deterministically; duplicate scenarios return a controlled conflict
- ModelBuilder now shows actionable next steps for each missing readiness dimension, while Results exposes persisted model/schema/hash/engine/seed/iteration traceability and conditional-result limits; the run-list API and regression tests cover that contract
- Legacy scalar equations now draw `random()` from the simulation-owned seeded generator; explicit empty model specs are rejected instead of being silently replaced by a starter model, and malformed XLSX uploads return controlled validation errors
- Legacy equation solving no longer fills missing dependencies with placeholder values; the basic financial fallback is now incomplete unless units sold, price, variable cost and fixed cost are explicitly supplied, and degenerate demand series are rejected rather than fitted to zero-scale distributions
- Canonical scenario deltas are now applied against the immutable baseline on every period; only stock state carries forward, preventing multi-period scenario changes from compounding unintentionally. A three-period golden regression covers the contract.
- Version allocation is serialized per model definition and preserves the parent chain/current pointer; run history, reports, cancellation and comparison now enforce company ownership rather than incidental creator ownership, with cross-owner regression coverage.
- Discrete-event process throughput now uses the minimum per-stage capacity (the sequential bottleneck) instead of averaging resource capacity across stages; a two-stage golden regression covers queue and completion semantics.
- DES scenarios now accept validated `arrivals_per_period` changes and reject unknown scenario symbols consistently with the other engines; multi-period arrival and invalid-reference regressions pass.
- Legacy prediction validation now compares only aligned finite prediction/observation pairs, reports invalid and unpaired records, and no longer converts malformed data into fabricated perfect zero forecasts; MAPE remains unavailable when every valid observation is zero.
- The legacy scalar demand path now requires positive finite historical observations, rejects invalid persisted predictions, and fails instead of inventing demand 2500 or random ±5% output after errors. Persisted results identify whether dispersion came from historical business data or a simulated rolling window, and an all-period failure cannot be reported as successful.
- Legacy runtime mapping no longer imports dairy-scale prices, demand, capacity, inventory, costs, or derived KPIs from `variable_test_data`, no longer contextually inflates capacity/inventory or rewrites price/cost values, and drops malformed inputs instead of replacing them with examples. Seeded demos retain product-scoped `SYNTHETIC_TEMPLATE` parameters, while service templates run a safe demand/revenue/direct-cost equation set without physical inventory, spoilage, cold-chain, or manufacturing equations.
- Scalar and vectorized DES no longer manufacture `DSD` as 10% of current demand. Monte Carlo scenarios carry explicit dispersion and provenance, both execution paths consume the same contract, the vectorization guard validates parity under that dispersion, and a simulated rolling standard deviation takes precedence only after two prior periods; otherwise unavailable uncertainty remains absent.
- Distribution shape is now one stable contract across decision risk, demand analysis, statistical services and legacy result contexts. Skewness and excess kurtosis are calculated from normalized central moments for valid samples; insufficient or numerically degenerate samples serialize as unavailable with an explicit status instead of producing SciPy precision warnings, `NaN`, invented zeros or tail recommendations.
- Scalar and vectorized equation execution now rejects zero denominators, invalid powers, overflow and non-finite financial outputs at the equation boundary. The vector compatibility guard falls back without emitting NumPy runtime warnings, and the scalar fallback can no longer turn the same invalid model into a completed zero-revenue/zero-profit result.
- Historical distribution identification now uses the deterministic `distribution_fit_v2` contract. Continuous candidates expose their real fitted-sample KS distance but no naive p-value; Poisson uses a discrete CDF-distance diagnostic; invalid, small, constant or non-finite samples are explicit unavailable results. Candidate selection uses AIC/BIC only within comparable likelihood families, and the legacy UI no longer manufactures random or threshold-shaped p-values.
- Legacy truth audit wave: active result charts no longer generate random demand,
  revenue, profit, margin or trend series when observations are absent. The PDF
  uses `simulation_report_summary_v2` and leaves sample-dependent risk metrics
  unavailable instead of reconstructing Monte Carlo draws. Legacy onboarding
  no longer persists questionnaire test fixtures as company observations.
- Financial risk without at least 11 finite profit samples now serializes an
  explicit unavailable contract; missing revenue/cost inputs cannot trigger
  fabricated margin or cost recommendations.
- Forecast UI now plots the exact submitted historical series and labels its
  initial values `EJEMPLO SINTÉTICO`. Full local gate: 975/975 backend tests,
  Django check, migration dry-run, diff check, frontend smoke/typecheck/build;
  lint retains one pre-existing P3 warning.

## Not yet a release claim

The branch has not been committed, pushed, merged, or deployed in this environment. Git metadata is read-only and the shared ecosystem lock is also read-only. Frontend now has a dependency-free Node smoke gate for critical route/UI contracts; cached Playwright bytes were found, but browser launch fails because the host lacks `libasound.so.2`, so component-level and browser E2E remain unverified. Production discovery, backup, migration execution, owner-login acceptance, and post-deploy verification remain release gates. The evidence-backed P0–P3 registry is `findempro/docs/TECHNICAL_DEBT.md`; P1 remains open until those integration gates are executed.
