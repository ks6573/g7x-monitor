# Canon PowerShot G7X Mark III — MSRP Restock Monitor (macOS)

Watches authorized retailers for the **standard black Canon PowerShot G7X Mark
III** and fires a **loud macOS alert** the moment it is genuinely buyable at or
near **MSRP** — filtering out scalpers, marketplace resellers, and the $1,299
Limited Edition.

## What counts as an alert

A retailer must satisfy **all** of:

1. **In stock** right now (a real Add-to-Cart, not "Notify me" / "Sold out").
2. **Price ≤ `$899.99`** (MSRP is $879.99; the $20 buffer catches authorized
   listings that creep slightly over — still far below scalper prices; configurable).
3. **Authorized seller** — for Amazon, the buy box must be *Sold by Amazon*
   (third-party sellers are ignored).
4. **Standard model** — every checker is pinned to the standard-black SKU, so
   the 30th Anniversary Limited Edition can never match.

## Retailers watched

Canon, Best Buy, B&H Photo, Target, Adorama, Amazon (first-party only).

Detection differs per site because their defenses/markup differ:

| Retailer | Method | Notes |
|----------|--------|-------|
| Canon | schema.org JSON-LD | Behind Akamai + Queue-It; a queue redirect is logged, never alerted |
| Best Buy | buy-box `data-testid` | Its JSON-LD wrongly says "InStock" while Sold Out, so the button is authoritative |
| B&H | schema.org JSON-LD | Reliable price + availability |
| Target | DOM ("Out of stock" + disabled cart) | No JSON-LD offer |
| Adorama | JSON-LD (URL-matched offer) | Anti-bot needs a homepage warm-up; best-effort |
| Amazon | DOM buy box + seller | Best-effort; CAPTCHA → logged, never alerted |

## How it works

One long-running Python process (`monitor.py`) drives a single **real Google
Chrome** (Playwright, persistent profile) so it passes the retailers' bot
detection. Every ~2–3 minutes (randomized) it checks each retailer in random
order, applies the trigger, and alerts on the **out→in-stock transition**,
re-alerting every 15 min while a qualifying listing stays up. A `launchd` agent
keeps the process running and restarts it on crash; the loop itself relaunches
Chrome if the browser dies or a full sweep comes back all-errors; `caffeinate`
keeps the Mac awake.

```
launchd ─▶ caffeinate ─▶ monitor.py ─▶ checkers/*.py ─▶ decision.py ─▶ alert.py
                            (loop)      (real Chrome)     (trigger)    (notification)
```

## Install

```bash
cd g7x-monitor        # wherever you cloned or downloaded it
./install.sh
```

This creates the venv, installs dependencies, and loads the LaunchAgent (starts
immediately and on every login). Requires **Google Chrome** in `/Applications`.

## Share it — install on another Mac (no git, no download)

Build a single, self-contained, double-clickable installer that carries the code
inside it:

```bash
./make_installer.sh          # produces dist/Install-G7X-Monitor.command
```

Send that one `.command` file to anyone (AirDrop, email, USB). They double-click
it — it checks for Python + Chrome, unpacks itself into
`~/Library/Application Support/g7x-monitor`, builds its environment, and starts
the background monitor. A matching `Uninstall-G7X-Monitor.command` is created
alongside it. No git, no repo, no hosting.

> **Gatekeeper note:** a script received from the internet is quarantined. The
> recipient right-clicks it → **Open** (once), or runs
> `xattr -d com.apple.quarantine "Install-G7X-Monitor.command"`.

Prefer `brew install`? See [`packaging/HOMEBREW.md`](packaging/HOMEBREW.md) — the
formula is ready, but Homebrew requires hosting a release (one-time GitHub setup).

## Uninstall

```bash
./uninstall.sh               # this dev copy
```

(An installed copy has its own `Uninstall-G7X-Monitor.command`.)

## Everyday use

```bash
tail -f logs/monitor.log            # watch it work (one line per retailer per cycle)
launchctl list | grep g7xmonitor    # confirm it's running
cat .state/state.json               # last-seen status per retailer
```

An alert is a banner + repeated system sound + a spoken announcement. When you
hear "Canon G7X in stock at <retailer> for 879 dollars", go buy it.

## Tuning (`config.py`)

- `MSRP_CEILING` — alert threshold. `879.99` is the current MSRP. Bump to
  `899.99` if you want to catch authorized listings that creep slightly over.
- `CYCLE_MIN_SECONDS` / `CYCLE_MAX_SECONDS` — sleep *between* sweeps (default
  60–120s). A sweep itself takes ~70s, so a full check lands every ~2–3 min.
- `REALERT_SECONDS` — re-alert interval while in stock (default 900 = 15 min).
- `SOUND` / `SPEAK` / `AUTO_OPEN` — alert channels. `AUTO_OPEN=True` pops the
  buy page open automatically on a hit.
- `RETAILERS` — enable/disable a retailer or repin a URL.

After editing config, restart: `./uninstall.sh && ./install.sh`.

## When a site redesigns (a checker breaks)

Each retailer is one small file in `checkers/`. If a site changes its layout,
the checker starts logging an `err=...` (never a false alert — errors are
inert). Fix the selector in that one file and restart. The pure `interpret()`
logic in each has unit tests: `.venv/bin/pytest`.

## Tests

```bash
.venv/bin/pytest -q      # 58 unit tests: price parsing, the trigger, state,
                         # alert formatting, every checker's interpret logic,
                         # and the loop wiring / health-check contract
```

## Known limitations

- **Mac must be awake.** `caffeinate` prevents *idle* sleep, but closing the lid
  still sleeps the machine. Alerts are **local only** — if you're away from the
  Mac you'll miss them. (A phone-push channel is a clean future add.)
- **Canon / Amazon are best-effort** under heavy anti-bot; the other retailers
  cover you if one is temporarily blocked.
- A hidden Chrome window runs off-screen while the monitor is active.

## Future upgrades (not built)

- Phone push (Pushover / ntfy / SMS) so alerts reach you anywhere.
- 24/7 cloud deployment (needs a paid anti-bot scraping API for Canon).
- Fast JSON fast-paths for retailers that prove easy (e.g. Target RedSky).
