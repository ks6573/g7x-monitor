"""Configuration for the Canon G7X Mark III MSRP monitor (macOS only)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# Writable location for state, logs, and the browser profile. Defaults to the
# project dir; override with G7X_DATA_DIR for read-only installs (e.g. Homebrew).
DATA_DIR = Path(os.environ.get("G7X_DATA_DIR", BASE_DIR))

# --- Trigger --------------------------------------------------------------
# Alert when price <= this. MSRP is $879.99; the $20 buffer catches authorized
# listings that creep slightly over, while still far below scalper prices ($1,175+).
MSRP_CEILING = 899.99

# --- Cadence --------------------------------------------------------------
# A full 6-retailer sweep takes ~70s of work; the inter-cycle sleep below is
# tuned so each sweep lands ~2-3 min apart (the chosen check frequency).
CYCLE_MIN_SECONDS = 60         # min sleep between full cycles
CYCLE_MAX_SECONDS = 120        # max sleep between full cycles (randomized)
BETWEEN_RETAILER_MIN = 3       # small jittered pause between retailers
BETWEEN_RETAILER_MAX = 9
REALERT_SECONDS = 900          # re-alert every 15 min while still in stock

# --- Alerting -------------------------------------------------------------
SOUND = True                   # repeated system sound
SPEAK = True                   # spoken announcement via `say`
AUTO_OPEN = False              # auto-open the buy page in the browser on a hit

# --- Browser --------------------------------------------------------------
HEADLESS = False               # headed real Chrome passes anti-bot best
USER_DATA_DIR = DATA_DIR / "chrome-profile"
NAV_TIMEOUT_MS = 30000

# --- Paths ----------------------------------------------------------------
STATE_PATH = DATA_DIR / ".state" / "state.json"
LOG_PATH = DATA_DIR / "logs" / "monitor.log"

# --- Retailers ------------------------------------------------------------
# `url` is pinned to the STANDARD BLACK G7X Mark III so the Limited Edition
# ($1,299) can never match. Non-canon URLs are pinned + verified live during
# their build task.
RETAILERS = [
    {"name": "canon", "module": "canon", "enabled": True,
     "url": "https://www.usa.canon.com/shop/p/powershot-g7-x-mark-iii?color=Black&type=New"},
    {"name": "bestbuy", "module": "bestbuy", "enabled": True,
     "url": "https://www.bestbuy.com/product/canon-powershot-g7-x-mark-iii-20-1-megapixel-digital-camera-black/J7C86S93T6/sku/6359935"},
    {"name": "bhphoto", "module": "bhphoto", "enabled": True,
     "url": "https://www.bhphotovideo.com/c/product/1490985-REG/canon_3637c001_powershot_g7_x_mark.html"},
    {"name": "target", "module": "target", "enabled": True,
     "url": "https://www.target.com/p/canon-powershot-g7-x-mark-iii-20-1-megapixel-digital-camera-black/-/A-91467769"},
    {"name": "adorama", "module": "adorama", "enabled": True,
     "url": "https://www.adorama.com/canon-powershot-g7-x-mark-iii-digital-camera/p/icag7xm3b"},
    {"name": "amazon", "module": "amazon", "enabled": True,
     "url": "https://www.amazon.com/Canon-PowerShot-Digital-Camera-Screen/dp/B07TKNCQZL"},
]
