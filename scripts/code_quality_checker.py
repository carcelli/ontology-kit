#!/usr/bin/env python3
"""
Code Quality Checker for AI-Assisted Development

This script helps verify code quality and learning comprehension
when building with AI assistance.
"""

import subprocess
import sys
from pathlib import Path


class CodeQualityChecker:
    """Automated code quality and learning verification."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.checks_passed = 0
        self.total_checks = 0

    def run_check(self, name: str, command: str, cwd: Path | None = None) -> bool:
        """Run a quality check and report results."""
        self.total_checks += 1
        print(f"\n🔍 {name}...")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0:
                print("   ✅ PASSED")
                self.checks_passed += 1
                return True
            else:
                print("   ❌ FAILED")
                if result.stdout:
                    print(f"   STDOUT: {result.stdout[:500]}...")
                if result.stderr:
                    print(f"   STDERR: {result.stderr[:500]}...")
                return False

        except subprocess.TimeoutExpired:
            print("   ⏰ TIMEOUT (5min limit)")
            return False
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            return False

    def check_environment_setup(self) -> bool:
        """Verify development environment is properly set up."""
        print("\n" + "="*60)
        print("🛠️  ENVIRONMENT SETUP CHECKS")
        print("="*60)

        checks = [
            ("Python Version", "python3 --version"),
            ("Pip Available", "python3 -m pip --version"),
            ("Git Status", "git status --porcelain"),
        ]

        all_passed = True
        for name, cmd in checks:
            if not self.run_check(name, cmd):
                all_passed = False

        return all_passed

    def check_code_quality(self) -> bool:
        """Run automated code quality checks."""
        print("\n" + "="*60)
        print("🎯 CODE QUALITY CHECKS")
        print("="*60)

        # Check if dependencies are installed
        try:
            import black
            import mypy
            import pytest
            import ruff
            deps_installed = True
        except ImportError:
            print("⚠️  Quality tools not installed. Run: pip install -e .[dev]")
            return False

        checks = [
            ("Syntax Check", "python3 -m py_compile src/agent_kit/__init__.py"),
            ("Import Check", "python3 -c 'import src.agent_kit'"),
            ("Linting (ruff)", "make lint"),
            ("Formatting (black)", "make format"),
            ("Type Checking (mypy)", "make typecheck"),
        ]

        all_passed = True
        for name, cmd in checks:
            if not self.run_check(name, cmd):
                all_passed = False

        return all_passed

    def check_tests(self) -> bool:
        """Run test suite."""
        print("\n" + "="*60)
        print("🧪 TESTING CHECKS")
        print("="*60)

        checks = [
            ("Unit Tests", "make test-unit"),
            ("Fast Tests Only", "make test-slow"),
        ]

        all_passed = True
        for name, cmd in checks:
            if not self.run_check(name, cmd):
                all_passed = False

        return all_passed

    def check_examples(self) -> bool:
        """Test that examples run successfully."""
        print("\n" + "="*60)
        print("📚 EXAMPLE VALIDATION")
        print("="*60)

        example_files = [
            "examples/01_embed_and_search.py",
            "examples/02_ontology_query.py",
        ]

        all_passed = True
        for example in example_files:
            if Path(self.repo_root / example).exists():
                if not self.run_check(f"Example: {example}", f"python3 {example}"):
                    all_passed = False

        return all_passed

    def learning_verification_questions(self) -> dict[str, str]:
        """Questions to verify understanding of the codebase."""
        return {
            "architecture": "What are the three main layers of Agent Kit?",
            "ontology": "How does SPARQL querying work in this system?",
            "agents": "What's the difference between BaseAgent and SDK adapters?",
            "vectors": "Why do we use FAISS for vector search?",
            "testing": "What makes a good unit test for an agent?",
        }

    def run_full_check(self) -> dict[str, any]:
        """Run complete quality assurance suite."""
        print("🚀 Agent Kit - Code Quality Assurance")
        print("Building with AI: Quality Verification Suite")
        print("="*60)

        results = {}

        # Environment checks
        results['environment'] = self.check_environment_setup()

        # Code quality checks
        results['quality'] = self.check_code_quality()

        # Test checks
        results['tests'] = self.check_tests()

        # Example validation
        results['examples'] = self.check_examples()

        # Summary
        print("\n" + "="*60)
        print("📊 QUALITY REPORT SUMMARY")
        print("="*60)
        print(f"Checks Passed: {self.checks_passed}/{self.total_checks}")
        print(".1f")

        if self.checks_passed == self.total_checks:
            print("🎉 ALL CHECKS PASSED - Code is production-ready!")
        elif self.checks_passed >= self.total_checks * 0.8:
            print("✅ MOSTLY GOOD - Minor issues to address")
        else:
            print("⚠️  NEEDS WORK - Address quality issues before proceeding")

        # Learning prompts
        print("\n" + "="*60)
        print("🧠 LEARNING VERIFICATION")
        print("="*60)
        print("To ensure you're learning effectively, ask yourself:")
        for category, question in self.learning_verification_questions().items():
            print(f"• {category.upper()}: {question}")

        return results


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent

    checker = CodeQualityChecker(repo_root)
    results = checker.run_full_check()

    # Exit with appropriate code
    success_rate = checker.checks_passed / checker.total_checks if checker.total_checks > 0 else 0
    sys.exit(0 if success_rate >= 0.8 else 1)


if __name__ == "__main__":
    main()
