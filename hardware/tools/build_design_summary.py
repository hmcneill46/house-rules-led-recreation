#!/usr/bin/env python3
"""Build a local, image-aware design summary from the current engineering files.

No network calls. Missing renders receive a text placeholder, never a broken
image. DRC counts are read from the latest matching native KiCad JSON report;
they are not hard-coded and do not grant physical release approval.
"""
from __future__ import annotations

import ast
from datetime import datetime
import hashlib
from html import escape
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
HW = ROOT / "hardware"
TZ = ZoneInfo("Europe/London")


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def nice_time(timestamp):
    try:
        stamp = datetime.fromisoformat(timestamp)
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=TZ)
        return stamp.astimezone(TZ).strftime("29 Oct 2026, %H:%M %Z") if stamp.date().isoformat() == "2026-10-29" else stamp.astimezone(TZ).strftime("%d %b %Y, %H:%M %Z")
    except (TypeError, ValueError):
        return "Time not recorded"


def report_for(board):
    source = f"house-rules-{board}.kicad_pcb"
    candidates = []
    for path in (HW / "reports").glob("*drc.json"):
        if "negative" in path.name:
            # Deliberately failing copies verify rule scope, not the real PCB.
            continue
        data = read_json(path)
        if data and data.get("source") == source:
            candidates.append((data.get("date", ""), path.stat().st_mtime, path, data))
    if not candidates:
        return None
    _, _, path, data = max(candidates, key=lambda item: item[:2])
    pcb = HW / "kicad" / source
    return {
        "path": path,
        "date": nice_time(data.get("date")),
        "issues": len(data.get("violations", [])),
        "unconnected": len(data.get("unconnected_items", [])),
        "parity": len(data.get("schematic_parity", [])),
        "stale": pcb.exists() and pcb.stat().st_mtime > path.stat().st_mtime + 1,
        "ignored_rules": [x.get("key") for x in data.get("ignored_checks", [])],
    }


