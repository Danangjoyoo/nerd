# Remediation Verification Knowledge

Before claiming remediation:

1. Re-run the original safe exploit-path proof after the final change.
2. Confirm the attacker-controlled source no longer reaches the vulnerable sink.
3. Run relevant regression checks and read their exit status.
4. Confirm the correction stays within the authorized scope.
5. Report unresolved validation needs separately.

Code inspection or a passing unrelated suite does not prove the original path is closed.
