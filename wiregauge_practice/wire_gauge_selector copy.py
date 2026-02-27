# wire_gauge_selector.py
# Wire Gauge Selector (Copper or Aluminum, Single-Phase, Basic NEC-based)
# Now with continuous load factor (125%) and aluminum support

# Ampacity for Copper - NEC Table 310.15(B)(16) @ 30°C ambient, ≤3 CCC
# Format: AWG: (60°C, 75°C, 90°C)
ampacity_cu = {
    14: (15, 20, 25),
    12: (20, 25, 30),
    10: (30, 35, 40),
    8: (40, 50, 55),
    6: (55, 65, 75),
    4: (70, 85, 95),
    3: (85, 100, 110),
    2: (95, 115, 130),
    1: (110, 130, 145),
    '1/0': (125, 150, 170),
    '2/0': (145, 175, 195),
    '3/0': (165, 200, 225),
    '4/0': (195, 230, 260),
}

# Ampacity for Aluminum - NEC Table 310.15(B)(16)
ampacity_al = {
    12: (15, 20, 25),
    10: (25, 30, 35),
    8: (35, 40, 45),
    6: (40, 50, 55),
    4: (55, 65, 75),
    3: (65, 75, 85),
    2: (75, 90, 100),
    1: (85, 100, 115),
    '1/0': (100, 120, 135),
    '2/0': (115, 135, 150),
    '3/0': (130, 155, 175),
    '4/0': (150, 180, 205),
}

# DC Resistance (ohms per 1000 ft, uncoated at ~75°C)
resistance_cu = {
    14: 2.525,
    12: 1.588,
    10: 0.999,
    8: 0.628,
    6: 0.395,
    4: 0.248,
    3: 0.197,
    2: 0.156,
    1: 0.124,
    '1/0': 0.099,
    '2/0': 0.078,
    '3/0': 0.062,
    '4/0': 0.049,
}

resistance_al = {
    12: 2.659,   # Approx from NEC Ch.9 Table 8 aluminum
    10: 1.671,
    8: 1.052,
    6: 0.661,
    4: 0.416,
    3: 0.330,
    2: 0.262,
    1: 0.208,
    '1/0': 0.165,
    '2/0': 0.131,
    '3/0': 0.104,
    '4/0': 0.082,
}

def get_ampacity_table(material):
    return ampacity_cu if material.lower() == 'copper' else ampacity_al

def get_resistance_table(material):
    return resistance_cu if material.lower() == 'copper' else resistance_al

def get_gauge_options(material):
    amp_table = get_ampacity_table(material)
    ints = [g for g in amp_table if isinstance(g, int)]
    kcmils = [g for g in amp_table if isinstance(g, str)]
    sorted_ints = sorted(ints, reverse=True)  # 14,12,...1
    sorted_kcmils = sorted(kcmils)           # '1/0','2/0',...
    return sorted_ints + sorted_kcmils       # smallest wire → largest

def find_min_gauge(required_ampacity, temp_idx, material):
    options = get_gauge_options(material)
    amp_table = get_ampacity_table(material)
    for awg in options:
        amps = amp_table[awg][temp_idx]
        if amps >= required_ampacity:
            return awg, amps
    return None, None

def voltage_drop(current, length_ft, awg, voltage, material):
    res_table = get_resistance_table(material)
    if awg not in res_table:
        return None, None
    r = res_table[awg]
    vd_volts = 2 * current * length_ft * r / 1000  # single-phase
    vd_percent = (vd_volts / voltage) * 100 if voltage != 0 else 0
    return vd_volts, vd_percent

# ────────────────────────────────────────────────
# Safe input helpers
# ────────────────────────────────────────────────

def safe_float(prompt, default=None):
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            return float(raw)
        except ValueError:
            print(f"Invalid number: '{raw}' — please try again.")

def safe_int(prompt, valid_options=None, default=None):
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            val = int(raw)
            if valid_options and val not in valid_options:
                print(f"Please enter one of: {valid_options}")
                continue
            return val
        except ValueError:
            print(f"Invalid integer: '{raw}' — please try again.")

