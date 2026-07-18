"""Main monitor loop for the Canon G7X Mark III MSRP alert (macOS).

Drives one persistent real-Chrome across all retailer checkers on a jittered
loop, alerting (loud macOS notification) on the out->in-stock transition and
re-alerting periodically while a qualifying listing stays up. `run_cycle` is a
pure-ish seam (checkers/alerts/clock injected) so the loop wiring is unit
tested without a live browser.
"""
import argparse
import importlib
import random
import time
from datetime import datetime

import config
from decision import qualifies
from state import load_state, save_state, should_alert, record
from alert import build_alert, notify
from checkers.base import error_result


def _positive_hours(value):
    hours = float(value)
    if hours <= 0:
        raise argparse.ArgumentTypeError("hours must be greater than 0")
    return hours


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="g7x-monitor",
        description="Watch retailers for the Canon G7X Mark III and alert on "
                    "macOS when it is in stock at MSRP.")
    p.add_argument("--hours", type=_positive_hours, default=None, metavar="N",
                   help="Run for N hours, then stop (e.g. --hours 3, or --hours 1.5). "
                        "Omit to run until stopped.")
    return p.parse_args(argv)


def compute_deadline(hours, start_now):
    """Epoch second at which to stop, or None to run forever."""
    return None if hours is None else start_now + hours * 3600


def is_expired(deadline, now):
    return deadline is not None and now >= deadline


def run_cycle(context, checkers, state, *, now, alert_fn, ceiling,
              realert_seconds, log_fn=None, save_fn=None, pause_fn=None):
    """One pass over all retailers (random order). Each checker is isolated:
    an exception becomes an error Result and never stops the pass. Returns the
    list of Results so the caller can detect a dead browser (all errors)."""
    order = list(checkers)
    random.shuffle(order)
    results = []
    for spec in order:
        name, module, url = spec["name"], spec["module_obj"], spec["url"]
        try:
            result = module.check(context, url)
        except Exception as e:
            result = error_result(name, url, f"{type(e).__name__}: {e}")
        results.append(result)
        q = qualifies(result, ceiling)
        if should_alert(state, name, q, now, realert_seconds):
            title, msg, speak = build_alert(result)
            alert_fn(title, msg, speak, result)
            record(state, name, q, now, alerted=True)
        else:
            record(state, name, q, now, alerted=False)
        if log_fn:
            log_fn(result)
        if save_fn:
            save_fn(state)
        if pause_fn:
            pause_fn()
    return results


# --- live wiring (not unit-tested) ----------------------------------------

def _log(result):
    line = (f"{datetime.now():%Y-%m-%d %H:%M:%S} [{result.retailer:8}] "
            f"in_stock={result.in_stock!s:5} price={result.price} "
            f"err={result.error!r} :: {result.raw_status}")
    print(line, flush=True)
    try:
        config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(config.LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _alert(title, msg, speak, result):
    notify(title, msg, sound=config.SOUND,
           speak_text=speak if config.SPEAK else None,
           open_url=result.url if config.AUTO_OPEN else None)


def _build_checkers():
    checkers = []
    for r in config.RETAILERS:
        if not r.get("enabled", True) or not r.get("url"):
            continue
        module = importlib.import_module(f"checkers.{r['module']}")
        checkers.append({"name": r["name"], "module_obj": module, "url": r["url"]})
    return checkers


def main(argv=None):
    from playwright.sync_api import sync_playwright

    args = parse_args(argv)
    checkers = _build_checkers()
    state = load_state(config.STATE_PATH)
    deadline = compute_deadline(args.hours, time.time())
    window = f"for {args.hours:g}h" if args.hours else "until stopped"
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} monitor starting ({window}) — "
          f"{[c['name'] for c in checkers]} ceiling=${config.MSRP_CEILING}", flush=True)

    with sync_playwright() as p:
        while not is_expired(deadline, time.time()):  # outer: relaunch after a crash
            try:
                context = p.chromium.launch_persistent_context(
                    str(config.USER_DATA_DIR),
                    channel="chrome",
                    headless=config.HEADLESS,
                    viewport={"width": 1366, "height": 1000},
                    args=["--disable-blink-features=AutomationControlled",
                          "--window-position=-32000,-32000"],  # window out of sight
                )
            except Exception as e:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} browser launch failed: "
                      f"{e}; retrying in 30s", flush=True)
                time.sleep(30)
                continue

            disconnected = {"v": False}
            context.on("close", lambda: disconnected.__setitem__("v", True))
            all_error_streak = 0
            try:
                while not is_expired(deadline, time.time()):
                    results = run_cycle(
                        context, checkers, state,
                        now=time.time(), alert_fn=_alert,
                        ceiling=config.MSRP_CEILING,
                        realert_seconds=config.REALERT_SECONDS,
                        log_fn=_log,
                        save_fn=lambda s: save_state(config.STATE_PATH, s),
                        pause_fn=lambda: time.sleep(random.uniform(
                            config.BETWEEN_RETAILER_MIN, config.BETWEEN_RETAILER_MAX)),
                    )
                    all_error_streak = (all_error_streak + 1
                                        if results and all(r.error for r in results)
                                        else 0)
                    if disconnected["v"] or all_error_streak >= 2:
                        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} browser unhealthy "
                              f"(disconnected={disconnected['v']} "
                              f"all_error_streak={all_error_streak}); relaunching",
                              flush=True)
                        break
                    nap = random.uniform(config.CYCLE_MIN_SECONDS, config.CYCLE_MAX_SECONDS)
                    if deadline is not None:  # don't sleep past the stop time
                        nap = min(nap, max(0.0, deadline - time.time()))
                    time.sleep(nap)
            except Exception as e:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} cycle loop crashed: "
                      f"{e}; relaunching browser", flush=True)
            finally:
                try:
                    context.close()
                except Exception:
                    pass
            if is_expired(deadline, time.time()):
                break
            time.sleep(10)  # brief backoff before relaunching

    if deadline is not None:
        print(f"{datetime.now():%Y-%m-%d %H:%M:%S} reached {args.hours:g}h limit — "
              f"stopped.", flush=True)


if __name__ == "__main__":
    main()
