import streamlit as st
import pandas as pd
import numpy as np
import math
from math import ceil
from fpdf import FPDF

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="Solar System Sizing + Critical Load", layout="wide")
st.title("🔆 Solar System Sizing Calculator (Full + Critical Load)")
#st.caption("Unified version combining sizing, module selection, and PDF export")

st.markdown("---")

# ---------------------------
# 1) Appliance input with critical load flag
# ---------------------------

st.header("1️⃣ Appliance / Load List")
st.info("Add your appliances. Mark *Critical Load* if this device must always remain powered (e.g. lights, router).")

# Initialize session state for appliance table
if "appliances" not in st.session_state:
    # columns: name, power_w, qty, hours_per_day, surge_w, critical (bool)
    st.session_state.appliances = pd.DataFrame(columns=[
        "name", "power_w", "qty", "hours_per_day", "surge_w", "critical"
    ])

# Form to add a load
with st.form("add_load_form", clear_on_submit=True):
    name = st.text_input("Appliance name", value="LED Bulb")
    power_w = st.number_input("Power (W)", min_value=0.0, value=10.0, step=1.0)
    qty = st.number_input("Quantity", min_value=1, value=1, step=1)
    hours = st.number_input("Hours per day", min_value=0.0, value=4.0, step=0.5)
    surge = st.number_input("Start-up surge (W) — optional", min_value=0.0, value=0.0, step=10.0)
    critical = st.checkbox("Critical load?", value=False)
    add = st.form_submit_button("Add load")
    if add:
        row = {
            "name": name,
            "power_w": float(power_w),
            "qty": int(qty),
            "hours_per_day": float(hours),
            "surge_w": float(surge),
            "critical": bool(critical)
        }
        st.session_state.appliances = pd.concat(
            [st.session_state.appliances, pd.DataFrame([row])],
            ignore_index=True
        )

# Editable table
st.markdown("### Current loads (you can edit or delete rows)")
edited = st.data_editor(
    st.session_state.appliances,
    num_rows="dynamic",
    use_container_width=True
)
st.session_state.appliances = edited.copy()

st.markdown("---")

# ---------------------------
# 2) System & user preference settings
# ---------------------------

st.header("2️⃣ System & Equipment Preferences")

col1, col2, col3 = st.columns(3)
with col1:
    system_voltage = st.selectbox("System nominal voltage (V)", options=[12, 24, 48], index=1)
with col2:
    ps_h = st.slider("Peak Sun Hours (PSH) — full sun equivalent h/day", 2.0, 8.0, 5.0, 0.25)
with col3:
    autonomy_days = st.number_input("Battery autonomy (days)", min_value=0, max_value=7, value=1, step=1)

st.markdown("### Battery / Panel Module Options & Efficiencies")

col4, col5, col6 = st.columns(3)
with col4:
    battery_chem = st.selectbox("Battery chemistry", ["LiFePO4", "Lithium-ion", "Lead-acid (flooded/AGM)", "Tubular"])
with col5:
    preferred_batt_ah = st.selectbox("Preferred battery module (Ah)", [50, 100, 150, 200, 250, 300], index=1)
with col6:
    preferred_panel_w = st.selectbox("Preferred PV panel wattage (W)", [100, 150, 200, 250, 300, 360, 400, 450, 500, 540, 600], index=5)

# Default usable DoD mapping
default_dod_map = {
    "LiFePO4": 0.8,
    "Lithium-ion": 0.8,
    "Lead-acid (flooded/AGM)": 0.5,
    "Tubular": 0.5
}
dod_default = default_dod_map.get(battery_chem, 0.5)

usable_dod = st.number_input("Usable Depth of Discharge (DoD)", min_value=0.2, max_value=1.0, value=float(dod_default), step=0.05)

st.markdown("### Efficiency & Margins (advanced)")
eta_inv = st.number_input("Inverter efficiency", min_value=0.7, max_value=0.99, value=0.90, step=0.01)
eta_batt_roundtrip = st.number_input("Battery round-trip efficiency", min_value=0.6, max_value=0.99, value=0.90, step=0.01)
eta_misc = st.number_input("PV derate (temp, wiring, dust) factor", min_value=0.6, max_value=0.95, value=0.80, step=0.01)
safety_margin = st.number_input("Safety margin (multiply PV)", min_value=1.0, max_value=1.5, value=1.15, step=0.01)