def safe_yes_no(prompt, default='n'):
    while True:
        raw = input(prompt).strip().lower()
        if raw == "":
            return default == 'y'
        if raw in ['y', 'yes']:
            return True
        if raw in ['n', 'no']:
            return False
        print("Please enter y/yes or n/no.")

# ────────────────────────────────────────────────
# Main program
# ────────────────────────────────────────────────

def main():
    print("Wire Gauge Selector (Copper or Aluminum, Single-Phase, Basic NEC-based)")
    print("Enter values below. Press Enter to use defaults where shown.\n")

    material_raw = input("Conductor material (copper or aluminum) [default copper]: ").strip().lower() or 'copper'
    material = 'copper' if material_raw in ['c', 'cu', 'copper'] else 'aluminum' if material_raw in ['a', 'al', 'aluminum'] else 'copper'
    print(f"Using {material.capitalize()}.\n")

    current  = safe_float("Load current (A): ")
    voltage  = safe_float("Circuit voltage (V): ")
    length   = safe_float("One-way run length (feet): ")
    temp_idx = safe_int("Insulation temp rating (0=60°C, 1=75°C, 2=90°C) [default 1]: ",
                        valid_options=[0, 1, 2], default=1)
    is_continuous = safe_yes_no("Is this a continuous load (>3 hours)? (y/n) [default n]: ", default='n')
    vd_max   = safe_float("Max allowable voltage drop % (e.g. 3, no % sign) [default 3]: ",
                          default=3.0)

    required_amp = current * 1.25 if is_continuous else current
    cont_note = " (includes 125% continuous factor)" if is_continuous else ""

    awg, allowed_amps = find_min_gauge(required_amp, temp_idx, material)
    if awg is None:
        print("\nNo suitable gauge found — load is too high for common sizes!")
        return

    print(f"\nMinimum ampacity needed: {required_amp:.1f} A{cont_note}")
    print(f"Smallest gauge meeting ampacity: {awg} (allows {allowed_amps} A at selected temp rating)")

    vd_volts, vd_percent = voltage_drop(current, length, awg, voltage, material)
    if vd_volts is not None:
        print(f"Calculated voltage drop: {vd_volts:.2f} V  ({vd_percent:.2f}%)")

        current_awg = awg
        while vd_percent > vd_max:
            print(f"  → Exceeds {vd_max}% limit! Trying larger wire...")
            options = get_gauge_options(material)
            try:
                idx = options.index(current_awg)
                if idx == len(options) - 1:
                    print("  Cannot improve further — largest wire in table still exceeds limit.")
                    break
                current_awg = options[idx + 1]
            except ValueError:
                print("Gauge not found in list — stopping.")
                break

            vd_volts, vd_percent = voltage_drop(current, length, current_awg, voltage, material)
            if vd_volts is not None:
                print(f"  {current_awg} AWG → drop {vd_percent:.2f}% ({vd_volts:.2f} V)")

        if vd_percent <= vd_max:
            print(f"\nFinal recommendation: {current_awg} AWG (meets both ampacity and voltage drop limit)")
        else:
            print("\nEven the largest wire exceeds voltage drop limit — consider:")
            print("  • Shorten the run length")
            print("  • Reduce the load current")
            print("  • Use parallel conductors")
            print("  • Increase allowable drop (if code permits)")
    else:
        print("Resistance data not available for selected gauge.")

    print("\nNotes & Disclaimers:")
    print("- Uses NEC 2023 Table 310.15(B)(16) ampacities and Ch.9 Table 8 resistances (approximate)")
    print("- Always verify with latest NEC and local codes")
    print("- Apply full derating (ambient, bundling >3 CCC, etc.) as needed")
    print("- Voltage drop is recommended (NEC informational note), not required")
    print("- For 3-phase, ambient derating, or more — let me know!")

if __name__ == "__main__":
    main()
    