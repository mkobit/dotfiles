# Specification - CI caching improvement

## Overview
This track aims to optimize CI performance in GitHub Actions by implementing robust caching for Bazel builds and Python dependencies. Currently, CI runs are re-executing tasks that should be cached, specifically rebuilds and re-computation of repository rules and Bazel modules.

## Functional requirements
- **Bazel Cache Persistence:** Configure GitHub Actions to persist and restore the Bazel build cache (repository rules, external modules, and analysis cache) between runs using `actions/cache` or integrated Bazel-GHA caching tools.
- **Python Dependency Caching:** Ensure Bazel-managed Python dependencies are effectively cached to avoid re-downloads and re-compilations.
- **CI Workflow Optimization:** Update `.github/workflows/ci.yml` and `.github/actions/setup-bazel-common/` to incorporate optimal caching strategies.
- **Cache Invalidation Policy:** Define appropriate cache keys (e.g., based on `MODULE.bazel.lock`, `requirements.lock.txt`, and system environment) to ensure cache freshness and prevent poisoning.

## Non-functional requirements
- **Performance:** Target a 90% cache hit rate for unchanged build targets and repository rules.
- **Cost-efficiency:** Utilize standard GitHub Actions caching features without relying on external paid remote cache services.
- **Maintainability:** Ensure the caching configuration is easy to understand and maintain within the existing CI setup.

## Acceptance criteria
- [ ] CI runs for incremental changes show a significant reduction in execution time compared to full builds.
- [ ] Bazel logs indicate cache hits for previously built targets and external repositories.
- [ ] GitHub Actions 'Cache' tab shows successful uploads and downloads of Bazel-related data.
- [ ] CI remains stable and correctly invalidates the cache when dependencies change.

## Out of scope
- Implementing external remote execution or caching services (e.g., BuildBuddy, Google Cloud Storage).
- Optimizing local developer build performance (though CI improvements may provide insights).
