#!/usr/bin/env python3
"""Generate 1920x1080 slide PNGs for the FIND EVIL! demo video."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).parent / "slides"
OUT.mkdir(exist_ok=True)

W, H = 1920, 1080

# palette
BG     = (13, 17, 23)
PANEL  = (22, 27, 34)
PANEL2 = (28, 33, 40)
TEXT   = (230, 237, 243)
MUTED  = (139, 148, 158)
GREEN  = (63, 185, 80)
RED    = (248, 81, 73)
AMBER  = (210, 153, 34)
BLUE   = (88, 166, 255)
PURPLE = (188, 140, 255)
LINE   = (48, 54, 61)

F = "C:/Windows/Fonts/"
def font(name, size):
    return ImageFont.truetype(F + name, size)

H1   = font("arialbd.ttf", 92)
H2   = font("arialbd.ttf", 64)
H3   = font("arialbd.ttf", 46)
BODY = font("arial.ttf", 40)
BODYB= font("arialbd.ttf", 40)
SMALL= font("arial.ttf", 32)
MONO = font("consola.ttf", 34)
MONOS= font("consola.ttf", 28)
TINY = font("arial.ttf", 26)
BADGE= font("arialbd.ttf", 30)


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # header bar
    d.rectangle([0, 0, W, 78], fill=PANEL)
    d.line([0, 78, W, 78], fill=LINE, width=2)
    d.text((60, 22), "FIND EVIL!", font=font("arialbd.ttf", 38), fill=RED)
    d.text((280, 28), "Autonomous Forensic IR Agent", font=SMALL, fill=MUTED)
    d.text((W - 470, 28), "Case #20161104 — VANKO", font=MONOS, fill=GREEN)
    # footer bar
    d.line([0, H - 64, W, H - 64], fill=LINE, width=2)
    d.text((60, H - 50), "gpt-5.4-mini  +  SIFT Workstation  +  MCP", font=TINY, fill=MUTED)
    d.text((W - 560, H - 50), "github.com/OLGTX303/find-evil-sift-agent", font=TINY, fill=MUTED)
    return img, d


def wrap(d, text, fnt, maxw):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def badge(d, x, y, text, color):
    pad = 18
    w = d.textlength(text, font=BADGE)
    d.rounded_rectangle([x, y, x + w + pad * 2, y + 48], radius=10, fill=color)
    d.text((x + pad, y + 8), text, font=BADGE, fill=(13, 17, 23))
    return x + w + pad * 2


def panel(d, box, fill=PANEL, outline=LINE):
    d.rounded_rectangle(box, radius=16, fill=fill, outline=outline, width=2)


def check(d, x, y, color, s=34, w=6):
    d.line([(x, y + s*0.55), (x + s*0.35, y + s*0.92)], fill=color, width=w)
    d.line([(x + s*0.35, y + s*0.92), (x + s*0.98, y + s*0.12)], fill=color, width=w)


def cross(d, x, y, color, s=30, w=6):
    d.line([(x, y), (x + s, y + s)], fill=color, width=w)
    d.line([(x + s, y), (x, y + s)], fill=color, width=w)


def save(img, name):
    img.save(OUT / f"{name}.png")
    print("saved", name)


# ---- 01 title ----
def s01():
    img, d = base()
    d.text((W/2, 320), "FIND EVIL!", font=H1, fill=RED, anchor="mm")
    d.text((W/2, 430), "Autonomous Forensic Incident Response Agent", font=H3, fill=TEXT, anchor="mm")
    # chips
    chips = [("gpt-5.4-mini", BLUE), ("SIFT Workstation", GREEN), ("MCP · 18 tools", PURPLE)]
    total = sum(d.textlength(c[0], font=BODYB) + 70 for c in chips) + 40 * (len(chips) - 1)
    x = (W - total) / 2
    for label, col in chips:
        w = d.textlength(label, font=BODYB) + 70
        d.rounded_rectangle([x, 560, x + w, 632], radius=14, outline=col, width=3)
        d.text((x + 35, 575), label, font=BODYB, fill=col)
        x += w + 40
    d.text((W/2, 740), "From a raw 119 GB disk image to a courtroom-ready report — with no human in the loop.",
           font=BODY, fill=MUTED, anchor="mm")
    save(img, "01_title")


# ---- 02 case ----
def s02():
    img, d = base()
    d.text((120, 150), "The Target", font=H2, fill=TEXT)
    d.line([120, 240, 700, 240], fill=RED, width=4)
    rows = [
        ("Device", "Microsoft Surface 3"),
        ("Acquired", "2016-11-04  ·  Ovie Carroll, DFIR.training"),
        ("Evidence", "surface_physical.E01–E21  (EWF / Expert Witness Format)"),
        ("Size", "119 GB physical image  ·  6 partitions  ·  NTFS"),
        ("MD5", "4032d556cc866c23f1e797410e95603c"),
    ]
    y = 320
    for k, v in rows:
        d.text((120, y), k, font=BODYB, fill=GREEN)
        d.text((420, y), v, font=MONO if k in ("MD5",) else BODY, fill=TEXT)
        y += 92
    panel(d, [120, y + 10, W - 120, y + 140])
    d.text((150, y + 45), "MISSION:", font=BODYB, fill=RED)
    d.text((360, y + 45), "Find the evil hiding on this machine.", font=BODY, fill=TEXT)
    save(img, "02_case")


# ---- 03 problem ----
def s03():
    img, d = base()
    d.text((120, 150), "Why Autonomy?", font=H2, fill=TEXT)
    d.line([120, 240, 760, 240], fill=RED, width=4)
    # two columns
    panel(d, [120, 320, 930, 820], fill=PANEL)
    d.text((160, 360), "Manual DFIR", font=H3, fill=RED)
    for i, t in enumerate(["Hours mounting & imaging", "Hand-parsing event logs",
                            "Walking the registry by hand", "Correlating artifacts manually",
                            "Easy to miss the one clue"]):
        cross(d, 162, 458 + i*68, RED, s=28, w=5)
        d.text((220, 450 + i*68), t, font=BODY, fill=MUTED)
    panel(d, [990, 320, W - 120, 820], fill=PANEL)
    d.text((1030, 360), "AI Agent", font=H3, fill=GREEN)
    for i, t in enumerate(["Mounts & enumerates itself", "Runs 18 forensic tools",
                            "Self-corrects on errors", "Confidence-scored findings",
                            "Full audit trail of every step"]):
        check(d, 1030, 452 + i*68, GREEN, s=30, w=6)
        d.text((1090, 450 + i*68), t, font=BODY, fill=TEXT)
    save(img, "03_problem")


# ---- 04 architecture ----
def s04():
    img, d = base()
    d.text((120, 130), "Architecture", font=H2, fill=TEXT)
    d.line([120, 220, 640, 220], fill=RED, width=4)
    # host box
    panel(d, [120, 290, 920, 900], fill=PANEL)
    d.text((150, 320), "Windows Host", font=H3, fill=BLUE)
    panel(d, [160, 410, 880, 530], fill=PANEL2, outline=BLUE)
    d.text((185, 435), "orchestrator.py", font=MONO, fill=TEXT)
    d.text((185, 478), "agent loop  ·  gpt-5.4-mini", font=MONOS, fill=MUTED)
    panel(d, [160, 560, 880, 860], fill=PANEL2, outline=PURPLE)
    d.text((185, 585), "sift-mcp  (stdio MCP server)", font=MONO, fill=TEXT)
    d.text((185, 632), "18 forensic tools:", font=MONOS, fill=MUTED)
    tools = ["mount_image", "list_users", "find_suspicious", "parse_evtx",
             "yara_scan", "run_log2timeline", "get_run_keys", "hash_file"]
    for i, t in enumerate(tools):
        cx = 185 + (i % 2) * 350
        cy = 685 + (i // 2) * 44
        d.text((cx, cy), "• " + t, font=MONOS, fill=GREEN)
    # arrow
    d.text((948, 580), "SSH", font=BODYB, fill=AMBER)
    d.line([930, 620, 1000, 620], fill=AMBER, width=4)
    d.polygon([(1000, 610), (1020, 620), (1000, 630)], fill=AMBER)
    # VM box
    panel(d, [1030, 290, W - 120, 900], fill=PANEL)
    d.text((1060, 320), "SIFT Workstation VM", font=H3, fill=GREEN)
    d.text((1060, 392), "Ubuntu 22.04  ·  200+ IR tools  ·  VMware NAT", font=SMALL, fill=MUTED)
    panel(d, [1070, 460, W - 160, 840], fill=PANEL2, outline=GREEN)
    chain = ["surface_physical.E01  (read-only)", "  v  ewfmount", "/mnt/ewf/ewf1",
             "  v  kpartx", "/dev/mapper/loop10p4", "  v  ntfs-3g  (ro)", "/mnt/windows/  >> MOUNTED"]
    for i, t in enumerate(chain):
        col = GREEN if t.startswith("/mnt/windows") else (AMBER if t.strip().startswith("v ") else TEXT)
        d.text((1100, 495 + i*46), t, font=MONO, fill=col)
    d.text((130, 925), "Evidence is mounted READ-ONLY — the agent investigates but never alters the original image.",
           font=SMALL, fill=RED)
    save(img, "04_arch")


# ---- 05 loop ----
def s05():
    img, d = base()
    d.text((120, 130), "The Autonomous Loop", font=H2, fill=TEXT)
    d.line([120, 220, 880, 220], fill=RED, width=4)
    steps = [
        ("1", "setup_evidence", "share & verify the image"),
        ("2", "mount_image", "ewfmount + kpartx + ntfs-3g"),
        ("3", "list_users / system_info", "enumerate the machine"),
        ("4", "find_suspicious_executables", "scan every user profile"),
        ("5", "parse_evtx + get_logon_events", "Security.evtx anomalies"),
        ("6", "yara_scan + hash_file", "malware detection"),
        ("7", "run_log2timeline", "full super-timeline (async)"),
        ("8", "synthesize findings_report.json", "confidence-scored output"),
    ]
    y = 300
    for n, cmd, desc in steps:
        d.ellipse([120, y, 168, y+48], fill=GREEN)
        d.text((144, y+24), n, font=BADGE, fill=BG, anchor="mm")
        d.text((200, y+4), cmd, font=MONO, fill=TEXT)
        d.text((760, y+8), desc, font=SMALL, fill=MUTED)
        y += 66
    panel(d, [120, y + 14, W - 120, y + 120], outline=AMBER)
    d.text((150, y + 48), "Self-correcting:", font=BODYB, fill=AMBER)
    d.text((470, y + 48), "on any tool error the agent tries an alternate path — every step logged to JSONL.",
           font=SMALL, fill=TEXT)
    save(img, "05_loop")


# ---- finding slide factory ----
def finding(name, fid, sev, sevcol, cat, title, bullets, conf):
    img, d = base()
    x = 120
    badge(d, x, 150, fid, MUTED)
    x = badge(d, x + 20 + d.textlength(fid, font=BADGE), 150, sev, sevcol) if False else x
    # simpler badges row
    img, d = base()
    bx = 120
    bx = badge(d, bx, 140, fid, BLUE) + 20
    bx = badge(d, bx, 140, sev, sevcol) + 20
    badge(d, bx, 140, cat, PURPLE)
    # title
    for i, ln in enumerate(wrap(d, title, H3, W - 240)):
        d.text((120, 230 + i*60), ln, font=H3, fill=TEXT)
    ty = 230 + len(wrap(d, title, H3, W - 240)) * 60 + 30
    # evidence panel
    panel(d, [120, ty, W - 120, 880])
    d.text((150, ty + 24), "EVIDENCE", font=BODYB, fill=GREEN)
    yy = ty + 92
    for b in bullets:
        d.text((150, yy), "›", font=MONO, fill=AMBER)
        for j, ln in enumerate(wrap(d, b, MONOS, W - 360)):
            d.text((200, yy + j*38), ln, font=MONOS, fill=TEXT)
        yy += 38 * max(1, len(wrap(d, b, MONOS, W - 360))) + 18
    # confidence bar
    d.text((150, 800), "Confidence", font=SMALL, fill=MUTED)
    d.rounded_rectangle([340, 802, 340 + 600, 832], radius=8, fill=PANEL2)
    d.rounded_rectangle([340, 802, 340 + int(600*conf), 832], radius=8, fill=sevcol)
    d.text((960, 800), f"{int(conf*100)}%", font=BODYB, fill=sevcol)
    save(img, name)


def s06():
    finding("06_find1", "F001", "CRITICAL", RED, "surveillance",
            "Unauthorized WiFi Packet Capture on Public Network",
            ["Documents/starbucks pcap.pcap  +  starbucks.csv",
             "Prefetch: NETSTUMBLER.EXE-C14B26F4.pf  (confirmed executed)",
             "Downloads: Acrylic_WiFi_Professional_v3.0.5802...Setup.exe",
             "Downloads: netstumblerinstaller_0_4_0.exe  (two copies)"], 0.97)

def s07():
    finding("07_find2", "F002", "CRITICAL", RED, "intel/documents",
            "Documents on Weaponizing Technology",
            ["Research to Weaponize the Ion Thruster.docx",
             "ZF DNA splice test notes.docx",
             "Rapid cell regeneration research.docx",
             "Recent LNK: ic-enhanced-spec-sheet.pdf  (ion thruster spec)"], 0.92)

def s08():
    finding("08_find3", "F003 + F006", "HIGH", AMBER, "anti-forensics",
            "Evidence Destruction — SDelete + VeraCrypt",
            ["Windows/System32/sdelete.exe + sdelete64.exe  (unusual location)",
             "Prefetch: SDELETE.EXE-FBA93810.pf  (confirmed executed)",
             "Prefetch: VERACRYPT FORMAT.EXE  (encrypted volume created)",
             "Downloads: VeraCrypt Setup 1.17.exe  +  SDelete.zip"], 0.98)

def s09():
    finding("09_find4", "F004 + F005", "HIGH", AMBER, "suspicious exe",
            "Malware Dropper + Typosquatted Exfil Tool",
            ["AppData/Local/Temp/set_PxRcHIFy.exe  (random-named PE32 dropper)",
             "  md5: 6f047f29414952777ace6d1cf5b598bc",
             "Downloads/NETWIORK LICENSE SERVER 3.4.1.exe  (intentional typo)",
             "  strings: HttpSendRequestW, FtpFindFirstFileA  ·  requireAdministrator"], 0.88)

def s10():
    finding("10_find5", "F007 + F008", "MEDIUM", BLUE, "attribution",
            "Counter-Forensics & Operator Identity",
            ["Desktop/security.evtx  (26,737 events — anomalous location)",
             "Event 4648 / 4624 ties activity to:  anthony.vanko@gmail.com",
             "Documents/NinaResearch/  +  NinaResearch.zip  (targeted research)"], 0.82)


# ---- 11 results ----
def s11():
    img, d = base()
    d.text((120, 130), "Results", font=H2, fill=TEXT)
    d.line([120, 220, 460, 220], fill=RED, width=4)
    # stat cards
    cards = [("8", "Findings", GREEN), ("2", "Critical", RED), ("4", "High", AMBER), ("2", "Medium", BLUE)]
    cw = 400
    x = 120
    for num, lbl, col in cards:
        panel(d, [x, 290, x + cw - 30, 520], outline=col)
        d.text((x + (cw-30)/2, 380), num, font=H1, fill=col, anchor="mm")
        d.text((x + (cw-30)/2, 470), lbl, font=H3, fill=TEXT, anchor="mm")
        x += cw
    # explainability points
    panel(d, [120, 560, W - 120, 880])
    d.text((150, 590), "Explainable & Reproducible", font=H3, fill=GREEN)
    pts = ["Every finding carries evidence, a confidence score, and a recommended action",
           "False positives recorded — e.g. CNN.EXE confirmed as the legit CNN Store app",
           "Full JSONL audit log: every tool call, result, and decision is timestamped",
           "Read-only evidence handling preserves chain of custody"]
    for i, p in enumerate(pts):
        check(d, 152, 684 + i*52, GREEN, s=26, w=5)
        d.text((200, 680 + i*52), p, font=SMALL, fill=TEXT)
    save(img, "11_results")


# ---- 12 outro ----
def s12():
    img, d = base()
    d.text((W/2, 300), "FIND EVIL!", font=H1, fill=RED, anchor="mm")
    d.text((W/2, 410), "Autonomous Incident Response, Powered by AI", font=H3, fill=TEXT, anchor="mm")
    panel(d, [460, 510, W - 460, 760])
    rows = [("Subject identified", "anthony.vanko@gmail.com", GREEN),
            ("Findings", "8  (2 critical, 4 high, 2 medium)", TEXT),
            ("License", "MIT — open source", BLUE),
            ("Repo", "github.com/OLGTX303/find-evil-sift-agent", PURPLE)]
    y = 545
    for k, v, c in rows:
        d.text((500, y), k, font=BODYB, fill=MUTED)
        d.text((900, y), v, font=BODY, fill=c)
        y += 54
    d.text((W/2, 850), "Thank you.", font=H2, fill=TEXT, anchor="mm")
    save(img, "12_outro")


if __name__ == "__main__":
    for fn in [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12]:
        fn()
    print("ALL SLIDES DONE")
