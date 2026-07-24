"""
Phase 1 — Run All Integration Tests
Runs P1.1 through P1.5 in sequence. Stops on first failure.
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tests.phase1.test_crdb_connection import test_connection
from tests.phase1.test_vector_ops import test_vector_operations
from tests.phase1.test_bedrock import test_bedrock
from tests.phase1.test_e2e_pipeline import test_e2e_pipeline
from tests.phase1.test_mcp import test_mcp_connection


def main():
    print("\n" + "🔬 " * 20)
    print("   MNEMOSYNE — Phase 1 Integration Tests")
    print("   Thin End-to-End Slice")
    print("🔬 " * 20 + "\n")

    tests = [
        ("P1.1 — CockroachDB Connection", test_connection),
        ("P1.2 — Vector Operations", test_vector_operations),
        ("P1.3 — Bedrock (Embeddings + Chat)", test_bedrock),
        ("P1.4 — End-to-End Pipeline", test_e2e_pipeline),
        ("P1.5 — MCP Server", None),  # async test, handled separately
    ]

    results = {}

    for name, test_fn in tests:
        if name == "P1.5 — MCP Server":
            # Async test
            print(f"\n{'─' * 60}")
            print(f"▶ Running: {name}")
            print(f"{'─' * 60}")
            try:
                passed = asyncio.run(test_mcp_connection())
            except Exception as e:
                print(f"❌ {name} crashed: {e}")
                passed = False
        else:
            print(f"\n{'─' * 60}")
            print(f"▶ Running: {name}")
            print(f"{'─' * 60}")
            try:
                passed = test_fn()
            except Exception as e:
                print(f"❌ {name} crashed: {e}")
                passed = False

        results[name] = passed

        if not passed:
            print(f"\n⛔ STOPPING — {name} failed. Fix this before proceeding.")
            break

    # Summary
    print("\n\n" + "=" * 60)
    print("   PHASE 1 — RESULTS SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}  {name}")
        if not passed:
            all_passed = False

    remaining = len(tests) - len(results)
    if remaining > 0:
        print(f"\n   ⏭️  {remaining} test(s) skipped due to earlier failure")

    print(f"\n{'=' * 60}")
    if all_passed:
        print("🎉 ALL PHASE 1 TESTS PASSED — Safe to proceed to Phase 2!")
    else:
        print("🚫 Phase 1 NOT complete — fix failures before proceeding.")
    print(f"{'=' * 60}\n")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
