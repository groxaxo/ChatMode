#!/usr/bin/env python3
"""
Integration smoke test runner for ChatMode.

This script runs a comprehensive set of smoke tests to verify:
1. Profile loading (with extra_prompt, backward compat)
2. Solo mode (AdminAgent interaction)
3. Memory (session/agent tagging, filtering, purge)
4. MCP/Tooling (list, block, call)
5. Exports (transcript markdown/CSV)
6. Tool call robustness (no finish_reason reliance)

Usage:
    python3 run_smoke_tests.py
    python3 run_smoke_tests.py --category memory
    python3 run_smoke_tests.py --verbose
"""

import sys
import argparse
import subprocess
from pathlib import Path

# Test categories
CATEGORIES = {
    "profiles": "TestProfileLoading",
    "solo": "TestSoloMode",
    "memory": "TestMemory",
    "tools": "TestMCPTools",
    "exports": "TestExports",
    "robustness": "TestToolCallRobustness",
}

def run_tests(category=None, verbose=False):
    """Run smoke tests."""
    test_file = Path(__file__).parent / "tests" / "test_smoke_tests.py"
    
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return 1
    
    cmd = ["pytest"]
    
    if category:
        if category not in CATEGORIES:
            print(f"❌ Unknown category: {category}")
            print(f"Available categories: {', '.join(CATEGORIES.keys())}")
            return 1
        cmd.append(f"{test_file}::{CATEGORIES[category]}")
        print(f"🧪 Running {category} smoke tests...\n")
    else:
        cmd.append(str(test_file))
        print("🧪 Running all smoke tests...\n")
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Run tests
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n✅ All smoke tests passed!")
    else:
        print("\n❌ Some smoke tests failed. See output above for details.")
    
    return result.returncode

def main():
    parser = argparse.ArgumentParser(
        description="Run ChatMode smoke tests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Categories:
  profiles    - Profile loading tests (extra_prompt, backward compatibility)
  solo        - Solo mode tests (AdminAgent interaction)
  memory      - Memory tests (session/agent tagging, filtering, purge)
  tools       - MCP tools tests (list, block, call)
  exports     - Export tests (transcript markdown/CSV)
  robustness  - Tool call robustness tests (no finish_reason reliance)

Examples:
  python3 run_smoke_tests.py
  python3 run_smoke_tests.py --category memory
  python3 run_smoke_tests.py --category tools --verbose
        """
    )
    
    parser.add_argument(
        "--category",
        choices=list(CATEGORIES.keys()),
        help="Run tests for a specific category only"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    sys.exit(run_tests(category=args.category, verbose=args.verbose))

if __name__ == "__main__":
    main()
