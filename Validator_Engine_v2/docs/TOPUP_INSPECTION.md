# Top-Up Inspection Report

## A. Git Diff & Status Verification
Command:
```bash
git diff --stat -- ai_engine Validator_Engine
git status -s
```
Pasted Output:
```text
 M next_app/components/HldWorkspace.tsx
 M next_app/lib/store.ts
?? Validator_Engine_v2/
?? next_app/components/ValidationReportView.tsx
?? next_app/lib/validator-v2-client.ts
```
**Conclusion**: Exactly 0 files modified or deleted under `ai_engine/` and `Validator_Engine/`. Hard constraints 1 and 2 are strictly satisfied.

---

## B. Scaffolds in Real AI Engine Runs
### 1. What the AI Engine Real-World Run Returns
Inspection of the endpoint `GET /api/v1/generations/{generation_id}/package` and on-disk run packages under `ai_engine/output/run_*` reveals the following:
- Real on-disk file: `ai_engine/output/run_20261011_205247_gen_397b3b26d28b/10_architecture_package.json`
- Top-level keys:
  ```json
  ["generation_id", "prompt", "status", "arsrs", "hld", "llds", "created_at", "completed_at"]
  ```
- **Does a real package contain openapi/Dockerfile/Terraform/Alembic content?**
  **NO.** Real packages contain ARSRS, HLD, and the 5 LLDs.
- **Where are scaffolds produced in `ai_engine`?**
  In `ai_engine/app/sae/pipeline.py` (lines 711–740), deterministic generators (`generate_openapi_spec`, `generate_docker_scaffolds`, `generate_alembic_migration`, `generate_terraform_scaffold`) write text files to `self.output_dir / "scaffolds"` during standalone SAE pipeline runs. However, the FastAPI service endpoint `POST /api/v1/generations/{id}/generate` delegates to `generation_service.py` which only runs HLD and LLD generators; Phase 4 scaffold generation is not invoked during web execution, and scaffolds are never embedded into the HTTP response.
- **How can Validator_Engine_v2 obtain them from a REAL run?**
  If `ai_engine` ran with Phase 4 enabled, scaffolds would be present under `ai_engine/output/<run_id>/scaffolds/`. When running via HTTP only, scaffolds are absent from the payload.
- **What does the current code do when scaffolds are absent?**
  Currently, if `scaffolds` is missing, `l1_evidence` checks return `passed=True` because there is nothing to validate.
  **Required Extension (4.H)**: Per requirement 4.H, if scaffolds are absent from the package, each L1 check MUST return status `"not_evaluated"` (never `"passed"`). It must not deduct points, and the UI/report must explicitly display `"not evaluated: no scaffold provided"`. Synthesizing fake scaffolds is strictly prohibited.

---

## C. Fixture Provenance: `tests/fixtures/sample_package.json`
- **Source Run**: Based on `ai_engine/output/run_20261004_200235_gen_415ece685f85/10_architecture_package.json`.
- **Evidence of Deterministic Fallback Generation**:
  - Contains 10 occurrences of the string `"fallback"` in `10_architecture_package.json`.
  - Endpoint path: `/design-a-bookstore-management`.
  - Service names: `BookstoreManagementService`.
  - Domain: `Bookstore Management`.
- **Synthetic Modifications in `sample_package.json`**:
  1. `scaffolds`: Hand-crafted dictionary containing `openapi.yaml`, `Dockerfile`, `terraform/main.tf`, and `alembic/versions/0001_initial_schema.py`.
  2. Endpoint alignment: Endpoints `/auth/login` and `/design-a-bookstore-management` added to `openapi.yaml`.
  3. Database tables: `users`, `designs`, `bookstores` added to Alembic AST script to align with Database LLD.
  4. Concurrency annotations: `"Redis Redlock"` and `"SELECT FOR UPDATE"` added to Backend and Database LLDs.
