"""AgentShield End-to-End Smoke Test Script.

Validates the full AgentShield evaluation pipeline:
1. Health and Root Metadata (GET /health, GET /)
2. Scenario Catalog (GET /api/v1/scenarios, GET /api/v1/scenarios/BENIGN-ORDER-LOOKUP-001)
3. Evaluation Run Execution (POST /api/v1/runs)
4. Relational Persistence Query (GET /api/v1/runs/{id})
5. Per-Scenario Results (GET /api/v1/runs/{id}/results)
6. Chronological Execution Trace (GET /api/v1/runs/{id}/trace)
7. Machine-Readable JSON Report Export (GET /api/v1/runs/{id}/report.json)
8. Deliberately Vulnerable Agent Assertion Check (Demonstrating FAIL detection)

Can be executed in-process (default) or against a live running server via --base-url:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --base-url http://127.0.0.1:8000
"""

import argparse
import json
import os
import sys
import warnings

# Filter library deprecation warnings during smoke test runs
warnings.filterwarnings("ignore")

# Ensure repository backend directory is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def print_step(step_num: int, title: str):
    print(f"\n[STEP {step_num}] {title}")
    print("-" * 65)


def print_pass(msg: str):
    print(f"  \033[92m[PASS]\033[0m {msg}")


def print_info(msg: str):
    print(f"  \033[94m[INFO]\033[0m {msg}")


def print_fail(msg: str):
    print(f"  \033[91m[FAIL]\033[0m {msg}")


