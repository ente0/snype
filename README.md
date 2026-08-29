<p align="center">
  <img src="https://github.com/user-attachments/assets/87eb4eb2-57ce-4a63-9f29-8e6907fdb4ca"/>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/ente0/snype">
  <img src="https://img.shields.io/badge/language-python-green" alt="Language: Python">
  <img src="https://img.shields.io/badge/ui-Textual-blueviolet" alt="Interface: Textual">
  <img src="https://img.shields.io/badge/dependencies-aircrack--ng%20%7C%20hcxtools%20%7C%20textual%20%7C%20rich-green" alt="Dependencies">
  <img src="https://img.shields.io/badge/status-development-orange" alt="Status: development">
</p>

<div align="center">

# snype — WPA Handshake Capture Utility

**A modern terminal UI for the aircrack-ng / hcxtools workflow. snype streamlines wireless reconnaissance, handshake capture, deauthentication and wordlist cracking through a keyboard-driven TUI and sensible defaults.**

</div>

> [!CAUTION]
> This tool is provided for educational and legitimate security testing purposes only. The author assumes no responsibility for any damages or legal consequences arising from its use. Always obtain explicit authorization before performing any network assessment. Unauthorized use is strictly prohibited and may violate local, national and international laws.

---

## Overview

snype wraps the standard wireless auditing toolchain behind a single interface:

- **Modern TUI** built with `textual` and `rich` — status bar, sidebar navigation, keybindings, modal dialogs.
- **Inline monitor and deauthentication** — `airodump-ng` statistics and `aireplay-ng` output are displayed together in the TUI.
- **Monitor-mode setup** — Scan enables monitor mode through `airmon-ng` and restores managed mode when the TUI exits.
- **Structured output** — every capture is written to a per-session directory with a `meta.json` for reproducibility.
- **CLI preselection** — interfaces, target and data directory can be supplied before opening the TUI.

---

## Features

- Interactive TUI with contextual keybindings and live status bar.
- Network scanning and target selection via `airodump-ng` with CSV parsing.
- Targeted packet capture with timestamped per-session output.
- Deauthentication module with an adjustable duration against all clients on the selected AP.
- Automatic conversion from `.cap` to `.hc22000` via `hcxpcapngtool`.
- Wordlist cracking with `hashcat` or `aircrack-ng` and result persistence.
- One-shot migration from the legacy flat layout to the new `snype-data/` tree.
- Argparse-based CLI for interface, target and workspace preselection.

---

## Requirements

### System

- Linux-based operating system (desktop, SSH, or NetHunter / Termux).
- Wireless adapter supporting monitor mode and packet injection.
- Python 3.10 or higher.
- `sudo` access for monitor mode, capture and packet injection; the TUI itself should run as the regular user.

### External tools

- `aircrack-ng` suite: `airmon-ng`, `airodump-ng`, `aireplay-ng`, `aircrack-ng`.
- `hcxtools`: `hcxpcapngtool`.
- `iw` for interface discovery and mode detection (`iwconfig` is used as a fallback).
- `hashcat` is optional and only required when selecting it in the Crack view; `aircrack-ng` remains available as the alternative.

### Python packages

