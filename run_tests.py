"""Run all test suites."""

import sys


def main():
    passed = 0
    failed = 0
    errors = []

    # Collect all test functions from all test modules
    import tests.test_serializer as ts
    import tests.test_parser as tp
    import tests.test_e2e as te

    suites = [
        ("serializer", ts),
        ("parser", tp),
        ("e2e", te),
    ]

    for suite_name, module in suites:
        print(f"\n--- {suite_name} ---")
        for name in sorted(dir(module)):
            if not name.startswith("test_") :
                continue
            func = getattr(module, name)
            if not callable(func):
                continue
            try:
                func()
                print(f"  PASS  {name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
                failed += 1
                errors.append((suite_name, name, e))

    print(f"\n{'=' * 40}")
    print(f"{passed + failed} total, {passed} passed, {failed} failed")
    if errors:
        print("\nFailures:")
        for suite, name, e in errors:
            print(f"  {suite}/{name}: {e}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