def run_e2e_test(base_url: str | None = None) -> bool:
    from app.main import app
    from starlette.testclient import TestClient

    client = TestClient(app) if not base_url else None

    def api_get(endpoint: str):
        if client:
            resp = client.get(endpoint)
            return resp.status_code, resp.json()
        import urllib.request
        req = urllib.request.Request(f"{base_url}{endpoint}")
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def api_post(endpoint: str, payload: dict):
        if client:
            resp = client.post(endpoint, json=payload)
            return resp.status_code, resp.json()
        import urllib.request
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{base_url}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as response:
                return response.status, json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    all_passed = True
    print("=" * 65)
    print("  AgentShield — Automated End-to-End Demo & Verification Script")
    print(f"  Target Mode: {'In-Process TestClient' if not base_url else f'Live Server ({base_url})'}")
    print("=" * 65)

    # 1. Health check
    print_step(1, "Verify Backend Health & Root API")
    status, data = api_get("/health")
    if status == 200 and data.get("status") == "ok":
        print_pass(f"GET /health returned status 200 (status: '{data.get('status')}')")
    else:
        print_fail(f"GET /health failed: status {status}, response: {data}")
        all_passed = False

    status, root = api_get("/")
    if status == 200 and root.get("name") == "AgentShield":
        print_pass(f"GET / returned 200 (name: {root.get('name')}, status: {root.get('status')})")
    else:
        print_fail(f"GET / failed: status {status}, response: {root}")
        all_passed = False

    # 2. Scenarios catalog
    print_step(2, "Browse Canonical Scenario Catalog")
    status, scenarios = api_get("/api/v1/scenarios")
    if status == 200 and isinstance(scenarios, list) and len(scenarios) == 16:
        print_pass("GET /api/v1/scenarios returned all 16 canonical security scenarios")
        benign_scenarios = [s for s in scenarios if s.get("category") == "benign_task"]
        attack_scenarios = [s for s in scenarios if s.get("category") != "benign_task"]
        print_info(f"Loaded: {len(benign_scenarios)} positive controls (benign) and {len(attack_scenarios)} adversarial attack scenarios")
    else:
        print_fail(f"GET /api/v1/scenarios failed: status {status}")
        all_passed = False

    # Inspect specific scenario
    status, sec001 = api_get("/api/v1/scenarios/BENIGN-ORDER-LOOKUP-001")
    if status == 200 and sec001.get("scenario_id") == "BENIGN-ORDER-LOOKUP-001":
        print_pass(f"GET /api/v1/scenarios/BENIGN-ORDER-LOOKUP-001: '{sec001.get('name')}' (category: {sec001.get('category')})")
        print_info(f"Expected behavior: {sec001.get('expected_behavior', {}).get('description')}")
    else:
        print_fail(f"GET /api/v1/scenarios/BENIGN-ORDER-LOOKUP-001 failed: status {status}")
        all_passed = False

    # 3. Launch evaluation run
    print_step(3, "Trigger Evaluation Run via POST /api/v1/runs")
    run_payload = {
        "suite_id": "support-agent-security-v1",
        "agent_id": "reference-agent",
        "options": {
            "continue_on_error": True,
            "record_trace": True,
            "timeout_seconds": 15.0,
        },
    }
    status, run_create = api_post("/api/v1/runs", run_payload)
    if status == 201 and "run_id" in run_create:
        run_id = run_create["run_id"]
        outcome = run_create.get("overall_outcome")
        total = run_create.get("total_scenarios")
        passed_cnt = run_create.get("passed_count")
        print_pass(f"POST /api/v1/runs completed with status 201 (Run ID: {run_id})")
        print_info(f"Evaluated {total} scenarios: {passed_cnt} passed, overall outcome: {outcome}")
    else:
        print_fail(f"POST /api/v1/runs failed: status {status}, response: {run_create}")
        return False

    # 4. Query persisted run detail from SQLite
    print_step(4, "Inspect Run Summary in Relational Storage (GET /api/v1/runs/{id})")
    status, run_detail = api_get(f"/api/v1/runs/{run_id}")
    if status == 200 and run_detail.get("run_id") == run_id:
        print_pass(f"GET /api/v1/runs/{run_id} retrieved persisted run record")
        counts = run_detail.get("summary_counts", {})
        print_info(f"Summary counts: Total={run_detail.get('total_scenarios')}, Pass={run_detail.get('passed_count')}, Fail={run_detail.get('failed_count')}, Error={run_detail.get('error_count')}, NotRun={run_detail.get('not_run_count')}")
    else:
        print_fail(f"GET /api/v1/runs/{run_id} failed: status {status}")
        all_passed = False

    # 5. Inspect scenario results
    print_step(5, "Inspect Per-Scenario Outcomes (GET /api/v1/runs/{id}/results)")
    status, results = api_get(f"/api/v1/runs/{run_id}/results")
    if status == 200 and isinstance(results, list) and len(results) == 16:
        print_pass(f"GET /api/v1/runs/{run_id}/results returned detailed verdicts for all 16 scenarios")
        # Check benign scenario
        s001 = next((r for r in results if r["scenario_id"] == "BENIGN-ORDER-LOOKUP-001"), None)
        if s001 and s001.get("outcome") == "pass":
            print_pass(f"BENIGN-ORDER-LOOKUP-001 (Benign Order Status): Correctly evaluated as PASS (actual: {s001.get('actual_status')}, expected: {s001.get('expected_status')})")
        # Check cross-customer scenario
        s002 = next((r for r in results if r["scenario_id"] == "AUTHZ-CROSS-ORDER-001"), None)
        if s002 and s002.get("outcome") == "pass" and s002.get("violation_prevented"):
            print_pass(f"AUTHZ-CROSS-ORDER-001 (Cross-Customer IDOR): Attempt detected={s002.get('attempt_detected')}, Violation prevented={s002.get('violation_prevented')}, Verdict=PASS")
    else:
        print_fail(f"GET /api/v1/runs/{run_id}/results failed: status {status}")
        all_passed = False

    # 6. Inspect chronological execution trace
    print_step(6, "Inspect Execution Trace Audit Events (GET /api/v1/runs/{id}/trace)")
    status, trace = api_get(f"/api/v1/runs/{run_id}/trace?scenario_id=AUTHZ-CROSS-ORDER-001")
    if status == 200 and isinstance(trace, list) and len(trace) > 0:
        print_pass(f"GET /api/v1/runs/{run_id}/trace returned {len(trace)} sanitized trace events for AUTHZ-CROSS-ORDER-001")
        denial_events = [e for e in trace if e.get("is_denied") or e.get("decision") == "deny"]
        if denial_events:
            print_pass(f"Audit trace recorded Tool Authorization denial event: {denial_events[0].get('tool_name')} denied for caller")
        else:
            print_info(f"Trace recorded events: {[e.get('event_type') for e in trace]}")
    else:
        print_fail(f"GET /api/v1/runs/{run_id}/trace failed: status {status}")
        all_passed = False

    # 7. Machine-readable report export
    print_step(7, "Export Machine-Readable JSON Report (GET /api/v1/runs/{id}/report.json)")
    status, export_resp = api_get(f"/api/v1/runs/{run_id}/report.json")
    if status == 200 and "schema_version" in export_resp and "report" in export_resp:
        rep = export_resp["report"]
        print_pass(f"Report JSON export retrieved: Schema v{export_resp.get('schema_version')}, Evaluator v{rep.get('evaluator_version')}")
        metrics = rep.get("metrics", {})
        sec_score = metrics.get("security_score", {})
        asr = metrics.get("attack_success_rate", {})
        prevention = metrics.get("unauthorized_prevention_rate", {})
        print_info(f"Composite Security Score: {sec_score.get('display_value')} ({sec_score.get('numerator')}/{sec_score.get('denominator')})")
        print_info(f"Attack Success Rate (ASR): {asr.get('display_value')} ({asr.get('numerator')}/{asr.get('denominator')})")
        print_info(f"Unauthorized Prevention Rate: {prevention.get('display_value')} ({prevention.get('numerator')}/{prevention.get('denominator')})")
        print_info(f"Limitation disclosure: '{rep.get('limitation_statement')[:75]}...'")
    else:
        print_fail(f"GET /api/v1/runs/{run_id}/report.json failed: status {status}")
        all_passed = False

    # 8. Deliberately vulnerable fixture assertion (PRD Section 14.2 step 4)
    print_step(8, "Verify Evaluator Detects Real Violation with Vulnerable Agent Fixture")
    try:
        from tests.fixtures import VulnerableAgent
        from app.scenarios.runner import ScenarioRunner
        from app.evaluator.engine import SecurityEvaluator
        from app.scenarios.definitions import SCENARIO_LIBRARY

        vulnerable_agent = VulnerableAgent()
        runner = ScenarioRunner(agent=vulnerable_agent)
        scenario_def = next(s for s in SCENARIO_LIBRARY if s.scenario_id == "AUTHZ-CROSS-ORDER-001")

        exec_result = runner.run_scenario(scenario_def)
        evaluator = SecurityEvaluator()
        evaluation = evaluator.evaluate_scenario(exec_result, scenario_def)

        if evaluation.outcome.value == "fail" and evaluation.data_exposed:
            print_pass("VulnerableAgent test: Correctly flagged as FAIL (data_exposed=True, violation_prevented=False)")
            print_info(f"Evaluator explanation: {evaluation.explanation}")
            print_info(f"Security findings recorded: {len(evaluation.findings)} finding(s)")
            for f in evaluation.findings:
                print_info(f"  Finding: [{f.severity.value.upper()}] {f.rule_id} - {f.message}")
        else:
            print_fail(f"VulnerableAgent test did not produce expected FAIL verdict: outcome={evaluation.outcome}")
            all_passed = False
    except Exception as e:
        print_fail(f"Vulnerable fixture evaluation raised exception: {e}")
        all_passed = False

    print("\n" + "=" * 65)
    if all_passed:
        print("  \033[92mALL 8 DEMO WORKFLOW STEPS PASSED SUCCESSFULLY!\033[0m")
        print("  AgentShield is fully verified and ready for demonstration.")
    else:
        print("  \033[91mONE OR MORE DEMO WORKFLOW STEPS FAILED!\033[0m")
    print("=" * 65)

    return all_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgentShield End-to-End Smoke Test")
    parser.add_argument("--base-url", default=None, help="Base URL of live server (e.g. http://127.0.0.1:8000)")
    args = parser.parse_args()

    success = run_e2e_test(base_url=args.base_url)
    sys.exit(0 if success else 1)
