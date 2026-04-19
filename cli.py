"""Argparse entry + bootstrap."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


__version__ = "2.0.0-dev"


EPILOG = """\
examples:
  sudo snype
      Launch the TUI with defaults.

  sudo snype -i wlan0 -I wlan1
      Preconfigure both wireless interfaces and open the TUI.

  sudo snype -i wlan0 -b AA:BB:CC:DD:EE:FF -c 6 -e MyNet
      Preselect a target and skip the scan view.

  sudo snype -t tmux
      Force the tmux backend for the dual-terminal launcher.

  sudo snype --dry-run -v
      Print every external command without running anything.

data layout:
  ./snype-data/                  (override with -d or $SNYPE_DATA_DIR)
    config.json                   interfaces + last target
    hs/<ESSID>/<timestamp>/       per-session capture + meta.json
    logs/snype.log                application log
    found_passwords.jsonl         recovered keys

terminal backends (selected with -t):
  auto   xterm > tmux > PTY on desktop; tmux on NetHunter/Termux
  xterm  spawn a graphical terminal emulator (xterm/kitty/gnome/konsole)
  tmux   detached session with horizontal split
  pty    embedded PTY multiplexer (fallback, no external GUI needed)
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="snype",
        description="WPA handshake capture utility — TUI wrapper around aircrack-ng and hcxtools.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    ifaces = parser.add_argument_group("interfaces")
    ifaces.add_argument("-i", "--interface", metavar="IFACE",
                        help="primary interface (used for monitoring).")
    ifaces.add_argument("-I", "--inject", metavar="IFACE",
                        help="secondary interface for injection (defaults to the primary one).")

    target = parser.add_argument_group("target preselection")
    target.add_argument("-b", "--bssid", metavar="MAC",
                        help="preselect a target BSSID.")
    target.add_argument("-c", "--channel", metavar="N",
                        help="preselect a channel.")
    target.add_argument("-e", "--essid", metavar="NAME",
                        help="preselect an ESSID (used for session naming).")

    runtime = parser.add_argument_group("runtime")
    runtime.add_argument("-d", "--data-dir", metavar="PATH",
                         help="override the data directory (default: ./snype-data). "
                              "Also read from $SNYPE_DATA_DIR.")
    runtime.add_argument("-t", "--term-mode", choices=["auto", "xterm", "tmux", "pty"],
                         default="auto",
                         help="dual-terminal backend to use (default: auto).")
    runtime.add_argument("--duration", type=int, default=10,
                         help="default duration, in seconds, for timed deauth attacks "
                              "(default: 10).")
    runtime.add_argument("--dry-run", action="store_true",
                         help="print external commands without executing them.")
    runtime.add_argument("-v", "--verbose", action="store_true",
                         help="enable verbose logging to snype-data/logs/snype.log.")
    runtime.add_argument("--version", action="version",
                         version=f"snype {__version__}")

    return parser


def configure_logging(paths, verbose: bool) -> None:
    paths.ensure()
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(paths.logs / "snype.log", encoding="utf-8"),
            logging.StreamHandler(sys.stderr) if verbose else logging.NullHandler(),
        ],
    )


def bootstrap(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    from core.paths import build_paths
    from core.config import Config, Target
    from core import migrate
    from tui.state import AppState
    from tui.application import run_tui

    paths = build_paths(args.data_dir).ensure()
    configure_logging(paths, args.verbose)

    actions = migrate.run(paths, verbose=args.verbose)
    for line in actions:
        logging.getLogger("snype.migrate").info(line)

    config = Config.load(paths.config)
    if args.interface:
        config.monitor_iface = args.interface
    if args.inject:
        config.inject_iface = args.inject
    if args.bssid:
        config.target = Target(bssid=args.bssid, channel=args.channel, essid=args.essid)
    if args.term_mode and args.term_mode != "auto":
        config.term_mode = args.term_mode
    config.save(paths.config)

    state = AppState(
        paths=paths,
        config=config,
        term_mode=args.term_mode,
        dry_run=args.dry_run,
        verbose=args.verbose,
    )
    for line in actions:
        state.log(line)

    try:
        run_tui(state)
    except KeyboardInterrupt:
        return 130
    return 0