- **Conclusion**: `sample_package.json` is a **synthetic clean fixture** created to test the positive execution path of all 5 layers. It is **not** representative of raw `ai_engine` API output.
- **Remediation**:
  - Retain `sample_package.json` as `synthetic_clean_fixture`.
  - Created [`tests/fixtures/real_package_unmodified.json`](file:///d:/Archova.ai/Validator_Engine_v2/tests/fixtures/real_package_unmodified.json) directly copied from `ai_engine/output/run_20261011_205247_gen_397b3b26d28b/10_architecture_package.json` with zero modifications to test the honest "scaffolds not evaluated" path.

---

## D. Frontend Wiring & `npm run build` Output
### 1. Current Code Locations
- `runValidatorV2Pipeline` is defined in [`next_app/lib/store.ts`](file:///d:/Archova.ai/next_app/lib/store.ts#L606) and bound to `ValidationReportView.tsx` (manual trigger).
- In the generation flow (`InterviewPopup.tsx:271`, `InterviewCard.tsx:187`, `LldsView.tsx:240`), the UI calls `runCorrectionWorkflow(2)` (the legacy port 8001 engine).
- In [`next_app/lib/store.ts`](file:///d:/Archova.ai/next_app/lib/store.ts), `runCorrectionWorkflow` sets the final package on completion, but `runValidatorV2Pipeline` was not automatically triggered in that sequence.
- **Required Wiring**:
  1. Automatically invoke `runValidatorV2Pipeline` when architecture generation completes.
  2. Feed the HLD and LLD visualization strictly from the final package of the V2 report.
  3. When `final_status` is `PROVISIONAL` or `UNRESOLVED`, ensure the persistent workspace banner is rendered and visualization is never hidden.

### 2. `npm run build` Output (Executed in `next_app/`)
```text
> major-project@0.1.0 build
> next build

▲ Next.js 16.1.6 (Turbopack)
- Environments: .env

  Creating an optimized production build ...
✓ Compiled successfully in 7.1s
  Running TypeScript ...
  Collecting page data using 7 workers ...
  Generating static pages using 7 workers (0/16) ...
  Generating static pages using 7 workers (4/16) 
  Generating static pages using 7 workers (8/16) 
  Generating static pages using 7 workers (12/16) 
✓ Generating static pages using 7 workers (16/16) in 455.7ms
  Finalizing page optimization ...

Route (app)
┌ ○ /
├ ○ /_not-found
├ ƒ /api/ai/generate
├ ƒ /api/auth/login
├ ƒ /api/auth/signup
├ ƒ /api/chat/history
├ ƒ /api/chat/message
├ ƒ /api/chat/session
├ ƒ /api/v1/generations
├ ƒ /api/v1/generations/[id]/answers
├ ƒ /api/v1/generations/[id]/generate
├ ƒ /api/v1/generations/[id]/lld/[type]
├ ƒ /api/v1/generations/[id]/logs
├ ƒ /api/v1/generations/[id]/logs/stream
├ ƒ /api/v1/generations/[id]/status
├ ƒ /api/v1/health
├ ○ /auth/callback
├ ○ /chat
├ ○ /signin
└ ○ /signup

○  (Static)   prerendered as static content
ƒ  (Dynamic)  server-rendered on demand
```
**Conclusion**: `next_app` compiles cleanly with Next.js 16 (Turbopack) with 0 errors across all routes and components.

---

## E. Corpus Discovery Summary
Detailed in [`Validator_Engine_v2/docs/CORPUS_DISCOVERY.md`](file:///d:/Archova.ai/Validator_Engine_v2/docs/CORPUS_DISCOVERY.md):
- 25 case-study systems in `category_10_real_world_systems`.
- 14 domain architectures in `domain_architectures`.
- 28 failure modes in `category_11_failure_modes`.
- Consistent markdown headings across all case studies. No external HTTP URLs cited.
- Stop condition checked: 25 usable files (> 3 threshold); no paragraph-fallback required.
