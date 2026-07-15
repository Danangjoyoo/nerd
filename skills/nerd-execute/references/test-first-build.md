# Test-First Build Knowledge

For every new behavior or repair:

1. Write one minimal test expressing the desired behavior.
2. Run it before production edits.
3. Confirm RED is the expected assertion failure caused by missing behavior, not an import, syntax, or setup error.
4. Write the smallest implementation that can satisfy the test.
5. Run the same test and confirm GREEN.
6. Run relevant surrounding tests.
7. Refactor only while all relevant tests remain green.

If the new test passes before implementation, it is not evidence of missing behavior. Tighten it. If production code was written first, remove that change and restart from RED. Do not add unrelated improvements under the same test cycle.
