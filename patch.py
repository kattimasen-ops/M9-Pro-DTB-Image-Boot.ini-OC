import re
import subprocess
import os

INPUT_DTB = "rk3326-k36s-linux.dtb"
OUTPUT_DTB = "rk3326-m9pro-linux.dtb"

if not os.path.exists(INPUT_DTB):
    print(f"ERROR: {INPUT_DTB} nicht gefunden!")
    exit(1)

print("[*] Dekompiliere DTB...")
subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-f", "-o", "base.dts", INPUT_DTB], check=True)
with open("base.dts", "r", encoding="utf-8") as f:
    dts = f.read()

replacements = [
    ("rk3326-k36s-linux", "rk3326-m9pro-linux"),
    ("rk3326-k36s", "rk3326-m9pro"),
    ("r36s", "M9 Pro - St0len-One"),
    ("r36t", "M9 Pro - St0len-One"),
    ("k36s", "M9 Pro - St0len-One"),
    ("k36", "M9 Pro - St0len-One"),
    ("aislpc", "M9 Pro"),
]
for old, new in replacements:
    dts = dts.replace(old, new)

dts = re.sub(r'model\s*=\s*"[^"]*";', 'model = "M9 Pro - St0len-One";', dts, count=1)

dts = re.sub(r'(compatible\s*=\s*")([^"]*)(";)',
             lambda m: m.group(1) + m.group(2).replace('k36', 'm9pro') + m.group(3),
             dts, count=1)

if re.search(r'\bpanel\s*\{', dts):
    dts = re.sub(r'(\bpanel\s*\{[^}]*?)(\bmodel\s*=\s*"[^"]*";)?',
                 lambda m: m.group(1) + '\n\t\tmodel = "M9 Pro Display";' if not m.group(2) else m.group(0),
                 dts, flags=re.DOTALL)
else:
    panel_node = '''
panel {
    compatible = "simple-panel";
    model = "M9 Pro Display";
    status = "okay";
};
'''
    last_brace = dts.rfind('};')
    if last_brace != -1:
        dts = dts[:last_brace] + panel_node + "\n" + dts[last_brace:]

if 'm9pro,board' not in dts:
    dts = dts.replace('/ {', '/ {\n\tm9pro,board = "M9 Pro - St0len-One";', 1)

with open("merged.dts", "w", encoding="utf-8") as f:
    f.write(dts)

print("[*] Kompiliere finale DTB...")
subprocess.run(["dtc", "-I", "dts", "-O", "dtb", "-f",
                "-Wno-unique_unit_address", "-Wno-graph_child_address",
                "-o", OUTPUT_DTB, "merged.dts"], check=True)

if os.path.exists("boot.ini"):
    with open("boot.ini", "r", encoding="utf-8") as f:
        boot_ini = f.read()
    boot_ini_new = re.sub(r'[\w\-\.]*\.dtb', OUTPUT_DTB, boot_ini)
    with open("boot.ini", "w", encoding="utf-8") as f:
        f.write(boot_ini_new)
    print("[*] boot.ini aktualisiert auf", OUTPUT_DTB)
else:
    print("[!] boot.ini nicht gefunden – überspringe")

subprocess.run(["dtc", "-I", "dtb", "-O", "dts", "-f", "-o", "verify.dts", OUTPUT_DTB], check=True)
with open("verify.dts", "r", encoding="utf-8") as f:
    final_dts = f.read()

log = [
    "==================================================",
    "      M9 PRO DTB PATCH & VERIFICATION",
    "==================================================",
    f"[+] Quelle: {INPUT_DTB}",
    f"[+] Ausgabe: {OUTPUT_DTB}",
    "[+] Gerätename ersetzt:",
]
for old, new in replacements:
    log.append(f"  - {old} -> {new}: {'OK' if old not in final_dts else 'MISSING'}")
log.append("[+] Root model: " + ('OK' if 'model = "M9 Pro - St0len-One";' in final_dts else 'MISSING'))
log.append("[+] Compatible: " + ('OK' if 'rk3326-m9pro' in final_dts else 'MISSING'))
log.append("[+] Panel info: " + ('OK' if 'M9 Pro Display' in final_dts else 'MISSING'))
log.append("[+] m9pro,board: " + ('OK' if 'm9pro,board' in final_dts else 'MISSING'))

log_text = "\n".join(log)
with open("patch_verification.log", "w", encoding="utf-8") as f:
    f.write(log_text)
print(log_text)
print("[✓] Fertig!")