st.markdown("---")

# ---------------------------
# 3) Computation logic
# ---------------------------

# Copy loads for computation
loads = st.session_state.appliances.copy()

# Compute energies
if not loads.empty:
    loads["energy_wh"] = loads["power_w"] * loads["qty"] * loads["hours_per_day"]
else:
    loads["energy_wh"] = 0.0

E_total = loads["energy_wh"].sum()
E_critical = loads.loc[loads["critical"], "energy_wh"].sum()

# Function to compute required PV size ignoring losses:
def recommended_system(E_wh, ps_h, eta_inv, eta_batt, eta_misc, safety):
    E_from_panels = E_wh / (eta_inv * eta_batt)
    pv_watts = E_from_panels / (ps_h * eta_misc)
    pv_watts *= safety
    return E_from_panels, pv_watts

E_from_panels_full, pv_watts_full = recommended_system(
    E_total, ps_h, eta_inv, eta_batt_roundtrip, eta_misc, safety_margin
)
E_from_panels_crit, pv_watts_crit = recommended_system(
    E_critical, ps_h, eta_inv, eta_batt_roundtrip, eta_misc, safety_margin
)

# Battery sizing function (nominal)
def battery_req(E_wh, autonomy, eta_batt, Vsys):
    wh = (E_wh * autonomy) / eta_batt
    ah = wh / Vsys
    return wh, ah

bat_wh_full, bat_ah_full = battery_req(E_total, autonomy_days, eta_batt_roundtrip, system_voltage)
bat_wh_crit, bat_ah_crit = battery_req(E_critical, autonomy_days, eta_batt_roundtrip, system_voltage)

# Compute number of battery modules
module_wh = preferred_batt_ah * system_voltage
usable_module_wh = module_wh * usable_dod
if usable_module_wh > 0:
    num_batt_full = ceil(bat_wh_full / usable_module_wh)
    num_batt_crit = ceil(bat_wh_crit / usable_module_wh)
else:
    num_batt_full = num_batt_crit = 0

# Panel count
if preferred_panel_w > 0:
    num_panels_full = ceil(pv_watts_full / preferred_panel_w)
    num_panels_crit = ceil(pv_watts_crit / preferred_panel_w)
else:
    num_panels_full = num_panels_crit = 0

# Inverter sizing: pick worst-case continuous and surge
if not loads.empty:
    continuous_load = (loads["power_w"] * loads["qty"]).sum()
    surge_load = max(loads["surge_w"].max(), continuous_load)
else:
    continuous_load = 0.0
    surge_load = 0.0

inverter_continuous = ceil(continuous_load * 1.25)
inverter_surge = surge_load

# Charge controller sizing (for full)
if system_voltage > 0:
    controller_current = ceil((pv_watts_full / system_voltage) / 0.9)
else:
    controller_current = 0

# ---------------------------
# 4) Display results (UI)
# ---------------------------

st.header("📊 Results & Recommendations")

colA, colB = st.columns(2)

with colA:
    st.metric("Total Energy Needed", f"{E_total:.0f} Wh/day")
    st.metric("Critical Load Energy", f"{E_critical:.0f} Wh/day")
    st.write("### Loss & Efficiency Assumptions")
    st.write(f"- Inverter eff: {eta_inv:.2f}")
    st.write(f"- Battery round-trip eff: {eta_batt_roundtrip:.2f}")
    st.write(f"- PV derate (misc): {eta_misc:.2f}")
    st.write(f"- Safety margin: {safety_margin:.2f}")
    st.write("---")
    st.write("### Inverter & Controller Sizing")
    st.write(f"- Suggested inverter continuous: **{inverter_continuous} W**")
    st.write(f"- Surge capacity needed: **{inverter_surge} W**")
    st.write(f"- Charge controller current: **{controller_current} A** (for {system_voltage} V system)")