| Package | Version | Purpose |
|---|---|---|
| [`textual`](https://github.com/Textualize/textual) | `>= 0.50` | TUI framework (layout, widgets, keybindings) |
| [`rich`](https://github.com/Textualize/rich) | `>= 13.0` | Rich text and table rendering inside widgets |

---

## Installation

snype is installed in a project-local virtual environment. Its Python
dependencies and executable stay isolated from the system Python.

```bash
git clone https://github.com/ente0/snype.git
cd snype
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

After pulling new changes, refresh the active environment:

```bash
git pull
python -m pip install -e .
```

### Optional: expose `snype` globally

To run `snype` from any directory without activating `.venv`, add this
project's virtual-environment binaries to your `PATH`. Run this once from the
repository root:

```bash
printf '\nexport PATH="%s/.venv/bin:$PATH"\n' "$PWD" >> ~/.zshrc
source ~/.zshrc
```

For Bash, replace `~/.zshrc` with `~/.bashrc` in both commands. This stores
the repository's absolute `.venv/bin` path; repeat the setup if you move the
repository.

Leave the environment when finished:

```bash
deactivate
```

### System dependencies

<details>
<summary>Debian / Ubuntu / Kali</summary>

```bash
sudo apt update
sudo apt install -y aircrack-ng hcxtools \
                    python3 python3-pip python3-venv
```
</details>

<details>
<summary>Fedora</summary>

```bash
sudo dnf install -y aircrack-ng hcxtools \
                    python3 python3-pip
```
</details>

<details>
<summary>Arch Linux / Manjaro</summary>

```bash
sudo pacman -S aircrack-ng hcxtools python python-pip
```
</details>

<details>
<summary>Kali NetHunter / Termux</summary>

```bash
pkg install aircrack-ng hcxtools python
```
</details>

---

## Quick Start

```bash
.venv/bin/snype
```

The first run performs a one-shot migration: any legacy `handshakes/` directory,
`selected_network.txt`, `interface_config.txt` and `found_passwords.txt` data is
moved or imported into the new `snype-data/` layout. Legacy files are removed
only after their contents have been relocated or imported.

Launch with pre-filled state:

```bash
.venv/bin/snype -i wlan0 -I wlan1 -b AA:BB:CC:DD:EE:FF -c 6
```

If running directly from the repository without installation:

```bash
python3 snype.py
```

---

## CLI Reference

Run `snype --help` for the complete accepted list. The current behavior of the
most relevant flags is:

| Flag | Argument | Purpose |
|---|---|---|
| `-i`, `--interface` | `IFACE` | Primary interface, used for monitoring. |
| `-I`, `--inject` | `IFACE` | Secondary interface for injection (defaults to primary). |
| `-b`, `--bssid` | `MAC` | Preselect a target BSSID. |
| `-c`, `--channel` | `N` | Preselect a channel. |
| `-e`, `--essid` | `NAME` | Preselect an ESSID (used for session naming). |
| `-d`, `--data-dir` | `PATH` | Override the data directory (default: `./snype-data`). |
| `-t`, `--term-mode` | `auto\|xterm\|tmux\|pty` | Retained for compatibility; it does not affect the current inline Monitor view. |
| `--duration` | `SECONDS` | Accepted for CLI compatibility; the current Deauth view starts at 10 seconds and is adjusted with `+` / `-`. |
| `--dry-run` | | Skip the live `airodump-ng` scan and standalone `aireplay-ng` process. Monitor-mode setup still occurs; Monitor and Crack ignore this option. |
| `-v`, `--verbose` | | Enable Python debug logging and mirror it to stderr. |
| `--version` | | Print version and exit. |
| `-h`, `--help` | | Print the full help and exit. |

---

## TUI Guide

The TUI is divided into four regions:

```
+------------------------------------------------------------+
| status bar : iface, target, channel, cap/hc22000/pwd count |
+-----------+------------------------------------------------+
|  sidebar  |                                                |
|  Scan     |                  main pane                     |
|  Monitor  |       (tables, forms, progress, logs)          |
|  Deauth   |                                                |
|  Crack    |                                                |
|  Files    |                                                |
|  Settings |                                                |
+-----------+------------------------------------------------+
| footer : keybinding hints and last log line                |
+------------------------------------------------------------+
```

### Global keybindings

| Key | Action |
|---|---|
| `s` | Scan networks |
| `m` | Start targeted monitoring + deauth |
| `d` | Standalone deauthentication |
| `c` | Enter wordlist cracking view |
| `f` | Browse captured files |
| `t` | Settings (interfaces, terminal backend) |
| `h` | Return to welcome screen |
| `?` | Show help |
| `q` | Quit |

### View-specific keybindings

**Scan**

| Key | Action |
|---|---|
| `r` | Start a scan |
| `↑` / `↓` | Move selection |
| `Enter` | Pick target |
| `+` / `-` | Adjust scan duration |

**Deauth**

| Key | Action |
|---|---|
| `Enter` | Run deauth |
| `+` / `-` | Adjust duration |
| `c` | Clear the client MAC field (the current view targets all clients) |

**Crack**

| Key | Action |
|---|---|
| `p` | Open the capture picker |
| `w` | Open the wordlist picker |
| `t` | Toggle between `hashcat` and `aircrack-ng` |
| `r` | Refresh captures and wordlists |
| `↑` / `↓` | Move within a picker |
| `Enter` | Confirm the selection or start cracking |
| `Esc` | Return from a picker or stop cracking |

**Settings**

| Key | Action |
|---|---|
| `1` | Set monitor interface |
| `2` | Set injection interface |
| `3` | Cycle terminal backend |
| `f` | Flush monitor-mode services |

### Typical workflow

1. **Settings** (`t`) — set monitor and optional injection interfaces.
2. **Scan** (`s`) — discover and pick a target from the live table.
3. **Monitor + Deauth** (`m`) — press `Enter` to run capture and deauthentication together in the TUI. Use `1` to stop capture, `2` to stop deauthentication, or `Esc` to stop both.
4. **Convert** — `.cap` files are auto-converted to `.hc22000` at the end of the session.
5. **Crack** (`c`) — choose a capture with `p`, choose a wordlist with `w`, select the cracking tool with `t`, then press `Enter`. The wordlist picker searches `/usr/share/wordlists`, `~/wordlists`, `/usr/share/seclists/Passwords` and the current directory for `.txt`, `.lst` and `.dict` files.
6. **Files** (`f`) — review capture/hash counts and recovered passwords. Artefacts remain accessible under `snype-data/hs/`.

---

## Data Layout

All artefacts live under a single, portable tree. The default root is `./snype-data/`, overridable with `--data-dir` or the `SNYPE_DATA_DIR` environment variable.

```
snype-data/
├── config.json                      # interface + last target state
├── hs/                              # captures organised by ESSID
│   └── <readable-ESSID>-<hash>/
│       ├── <YYYYMMDD-HHMMSS>/
│       │   ├── capture.cap
│       │   ├── capture.hc22000       # present only after successful conversion
│       │   └── meta.json            # target, timing and handshake result
│       └── passwords/
│           └── network-<sha256>_password.txt
├── logs/
│   └── snype.log
└── found_passwords.jsonl            # append-only cracked keys
```

The exact ESSID remains unchanged in metadata and the UI, but it is never used
as a path. Credential filenames are deterministic SHA-256 identifiers, so
slashes, absolute paths, Unicode variants and colliding display slugs cannot
redirect or overwrite a password file. Managed directories use mode `0700`
and credential/config/log files use mode `0600` on POSIX systems. Existing
custom data roots are validated but are not chmodded wholesale.

### `meta.json`

Each session directory contains a self-describing metadata file. Example:

```json
{
  "essid": "MyNetwork",
  "bssid": "AA:BB:CC:DD:EE:FF",
  "channel": 6,
  "directory": "/path/to/snype-data/hs/MyNetwork/20260414-143201",
  "started_at": "2026-04-14T14:32:01+00:00",
  "stopped_at": "2026-04-14T14:34:18+00:00",
  "duration_s": 137,
  "eapol_frames": null,
  "handshake_complete": true,
  "capture": "capture.cap",
  "hashcat": "capture.hc22000",
  "extras": {}
}
```

`eapol_frames` is currently reserved for future packet-level accounting and is
therefore written as `null`.

---

## Monitor Session Controls

The current Monitor view runs capture and deauthentication concurrently inside the TUI:

- `Enter` starts both processes for the selected target.
- `1` stops only `airodump-ng`.
- `2` stops only `aireplay-ng`.
- `Esc` stops both processes and finalises the session.

At finalisation, snype saves the capture and invokes `hcxpcapngtool`. A missing converter or a conversion error is reported separately from a valid capture that contains no handshake.

---

## Recommended Companion: hashCrack

For GPU-accelerated cracking we recommend [hashCrack](https://github.com/ente0/hashCrack), a companion tool designed to pair with snype.

Workflow:

1. Capture the handshake with snype and let it produce the `.hc22000` artefact.
2. Feed the artefact to hashCrack:

```bash
hashcrack captured_handshake.hc22000
```

Benefits:

- GPU-accelerated attack modes via `hashcat`.
- Multiple prebuilt cracking strategies and masks.
- Extensive wordlist management.

<p align="center">
  <a href="https://github.com/ente0/hashCrack">
    <img src="https://img.shields.io/badge/Check%20out-hashCrack-blue?style=for-the-badge&logo=github" alt="hashCrack Repository">
  </a>
</p>

> [!NOTE]
> Always ensure you have proper authorization before attempting any password recovery.

---

## Troubleshooting

<details>
<summary>Interface not found</summary>

- Confirm the adapter is physically connected.
- Check monitor-mode capability with `iw list`.
- Use the exact interface name as reported by `ip link`.
</details>

<details>
<summary>Permission denied</summary>

- Keep snype running as your regular user and confirm that `sudo -v` succeeds; external wireless commands request elevation individually.
- On NetHunter, ensure the chroot has access to the USB wireless device.
</details>

<details>
<summary>No networks found</summary>

- Verify the adapter is actually in monitor mode (`iwconfig <iface>`).
- Some adapters are region-locked; check `iw reg`.
</details>

<details>
<summary><code>hcxpcapngtool</code> not found</summary>

- Install the `hcxtools` system package for your distribution.
- Confirm the converter is available with `command -v hcxpcapngtool`.
- Monitor will not start without the converter because the capture result could not otherwise be classified reliably.
</details>

<details>
<summary>Deauthentication ineffective</summary>

- Ensure you are in range of the target.
- Some clients implement 802.11w / PMF and will ignore deauth frames.
- Increase the duration with `+` in the standalone Deauth view or repeat the attack.
</details>

<details>
<summary>TUI rendering issues</summary>

- Make sure the terminal reports at least 100x30 characters.
- Disable truecolor by exporting `COLORTERM=` if colors look off.
- If textual throws an error on startup, ensure Python 3.10+ is in use: `python3 --version`.
</details>

<details>
<summary>snype command not found</summary>

- Activate the project environment: `source .venv/bin/activate`.
- Or run it directly from the repository root: `.venv/bin/snype`.
</details>

---

## Educational Resources

- [4-Way Handshake Explanation](https://notes.networklessons.com/security-wpa-4-way-handshake)
- [Radiotap Introduction](https://www.radiotap.org/)
- [Aircrack-ng Documentation](https://wiki.aircrack-ng.org/)

---

## License

This project is licensed under the GPL-3.0. See the LICENSE file for details.

---

## Support

- [Report issues](https://github.com/ente0/snype/issues)

---

## Related Projects

- [hashCrack](https://github.com/ente0/hashCrack)
- [hashcat-defaults](https://github.com/ente0/hashcat-defaults)
- [wpa2-wordlists](https://github.com/kennyn510/wpa2-wordlists)
- [paroleitaliane](https://github.com/napolux/paroleitaliane)
- [SecLists](https://github.com/danielmiessler/SecLists)
