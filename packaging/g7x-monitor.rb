class G7xMonitor < Formula
  desc "Alerts when the Canon PowerShot G7X Mark III restocks at MSRP"
  homepage "https://github.com/YOUR_USER/g7x-monitor"
  # Replace both of these after you cut a release (see packaging/HOMEBREW.md):
  url "https://github.com/YOUR_USER/g7x-monitor/archive/refs/tags/v1.0.0.tar.gz"
  sha256 "REPLACE_WITH_TARBALL_SHA256"
  license "MIT"

  depends_on "python@3.12"
  depends_on :macos

  def install
    libexec.install "config.py", "monitor.py", "decision.py", "state.py",
                    "alert.py", "requirements.txt", "checkers"
    system "python3", "-m", "venv", libexec/"venv"
    system libexec/"venv/bin/pip", "install", "--quiet", "playwright"

    # Wrapper: writable data dir + keep the Mac awake while running.
    (bin/"g7x-monitor").write <<~SH
      #!/bin/bash
      export G7X_DATA_DIR="$HOME/Library/Application Support/g7x-monitor"
      mkdir -p "$G7X_DATA_DIR"
      exec /usr/bin/caffeinate -i "#{libexec}/venv/bin/python" "#{libexec}/monitor.py"
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
      Alerts are local macOS notifications; the Mac must be awake to fire them.
    EOS
  end

  test do
    assert_predicate libexec/"monitor.py", :exist?
  end
end