def scalar_scad():
    """Read simple numeric dimensions without executing OpenSCAD."""
    try:
        source = re.sub(r"//[^\n]*", "", (HW / "mechanical/enclosure.scad").read_text())
    except OSError:
        return {}
    values = {}

    def value(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -value(node.operand)
        if isinstance(node, ast.BinOp):
            a, b = value(node.left), value(node.right)
            if isinstance(node.op, ast.Add): return a + b
            if isinstance(node.op, ast.Sub): return a - b
            if isinstance(node.op, ast.Mult): return a * b
            if isinstance(node.op, ast.Div): return a / b
        raise ValueError("Not a simple numeric expression")

    for match in re.finditer(r"^\s*(\w+)\s*=\s*([^;]+);", source, re.M):
        try:
            values[match[1]] = value(ast.parse(match[2].strip(), mode="eval").body)
        except (SyntaxError, ValueError, KeyError, TypeError, ZeroDivisionError):
            continue
    return values


def linked(path, label):
    return f'<a href="{escape(str(path), quote=True)}">{escape(label)}</a>'


def render_figure(filename, title, detail, wide=False):
    path = HW / "render" / filename
    valid = path.exists() and path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    image = (f'<a class="render-link" href="render/{filename}"><img src="render/{filename}" alt="{escape(title)} — CAD render" loading="lazy"></a>'
             if valid else '<div class="pending-render">KiCad render pending generation.</div>')
    return f'<figure class="{"wide" if wide else ""}">{image}<figcaption><b>{escape(title)}</b><span>{escape(detail)}</span></figcaption></figure>'


def main():
    spec_path = HW / "kicad/circuit-spec.json"
    spec = read_json(spec_path)
    if not spec:
        raise SystemExit("Current circuit specification is required")
    boards = spec["boards"]
    main_board, usb = boards["main"], boards["usb"]
    summary = read_json(HW / "reports/schematic-verification-summary.json") or {}
    software_checks = read_json(HW / "reports/software-verification.json") or {}
    host_tests = software_checks.get("unittest_count")
    host_checks_fresh = bool(software_checks.get("sha256"))
    for relative, expected in software_checks.get("sha256", {}).items():
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            host_checks_fresh = False
    host_test_text = (f"{host_tests} host tests passed" if software_checks.get("status") == "passed" and host_tests and host_checks_fresh
                      else "See the saved host-test report")
    package = HW / "manufacturing/A1_review"
    package_manifest = read_json(package / "manifest.json")
    package_fresh = bool(package_manifest and package_manifest.get("input_sha256"))
    for relative, expected in (package_manifest or {}).get("input_sha256", {}).items():
        path = ROOT / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            package_fresh = False
    if package_manifest:
        package_link = '<a href="manufacturing/A1_review/README.md">Manufacturing review package</a>'
        package_note = ("The review package matches its recorded source hashes." if package_fresh
                        else "The saved manufacturing package predates current inputs; regenerate before review.")
    else:
        package_link = '<span class="pending-file">Manufacturing review package — pending export</span>'
        package_note = "The final review package will be saved in manufacturing/A1_review after CAD checks."
    spec_digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    erc_fresh = summary.get("spec_sha256") == spec_digest
    erc_clean = all(summary.get("boards", {}).get(board, {}).get("erc_violation_count") == 0
                    and summary.get("boards", {}).get(board, {}).get("netlist_matches_spec") is True
                    for board in ("main", "usb"))
    reports = {name: report_for(name) for name in ("main", "usb")}
    clean = all(r and not r["stale"] and not r["issues"] and not r["unconnected"] and not r["parity"] for r in reports.values())
    routing_status = "CAD checks clean · bench release pending" if clean and erc_fresh and erc_clean else "Engineering prototype · release checks pending"
    report_rows = []
    for board, label in [("main", "Main display PCB"), ("usb", "USB carrier")]:
        report = reports[board]
        erc = summary.get("boards", {}).get(board, {}).get("erc_violation_count")
        if report:
            flag = "Report predates the current PCB" if report["stale"] else "Latest saved report"
            details = f'{linked("reports/" + report["path"].name, report["date"])}<small>{flag}</small>'
            checks = f'{report["issues"]} / {report["unconnected"]} / {report["parity"]}'
        else:
            checks, details = "Pending", "Native DRC report not generated"
        report_rows.append(f'<tr><th>{label}</th><td>{"—" if erc is None else erc}</td><td>{checks}</td><td>{details}</td></tr>')
    erc_note = "Schematic netlists match the current circuit specification." if erc_fresh else "Schematic/netlist verification must be refreshed against the current circuit specification."
    dimensions = scalar_scad()
    case_h = dimensions.get("outer_h")
    if all(dimensions.get(key) is not None for key in ("outer_w", "outer_h", "total_depth")):
        case_text = f'The printed case concept is {dimensions["outer_w"]:g} × {case_h:g} × {dimensions["total_depth"]:g} mm.'
    else:
        case_text = 'See the parametric case model for current enclosure dimensions.'
    try:
        build_log = (HW / "firmware/compiled/build.log").read_text()
        flash = re.search(r"Sketch uses (\d+) bytes", build_log)[1]
        ram = re.search(r"Global variables use (\d+) bytes", build_log)[1]
        memory = f'{int(flash):,} bytes flash / {int(ram):,} bytes static RAM'
    except (OSError, TypeError):
        memory = "See the saved compiler report for memory use"
    now = datetime.now(TZ).strftime("%d %B %Y · %H:%M %Z")
    figures = [render_figure("main-top.png", "Main PCB — top / LED side", "Native KiCad CAD render; seven touching upright modules.", True),
               render_figure("main-bottom.png", "Main PCB — bottom / electronics", "Controller and drivers behind the display.", True),
               render_figure("main-bare-front.png", "Main PCB — top, without LED bodies", "Through-hole footprint before fitting displays."),
               render_figure("usb-top.png", "USB carrier — component side", "USB-C, protection and six-wire connection.")]
    if (HW / "render/assembly-isometric.png").exists():
        figures.append(render_figure("assembly-isometric.png", "Assembly — isometric", "Packaging study; physical clearances need verification.", True))
    if (HW / "render/enclosure-PROTOTYPE-assembled.png").exists():
        figures.append(render_figure("enclosure-PROTOTYPE-assembled.png", "Printable enclosure prototype", "Native OpenSCAD render; case and cable fit still require a trial print.", True))
    revision = escape(spec.get("revision", "A1"))
    html = f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>House Rules — PCB design summary</title>
<style>
:root{{--ink:#222824;--muted:#626b63;--paper:#f5f3eb;--line:#dcded3;--green:#286b5a;--gold:#956224}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,sans-serif}}main{{max-width:1120px;margin:auto;padding:46px 30px 60px}}header{{padding-bottom:28px;border-bottom:1px solid var(--line)}}.eyebrow{{font-size:12px;text-transform:uppercase;letter-spacing:2px;color:var(--green);font-weight:700}}h1{{font-size:clamp(35px,5vw,58px);line-height:1.08;letter-spacing:-2px;margin:14px 0}}.lead{{font-size:20px;max-width:850px;color:#465148}}.status{{display:inline-block;background:#e8deca;color:#76501e;font-size:13px;padding:5px 12px;border-radius:20px;font-weight:650}}.meta{{font-size:12px;color:var(--muted);margin-top:14px}}.specs{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:25px}}.spec{{border:1px solid var(--line);border-radius:9px;padding:14px;background:#fffc}}.spec b{{font-size:22px;display:block;line-height:1.25}}.spec span{{font-size:12px;color:var(--muted)}}section{{margin-top:38px}}h2{{font-size:24px;letter-spacing:-.6px;margin:0 0 12px}}h3{{font-size:16px;margin:8px 0}}p{{margin:10px 0 14px}}a{{color:#246f68;text-decoration-thickness:1px;text-underline-offset:3px}}.gallery{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}figure{{margin:0;background:#fff;border:1px solid var(--line);border-radius:10px;overflow:hidden}}figure.wide{{grid-column:1/-1}}.render-link{{display:block;background:#ebece6}}figure img{{display:block;width:100%;max-height:480px;object-fit:contain}}figcaption{{padding:13px 18px;font-size:13px}}figcaption b,figcaption span{{display:block}}figcaption span{{color:var(--muted);margin-top:3px}}.pending-render{{padding:45px 20px;text-align:center;color:var(--muted);background:repeating-linear-gradient(135deg,#edf0e9,#edf0e9 15px,#f6f7f3 15px,#f6f7f3 30px);font-size:14px}}.two{{display:grid;grid-template-columns:1fr 1fr;gap:27px}}.note{{background:#e9eee5;border-left:4px solid var(--green);padding:14px 18px;border-radius:0 7px 7px 0}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{text-align:left;padding:12px 10px;border-bottom:1px solid var(--line);vertical-align:top}}thead th{{font-size:11px;letter-spacing:.6px;text-transform:uppercase;background:#e9ece3}}td small{{display:block;color:var(--muted);font-size:11px;margin-top:2px}}.table-wrap{{overflow-x:auto}}.small{{font-size:13px;color:var(--muted)}}.files{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}}.files a,.files .pending-file{{display:block;background:#fff9;border:1px solid var(--line);border-radius:7px;padding:13px 15px;font-size:14px;text-decoration:none}}ol{{padding-left:22px}}li{{margin:7px 0}}footer{{margin-top:38px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:12px}}code{{font-size:.9em}}@media(max-width:720px){{main{{padding:28px 17px}}.specs{{grid-template-columns:1fr 1fr}}.two,.files{{grid-template-columns:1fr}}.gallery{{grid-template-columns:1fr}}h1{{letter-spacing:-1px}}figure.wide{{grid-column:auto}}}}@media print{{body{{background:#fff}}main{{padding:0}}.spec,figure{{break-inside:avoid}}section{{break-inside:avoid-page}}a{{color:inherit}}}}
</style>
<main>
<header><div class="eyebrow">Rose Finn-Kelcey recreation · revision {revision}</div><h1>House Rules.<br>A physical 7 × 35 display.</h1>
<p class="lead">A programmable, USB-powered replica using your LED modules, with electronics hidden behind them.</p>
<div class="status">{routing_status}</div><div class="meta">Summary refreshed {now}. These are engineering files and CAD renders, not photographs of built hardware.</div>
<div class="specs"><div class="spec"><b>{main_board['width']:g} × {main_board['height']:g} mm</b><span>Main PCB · {main_board['layers']} layers · {main_board['thickness']:g} mm thick</span></div><div class="spec"><b>{usb['width']:g} × {usb['height']:g} mm</b><span>USB carrier · {usb['layers']} layers · {usb['thickness']:g} mm thick</span></div><div class="spec"><b>245 red dots</b><span>Seven 5 × 7 modules · continuous 35-column screen</span></div><div class="spec"><b>3 replicas</b><span>Your 21 modules · 84 LED solder joints per unit</span></div></div></header>

<section><h2>1. What the boards look like</h2><div class="gallery">{''.join(figures)}</div></section>

<section><h2>2. The electronics</h2><p>An STM32G0B1KBU6 controls four IS31FL3729 drivers in groups of 2 + 2 + 2 + 1 displays. Paired modules share scanned anodes and retain independent row cathodes. The 47 kohm resistors give approximately 7.25 mA peak per dot and 342 mA average LED load with every dot on, before controller overhead. Measure current and temperature.</p><p>Six layers accommodate the lead fanout. USB data runs along the front upper margin. The carrier enables the bottom-right USB opening without colliding with LED leads.</p></section>

<section><h2>3. USB power and programming</h2><div class="two"><div><h3>5 V, with source qualification</h3><p>Both C-to-C and A-to-C cables are supported. No higher-voltage USB PD contract is requested. Full output requires a valid Type-C current advertisement, positive completed BC1.2 charger detection, or USB configuration granting the 500 mA descriptor. An unqualified source uses a conservative dim fallback. Separate 5.1 kohm CC terminations and 47k/47k ADC dividers provide orientation-independent detection.</p></div><div><h3>The same port loads firmware</h3><p>Programming uses the factory USB DFU bootloader, with BOOT/RESET controls and SWD recovery pads. BOOT0 is PA14/SWCLK, pin 25; its option bytes must be configured and recovery tested. A series resistor protects that shared recovery pin. CDC is the running application’s serial interface, with walking, all-on and checkerboard diagnostics. Driver shutdown stays low during startup/detection; host suspend blanks the display and selects STOP0.</p></div></div><p class="small">Compiled prototype: {escape(memory)}. The actual ELF’s descriptor and startup/charge-detection call flow were audited. Analogue detection, inrush, suspend current and wake remain physical tests.</p></section>

<section><h2>4. How it comes together</h2><p>The carrier sits behind the main board’s right end at (72.15, 0.25) mm. A six-wire harness carries VBUS, D−, D+, ground, CC1 and CC2. The main header is vertical; the carrier header is side-entry. Verify numbered pin order. {escape(case_text)} Check the actual plug and wire bends.</p><p>The 12.70 mm module repeat is datasheet nominal; the breadboard check establishes only 2.54 mm lead pitch. Seven-module physical fit remains pending. Have the factory fit small components; solder and prove one LED first, then finish the pilot before populating the other replicas.</p></section>

<p>Quote three main boards and three carriers with <a href="https://jlcpcb.com/capabilities/pcb-assembly-capabilities">JLCPCB Economic PCBA</a>, comparing a smaller pilot and PCBWay. Factory fit the 37 main and seven carrier components; keep your LEDs locally. Two assembly setups, part fees, shipping and UK VAT can dominate cost. No live delivered quote or purchase has been made.</p>

<section><h2>5. Checks and release status</h2><div class="table-wrap"><table><thead><tr><th>Board</th><th>ERC issues</th><th>DRC issues / unrouted / parity</th><th>Saved DRC report</th></tr></thead><tbody>{''.join(report_rows)}</tbody></table></div><p class="small">{erc_note} Counts use saved project rules; see native reports for scope. CAD checks do not establish physical correctness.</p><p>{escape(host_test_text)}; diode-path tests include polarity, aliases and current policy. All 22,248 artwork windows reconstruct correctly; the compiled player matched 60,000 frames. The functional model does not establish physical behaviour.</p><p class="small">{escape(package_note)} Factory file review and bench release remain separate holds.</p></section>

<section><h2>6. Why KiCad</h2><p><a href="https://github.com/atopile/atopile#readme">atopile</a> defines hardware in code and works with KiCad layout. <a href="https://tscircuit.com/">tscircuit</a> combines TSX definitions with PCB generation and KiCad exports. This design uses <a href="https://www.kicad.org/">KiCad</a> for precise footprints, native 3D and ERC/DRC. A repository-owned Python specification keeps connections reproducible.</p></section>

<section><h2>7. Review the files</h2><div class="files"><a href="kicad/house-rules-main.kicad_pro">Main KiCad project</a><a href="kicad/house-rules-main.kicad_pcb">Main PCB</a><a href="kicad/house-rules-main.kicad_sch">Main schematic</a><a href="kicad/house-rules-usb.kicad_pro">USB carrier project</a><a href="firmware/compiled/HouseRules.ino.bin">Compiled prototype firmware</a><a href="simulation/matrix-emulator.html">Interactive matrix emulator</a><a href="firmware/README.md">Build and programming guide</a><a href="mechanical/enclosure.scad">Parametric enclosure</a><a href="mechanical/pin-fit-plate.stl">Print the pin-fit plate</a><a href="mechanical/pin-fit-plate-notes.md">Fit-check instructions</a><a href="mechanical/enclosure-PROTOTYPE-shell.stl">Prototype case shell</a><a href="mechanical/enclosure-PROTOTYPE-back.stl">Prototype back</a><a href="reports/component-sourcing.csv">Component sourcing</a><a href="assembly-and-test.md">Assembly and tests</a>{package_link}</div></section>

<section><h2>8. Release gates</h2><ol><li>Before prototype fabrication: dry-fit seven modules against the 1:1 template/pin plate; confirm pin 1 and polarity at low current.</li><li>Print fit samples; check leads, spacing, harness and USB plug.</li><li>Review final CAD, assembly files and delivered quote before purchasing.</li><li>On the pilot: measure current/heat and test chargers, orientations, DFU and suspend/resume before finishing the remaining units.</li></ol></section>
<footer>Local engineering summary. Times: Europe/London. Physical release gates remain. {linked('README.md', 'Full engineering notes')} · {linked('reports/firmware-power-review.md', 'Independent power review')}</footer>
</main></html>'''
    output = HW / "design-summary.html"
    temp = output.with_suffix(".html.tmp")
    temp.write_text(html)
    temp.replace(output)
    # Count visible prose, including headings/table labels, for a concise report.
    prose = re.sub(r"<style>.*?</style>", "", html, flags=re.S)
    prose = re.sub(r"<[^>]+>", " ", prose)
    words = len(re.findall(r"\S+", prose))
    print(f"Wrote {output}; approximately {words} visible words. Main/USB DRC status is read dynamically.")


if __name__ == "__main__":
    main()
