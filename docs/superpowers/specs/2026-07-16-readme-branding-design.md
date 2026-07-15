# README Branding Design

## Goal

Add the supplied Nerd banner and the official skills.sh install-count badge to the repository README without changing existing product copy, installation instructions, benchmark content, or skill documentation.

## Approved Layout

The README header will use this order:

1. `# Nerd`
2. The supplied `assets/nerd-banner.png` image rendered with standard Markdown and descriptive alt text
3. The existing CI badge and the new skills.sh badge on one line
4. The existing introductory paragraph

The skills.sh badge markup will be exactly:

```markdown
[![skills.sh](https://skills.sh/b/danangjoyoo/nerd)](https://skills.sh/danangjoyoo/nerd)
```

The existing CI badge will remain unchanged.

## Files and Responsibilities

- `assets/nerd-banner.png` is the user-supplied 1600×872 banner asset. It will be tracked as provided, without image generation or modification.
- `README.md` owns the visible header layout, banner reference, and badges.
- `tests/test_readme.py` owns deterministic contract checks for the exact banner path, meaningful alt text, exact skills.sh badge image URL, and exact skills.sh destination URL.

## Behavior and Error Handling

GitHub will render the repository-relative banner path and both remote badges. The change has no runtime data flow or application error path. Automated tests will fail if the banner reference or skills.sh owner/repository slug drifts. The implementation will also verify that the referenced banner exists and is a valid PNG.

## Testing Strategy

Implementation will follow test-first sequencing:

1. Add a focused README contract test for the banner and skills.sh badge.
2. Run that test and confirm it fails because the README markup is absent.
3. Add the minimal README markup and track the supplied asset.
4. Run the focused test, the complete README contract suite, and the full repository test suite.
5. Verify the final diff contains no unrelated README changes.

## Non-goals

- Do not edit or regenerate the supplied image.
- Do not add HTML sizing, centering, or decorative layout.
- Do not change installation commands, benchmark results, product copy, or skill definitions.
- Do not change skills.sh publication or telemetry behavior.