with colB:
    st.write("### Full Load System")
    st.write(f"- PV size required: **{pv_watts_full:.0f} W** → {num_panels_full} × {preferred_panel_w} W modules")
    st.write(f"- Battery needed: **{bat_ah_full:.1f} Ah** nominal → {num_batt_full} × {preferred_batt_ah} Ah modules")

    st.write("---")
    st.write("### Critical Load (Backup) System")
    st.write(f"- PV size (crit): **{pv_watts_crit:.0f} W** → {num_panels_crit} × {preferred_panel_w} W")
    st.write(f"- Battery (crit): **{bat_ah_crit:.1f} Ah** nominal → {num_batt_crit} × {preferred_batt_ah} Ah modules")

st.markdown("---")

# BOM Table
st.header("🧾 Bill of Materials (BOM) Summary")

bom = {
    "Item": [
        f"PV panels ({preferred_panel_w} W)",
        f"Battery modules ({preferred_batt_ah} Ah @ {system_voltage} V)",
        "MPPT Charge Controller",
        "Inverter (pure sine)",
        "Cables, Breakers, Mounting, Fuses"
    ],
    "Qty (Full)": [
        num_panels_full,
        num_batt_full,
        1,
        1,
        1
    ],
    "Qty (Critical)": [
        num_panels_crit,
        num_batt_crit,
        1,
        1,
        1
    ],
    "Notes": [
        "Check Voc, string arrangement",
        "Series/parallel per system voltage, include BMS for lithium",
        f"Must support >= {controller_current}A, check voltage window",
        f"Continuous ≥ {inverter_continuous}W, surge ≥ {inverter_surge}W",
        "Use correctly sized cables, DC breakers, fuses per local code"
    ]
}
bom_df = pd.DataFrame(bom)
st.dataframe(bom_df, use_container_width=True)

csv = bom_df.to_csv(index=False).encode("utf-8")
st.download_button("Download BOM CSV", data=csv, file_name="solar_bom_full.csv", mime="text/csv")

st.markdown("---")

# ---------------------------
# 5) PDF / Spec Sheet Export
# ---------------------------

def generate_pdf(loads_df, summary_text_lines, bom_df):
    class PDF(FPDF):
        def footer(self):
            # Move to 1.5 cm from bottom
            self.set_y(-15)
            self.set_font("Arial", "I", 9)
            self.set_text_color(100)
            # Footer text — personalized brand mark
            self.cell(
                0, 10,
                "Designed by OMOWAYE JOSHUA ⚡ | Empowering Energy Intelligence",
                align="C"
            )

    pdf = PDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Solar System Sizing Report", ln=True, align="C")
    pdf.ln(5)

    # Section 1: Appliance / Load List
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Appliance / Load List", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in loads_df.iterrows():
        crit = " (Critical)" if row.get("critical", False) else ""
        pdf.cell(0, 7, f"{row['name']}: {row['power_w']} W × {row['qty']} × {row['hours_per_day']} h {crit}", ln=True)

    pdf.ln(4)

    # Section 2: System Summary
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "System Summary", ln=True)
    pdf.set_font("Arial", "", 10)
    for line in summary_text_lines:
        pdf.cell(0, 7, line, ln=True)

    pdf.ln(4)

    # Section 3: Bill of Materials
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Bill of Materials (BOM)", ln=True)
    pdf.set_font("Arial", "", 10)
    for _, row in bom_df.iterrows():
        pdf.multi_cell(
            0, 7,
            f"{row['Item']}: Full qty = {row['Qty (Full)']}, "
            f"Critical qty = {row['Qty (Critical)']}. "
            f"Note: {row['Notes']}"
        )

    # ✅ Fixed return — compatible with FPDF2
    return bytes(pdf.output(dest="S"))



# Prepare summary lines
summary_lines = [
    f"System Voltage: {system_voltage} V",
    f"Battery Chemistry: {battery_chem}",
    f"Preferred Battery Module: {preferred_batt_ah} Ah",
    f"Preferred PV Module: {preferred_panel_w} W",
    f"Inverter continuous: {inverter_continuous} W, Surge: {inverter_surge} W",
    f"Controller current: {controller_current} A"
]

pdf_bytes = generate_pdf(loads, summary_lines, bom_df)
st.download_button("Download Spec Sheet (PDF)", data=pdf_bytes, file_name="solar_spec_full.pdf", mime="application/pdf")

st.success("✅ All done. Use the BOM table, tweak as needed, and hand the spec sheet to installers or vendors.")
