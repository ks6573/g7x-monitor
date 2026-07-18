"""Main monitor loop for the Canon G7X Mark III MSRP alert (macOS).

Drives one persistent real-Chrome across all retailer checkers on a jittered
loop, alerting (loud macOS notification) on the out->in-stock transition and
re-alerting periodically while a qualifying listing stays up. `run_cycle` is a
pure-ish seam (checkers/alerts/clock injected) so the loop wiring is unit
tested without a live browser.
"""
import importlib
import random
import time
from datetime import datetime

import config
from decision import qualifies
from state import load_state, save_state, should_alert, record
from alert import build_alert, notify
from checkers.base import error_result


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


def main():
    from playwright.sync_api import sync_playwright

    checkers = _build_checkers()
    state = load_state(config.STATE_PATH)
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S} monitor starting — "
          f"{[c['name'] for c in checkers]} ceiling=${config.MSRP_CEILING}", flush=True)

    with sync_playwright() as p:
        while True:  # outer loop: (re)launch the browser after a crash
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
                while True:
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
                    time.sleep(random.uniform(config.CYCLE_MIN_SECONDS,
                                              config.CYCLE_MAX_SECONDS))
            except Exception as e:
                print(f"{datetime.now():%Y-%m-%d %H:%M:%S} cycle loop crashed: "
                      f"{e}; relaunching browser", flush=True)
            finally:
                try:
                    context.close()
                except Exception:
                    pass
            time.sleep(10)  # brief backoff before relaunching


if __name__ == "__main__":
    main()
