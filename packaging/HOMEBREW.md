# Homebrew distribution

The monitor is published as a Homebrew tap. Anyone on macOS can install it with:

```bash
brew tap ks6573/tap
brew install g7x-monitor
brew services start g7x-monitor      # run it in the background
```

Stop / remove:

```bash
brew services stop g7x-monitor
brew uninstall g7x-monitor
```

Requirements: macOS + **Google Chrome** in `/Applications` (`python@3.12` is
pulled in automatically). Data (state, logs, Chrome profile, and the Python
environment) lives in `~/Library/Application Support/g7x-monitor` via the
`G7X_DATA_DIR` override, so Homebrew's read-only prefix is never written to.
The first `brew services start` builds the Python environment and can take a
minute.

## How it's wired

- **App repo:** https://github.com/ks6573/g7x-monitor — tagged releases; the
  formula's `url` points at the release tarball, pinned by `sha256`.
- **Tap repo:** `ks6573/homebrew-tap` holds `Formula/g7x-monitor.rb`
  (`brew tap ks6573/tap` maps to `ks6573/homebrew-tap`).

## Cutting a new version

```bash
git tag v1.1.0 && git push origin v1.1.0
curl -sL https://github.com/ks6573/g7x-monitor/archive/refs/tags/v1.1.0.tar.gz \
  | shasum -a 256
```

Update `url` + `sha256` in `g7x-monitor.rb`, then push it to the tap repo's
`Formula/` folder.
