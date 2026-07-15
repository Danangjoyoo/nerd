# Test-First Remediation Knowledge

1. Reproduce the confirmed exploit path with a safe local test or harmless fixture.
2. Run it before mutation and confirm the security assertion fails for the expected reason.
3. Apply the smallest correction at the vulnerable boundary.
4. Run the same proof and observe the exploit path close.
5. Run relevant functional and security regressions.
6. Retain the test when it prevents the confirmed issue from returning.

Do not create an unsafe payload, contact production, or broaden the original audit scope to make the reproducer work.
