# Homebrew distribution

> **TL;DR:** The double-click **`dist/Install-G7X-Monitor.command`** needs no
> hosting and is the easiest way to share this. Homebrew is only worth it if you
> want `brew install` — and brew *requires* the code to live at a public URL, so
> it needs a one-time GitHub (or other host) setup.

## Why brew needs hosting

A Homebrew formula downloads a release tarball from a `url` and verifies its
`sha256`. There's no way around hosting that tarball somewhere public. The
formula in `g7x-monitor.rb` is complete except for those two lines.

## One-time publish

1. Put this project in a public GitHub repo, e.g. `YOUR_USER/g7x-monitor`.
2. Cut a release tag:
   ```bash
   git tag v1.0.0 && git push origin v1.0.0
   ```
3. Get the tarball's checksum:
   ```bash
   curl -sL https://github.com/YOUR_USER/g7x-monitor/archive/refs/tags/v1.0.0.tar.gz \
     | shasum -a 256
   ```
4. In `g7x-monitor.rb`, replace `YOUR_USER`, the `url`, and the `sha256`.
5. Create a **tap** repo named `homebrew-tap` (also public) and drop
   `g7x-monitor.rb` into its `Formula/` folder.

## Then anyone installs with

```bash
brew tap YOUR_USER/tap
brew install g7x-monitor
brew services start g7x-monitor      # runs it in the background
```

`brew services stop g7x-monitor` stops it. Data (state, logs, Chrome profile)
lives in `~/Library/Application Support/g7x-monitor` via the `G7X_DATA_DIR`
override, so the read-only Homebrew prefix is never written to.

## Requirements for end users

- macOS + **Google Chrome** in `/Applications`
- Homebrew (`python@3.12` is pulled in automatically)
