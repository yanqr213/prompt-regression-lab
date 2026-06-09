# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-06-09

- Added optional JUnit XML output via `--junit-output`.
- Mapped each prompt regression case to a CI testcase with failure details and system output.
- Added CLI, report renderer, unit test, and GitHub Actions smoke coverage for JUnit reports.
- Updated the bilingual README with JUnit and CI usage guidance.

## [0.1.0] - 2026-06-07

- Initial public candidate release
- Added offline CLI for prompt regression test execution
- Added YAML/JSON suite loading, variable rendering, and golden comparisons
- Added `contains`, `regex`, `json-path-lite`, and `numeric_tolerance` assertions
- Added Markdown and JSON reporting
- Added unit tests, examples, and GitHub Actions CI workflow
