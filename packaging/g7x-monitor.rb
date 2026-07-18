class G7xMonitor < Formula
  desc "Alerts when the Canon PowerShot G7X Mark III restocks at MSRP"
  homepage "https://github.com/ks6573/g7x-monitor"
  url "https://github.com/ks6573/g7x-monitor/archive/refs/tags/v1.1.0.tar.gz"
  sha256 "9f7570173ab99c848fa6efa3b77339ed1adf46007ceeba64ddbc970154605047"
  license "MIT"

  depends_on "python@3.12"
  depends_on :macos

  def install
    # Copy the app. The Python venv is created on first run (Homebrew's build
    # sandbox has no network, so we can't pip-install here).
    libexec.install "config.py", "monitor.py", "decision.py", "state.py",
                    "alert.py", "requirements.txt", "checkers"

    python = Formula["python@3.12"].opt_bin/"python3.12"
    (bin/"g7x-monitor").write <<~SH
      #!/bin/bash
      set -e
      DATA="$HOME/Library/Application Support/g7x-monitor"
      VENV="$DATA/venv"
      mkdir -p "$DATA"
      if [ ! -x "$VENV/bin/python" ]; then
        echo "First run: setting up Python environment (about a minute)..." >&2
        "#{python}" -m venv "$VENV"
        "$VENV/bin/pip" install --quiet --upgrade pip
        "$VENV/bin/pip" install --quiet playwright
      fi
      export G7X_DATA_DIR="$DATA"
      exec /usr/bin/caffeinate -i "$VENV/bin/python" "#{libexec}/monitor.py" "$@"
    SH
  end

  service do
    run [opt_bin/"g7x-monitor"]
    keep_alive true
    log_path "#{Dir.home}/Library/Application Support/g7x-monitor/logs/brew.out.log"
    error_log_path "#{Dir.home}/Library/Application Support/g7x-monitor/logs/brew.err.log"
  end

  def caveats
    <<~EOS
      Requires Google Chrome in /Applications.
        Start:  brew services start g7x-monitor
        Stop:   brew services stop g7x-monitor
      The first start installs a small Python environment and may take a minute.
      Alerts are local macOS notifications; the Mac must be awake to fire them.
    EOS
  end

  test do
    assert_predicate libexec/"monitor.py", :exist?
  end
end
