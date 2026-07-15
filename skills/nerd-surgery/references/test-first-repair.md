# Test-First Repair Knowledge

1. Reproduce the reported behavior with the smallest automated test or faithful script.
2. Run it before changing production behavior.
3. Confirm it fails for the expected symptom, not a setup or syntax error.
4. Apply one minimal root-cause correction.
5. Run the same test and observe GREEN.
6. Run the relevant surrounding suite.
7. Keep the reproducer as a regression test when it protects real behavior.

If the test passes before the correction, it does not prove the failure. Tighten the reproducer before editing. If another test fails after GREEN, resolve the regression before claiming repair.
