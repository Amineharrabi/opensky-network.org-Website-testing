# Responsive Tests — Quick Run & Runner Tips

Purpose: guidance for running the `tests/test_suite_4_responsive.py` responsive checks locally or on CI and recommended options for browser/device coverage and visual diffs.

Basic local run (Windows PowerShell)

1. Activate your venv and run a single case (example: `RWD-01`):

```powershell
.\venv\Scripts\Activate.ps1
.\venv\Scripts\python.exe -m pytest tests/test_suite_4_responsive.py -k RWD-01 -v --browser chrome
```

2. Run the whole responsive suite (may take several minutes):

```powershell
.\venv\Scripts\python.exe -m pytest tests/test_suite_4_responsive.py -v --browser chrome
```

Notes about browser selection and drivers

- `--browser` is read by `tests/conftest.py` and must match the fixtures you have available (e.g. `chrome`, `firefox`, `edge`).
- For accurate mobile emulation (DPR, safe-area insets, touch behavior) prefer using:
  - Chrome device emulation via ChromeDriver with proper device metrics configured on the runner, or
  - Playwright device profiles, or
  - Real-device/cloud providers (BrowserStack, Sauce Labs, LambdaTest).
- Safari / iOS tests require macOS or a cloud provider with Safari/iOS devices. Local Windows runners cannot run Safari.

Screenshots and visual regression

- Screenshots are saved to `reports/screenshots/responsive/` by the tests. These are intended as input to a visual diff tool.
- Recommended visual-diff options:
  - Percy (hosted) — integrates with CI and provides baselines and PR diffs.
  - BackstopJS or local ImageMagick/SSIM scripts — good for self-hosted baseline diffs.
  - `compare` / `magick` or `ssim` can be used to produce pass/fail thresholds.
- Suggested workflow:
  1. Run the suite on a known-good commit and store `reports/screenshots/responsive/baseline/`.
  2. On PRs, run tests in the same environment and compare `reports/screenshots/responsive/` to the baseline.

CI / Cloud runner tips

- Use matrix jobs in your CI to test different browser families and OS combinations. Example GitHub Actions strategy keys:
  - `browser: [chrome, firefox, edge]`
  - `os: [ubuntu-latest, windows-latest, macos-latest]`
- For exact browser versions (e.g., Chrome 129–131, Firefox 132–134), use VM/container images that provide pinned browser binaries or use cloud browser providers that let you select versions.
- For iOS/Safari coverage use BrowserStack or Sauce Labs device farms. They expose remote WebDriver endpoints that `conftest.py` can be adapted to use via env vars.

Accessibility & DPR considerations

- For zoom tests (RWD-11) and dark-mode (RWD-12), the repo uses best-effort emulation. For high fidelity:
  - Run on the target OS/browser; simulate zoom via OS-level settings or use an emulator that supports DPR.
  - For dark-mode rely on `prefers-color-scheme` on the runner or use a visual-diff baseline created in dark mode.

When results are flaky

- Flakiness often comes from differences in local CPU/network or running headless. To reduce noise:
  - Run in a stable CI runner with consistent CPU and Chrome/Firefox versions.
  - Run visual diffs with tolerance (SSIM thresholds) rather than strict pixel-perfect checks.

Next recommended steps

- Create and commit a visual baseline (`reports/screenshots/responsive/baseline/`) from a known-good commit.
- Add a small visual-diff script (I can add a simple ImageMagick/SSIM converter if you'd like).
- Add a CI job matrix that runs a subset of the responsive suite on PRs and the full suite on nightly builds.

If you want, I can: create the baseline folder and run a smoke capture for `RWD-01` now, or add a small `tools/visual_diff.py` helper that fails when SSIM drops below a threshold.
