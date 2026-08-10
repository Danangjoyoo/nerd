# Definition of Done: Research

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Definition of Done router](index.md) and load it only for its named trigger.

## Research Basis

- [The Scrum Guide](https://scrumguides.org/scrum-guide.html): shared quality state, transparency, and the rule that unmet work is not done.
- [NASA Systems Engineering Handbook appendices](https://www.nasa.gov/reference/system-engineering-handbook-appendix/): requirement quality, source traceability, verification matrices, validation planning, and stakeholder evidence.
- [Cucumber BDD guidance](https://cucumber.io/docs/bdd/): discovery, formulation, executable examples, and collaborative validation of behavior.
- [Martin Fowler on TDD](https://martinfowler.com/bliki/TestDrivenDevelopment.html): test-list preparation and red-green-refactor as an inner development loop.
- [Hypothesis documentation](https://hypothesis.readthedocs.io/en/latest/): property-based and invariant testing across generated edge cases.
- [Pact documentation](https://docs.pact.io/): consumer-driven contracts and executable integration expectations.
- [Stryker mutation-testing guidance](https://stryker-mutator.io/docs/): evaluating whether tests detect meaningful defects rather than merely execute code.
- [TLA+ overview](https://lamport.azurewebsites.net/tla/tla.html): formal modeling and checking for concurrent and distributed system properties.
- [Google SRE on SLOs](https://sre.google/sre-book/service-level-objectives/): user-centered indicators, explicit thresholds and measurement conditions, and control-loop economics.
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/): referenceable application-security verification requirements.
- [NIST Secure Software Development Framework](https://csrc.nist.gov/projects/ssdf): outcome- and risk-based secure-development practices rather than an unfiltered checklist.
- [W3C WCAG overview](https://www.w3.org/WAI/standards-guidelines/wcag/): stable accessibility standards and testable conformance criteria.
- [NIST AI RMF Measure guidance](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/): documented, repeatable evaluation; representative conditions; independent assessors; and user feedback.
- [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots): controlled snapshot evidence and environment sensitivity.
- [OpenTelemetry overview](https://opentelemetry.io/docs/what-is-opentelemetry/): traces, metrics, and logs as operational evidence of system state.

Treat these sources as a technique library. Select only the requirements and evidence justified by the current task, its authorities, and its risks.
