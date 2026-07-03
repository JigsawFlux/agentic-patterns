# run.py
import os
import time
import argparse
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

from shared.environment import env
from shared.telemetry import TelemetryCallback
from patterns.react import run_pattern as run_react
from patterns.plan_execute import run_pattern as run_plan_execute
from patterns.rewoo import run_pattern as run_rewoo
from patterns.reflexion import run_pattern as run_reflexion
from patterns.hierarchical import run_pattern as run_hierarchical
from patterns.dag import run_pattern as run_dag
from patterns.network import run_pattern as run_network
from patterns.consensus import run_pattern as run_consensus


def print_banner(pattern_name, incident):
    print("=" * 70)
    print(f"🚀 EXECUTION RUN: {pattern_name.upper()} PATTERN")
    print(f"Incident: {incident}")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Run and compare Emergency Dispatch Agentic Patterns")
    parser.add_argument(
        "--pattern",
        choices=["react", "plan_execute", "rewoo", "reflexion", "hierarchical", "dag", "network", "consensus", "all"],
        default="react",
        help="Which agentic pattern/topology to execute (default: react)"
    )
    parser.add_argument(
        "--incident",
        default=(
            "Report of a 3-story building fire at 14 Kingsbourne Terrace (WC1B 9ZZ, London) "
            "with smoke inhalation casualties, possible burns, and severe traffic gridlock on High Holborn."
        ),
        help="Description of the emergency incident"
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Automatically approve Silver Commander authorisation prompts (default: False)"
    )

    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY is not set.")
        print("Please create a .env file or export the variable before running.")
        return

    if args.auto_approve:
        os.environ["AUTO_APPROVE"] = "true"

    incident = args.incident
    pattern = args.pattern

    os.makedirs("outputs", exist_ok=True)

    results = []

    def execute_one(name, run_func):
        print_banner(name, incident)

        # Reset the mock environment state to keep runs comparable
        env.__init__()

        # Fresh telemetry collector per run
        telemetry = TelemetryCallback()

        # Inject callback via environment so pattern nodes can pick it up.
        # Patterns that use get_llm() will pass the callback when we refactor;
        # for now we capture wall-clock time and store telemetry separately.
        os.environ["_TELEMETRY_ACTIVE"] = "true"

        start_time = time.time()
        try:
            res = run_func(incident)
            elapsed = time.time() - start_time
            print(f"\n✅ {name.upper()} execution completed in {elapsed:.2f} seconds!")

            output_file = f"outputs/report_{name.lower().replace('/', '_')}.md"
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(res["final_report"])

            print(f"💾 Report saved to: [./{output_file}]")

            telemetry_data = telemetry.summary()
            results.append({
                "Pattern": name,
                "Status": "✅ Success",
                "Time (s)": f"{elapsed:.2f}",
                "LLM Calls": telemetry_data["LLM Calls"] or "—",
                "Input Tok": telemetry_data["Input Tokens"] or "—",
                "Output Tok": telemetry_data["Output Tokens"] or "—",
                "Est. Cost ($)": telemetry_data["Est. Cost ($)"],
                "Report (chars)": len(res["final_report"]),
                "Steps": len(res.get("history", []))
            })

            print("\n" + "-" * 30 + " FINAL REPORT " + "-" * 30)
            print(res["final_report"])
            print("-" * 74 + "\n")

            if pattern == "all":
                print("⏳ Sleeping 5 seconds between runs to respect rate limits...")
                time.sleep(5)

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n❌ {name.upper()} execution failed after {elapsed:.2f} seconds.")
            print(f"Error Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            results.append({
                "Pattern": name,
                "Status": f"❌ Failed ({type(e).__name__})",
                "Time (s)": f"{elapsed:.2f}",
                "LLM Calls": "—",
                "Input Tok": "—",
                "Output Tok": "—",
                "Est. Cost ($)": "—",
                "Report (chars)": 0,
                "Steps": 0
            })

    pattern_map = {
        "react": ("ReAct", run_react),
        "plan_execute": ("Plan-and-Execute", run_plan_execute),
        "rewoo": ("ReWOO", run_rewoo),
        "reflexion": ("Reflexion", run_reflexion),
        "hierarchical": ("Hierarchical", run_hierarchical),
        "dag": ("Acyclic/DAG", run_dag),
        "network": ("Network/P2P", run_network),
        "consensus": ("Consensus", run_consensus)
    }

    if pattern == "all":
        for key, val in pattern_map.items():
            execute_one(val[0], val[1])

        print("\n" + "=" * 90)
        print("📊 COMPARATIVE SUMMARY TABLE: AGENTIC PATTERNS")
        print("=" * 90)
        headers = ["Pattern", "Status", "Time (s)", "LLM Calls", "Input Tok", "Output Tok", "Est. Cost ($)", "Report (chars)", "Steps"]
        data = [[r[h] for h in headers] for r in results]
        print(tabulate(data, headers=headers, tablefmt="grid"))
        print("=" * 90)
    else:
        name, run_func = pattern_map[pattern]
        execute_one(name, run_func)


if __name__ == "__main__":
    main()
