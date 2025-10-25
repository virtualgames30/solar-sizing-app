import streamlit as st
import pandas as pd
import numpy as np
import math
from math import ceil
from fpdf import FPDF
import io
import matplotlib.pyplot as plt

# ---------------------------
# 0) UTILITY FUNCTIONS (Defined first to prevent "is not defined" errors)
# ---------------------------

def sanitize_text(text):
    """
    Replace unsupported Unicode symbols with ASCII equivalents
    so fpdf (which uses Latin-1) can encode them safely, and handle NaN/None.
    """
    if pd.isna(text) or text is None:
        # Ensure no None/NaN reaches fpdf, replace with an empty string
        return ""
    if not isinstance(text, str):
        text = str(text)
        
    replacements = {
        "≥": ">=",
        "≤": "<=",
        "°": " deg",
        "Ω": " ohm",
        "µ": "u",
        "×": "x",
        "–": "-",  
        "—": "-", 
        "✔": "[OK]",
        "✘": "[X]",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

# FUNCTION TO CREATE THE CHART
def create_and_save_chart(loads_df):
    """
    Creates a horizontal bar chart of the top 5 energy consumers
    """
    # 1. Filter and sort the data for charting. Ensure energy_wh is numeric and greater than zero
    chart_data = loads_df.copy()
    chart_data['energy_wh'] = pd.to_numeric(chart_data['energy_wh'], errors='coerce').fillna(0)
    
    chart_data = chart_data[chart_data['energy_wh'] > 0].sort_values(
        by='energy_wh', ascending=False
    ).head(5)

    if chart_data.empty:
        return None 

    # 2. Create the Matplotlib figure
    fig, ax = plt.subplots(figsize=(8, 5))
    
    # Use log scale if numbers are extremely disparate
    if chart_data['energy_wh'].min() > 0 and chart_data['energy_wh'].max() / chart_data['energy_wh'].min() > 100:
        ax.barh(chart_data['name'], chart_data['energy_wh'], color='#1E88E5', log=True)
        ax.set_xlabel('Daily Energy Consumption (Wh) [Log Scale]', fontsize=12)
    else:
        ax.barh(chart_data['name'], chart_data['energy_wh'], color='#1E88E5')
        ax.set_xlabel('Daily Energy Consumption (Wh)', fontsize=12)
        
    ax.set_title('Top 5 Energy Consuming Appliances', fontsize=14, fontweight='bold')
    ax.invert_yaxis()

    # Customize appearance
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    # 3. Save to in-memory buffer as JPEG
    img_buffer = io.BytesIO()
    fig.savefig(img_buffer, format='jpeg', bbox_inches='tight', dpi=150) 
    plt.close(fig)
    img_buffer.seek(0)
    
    return img_buffer.getvalue()

# ---------------------------
# Page setup
# ---------------------------
st.set_page_config(page_title="Solar System Sizing + Critical Load", layout="wide")
st.title("🔆 Solar System Sizing Calculator (Full + Critical Load)")


st.info(
    "⚠️ **Disclaimer:** This tool provides a professional estimate and all calculations are for planning purposes only. "
    "A **certified professional** must perform an on-site evaluation to ensure your final solar system design is safe, efficient, and compliant with all local regulations."
) 

st.markdown("------")

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

# Prepare Editable Table
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
# 3) Computation logic (MODIFIED CLEANUP)
# ---------------------------

# Copy loads for computation
loads = st.session_state.appliances.copy()

# Fix 1: Ensure 'name' is a string and handle nulls for Matplotlib/PDF
loads["name"] = loads["name"].astype(str).replace(
    {"None": "Unnamed Appliance", "nan": "Unnamed Appliance", "": "Unnamed Appliance"}
)

# Fix 2: Ensure all numerical columns are properly typed (not None/NaN).
numeric_cols = ["power_w", "qty", "hours_per_day", "surge_w"]
for col in numeric_cols:
    loads[col] = pd.to_numeric(loads[col], errors='coerce').fillna(0.0)

# Compute energies
if not loads.empty:
    loads["energy_wh"] = loads["power_w"] * loads["qty"] * loads["hours_per_day"]
else:
    loads["energy_wh"] = 0.0

E_total = loads["energy_wh"].sum()
# Ensure the 'critical' column is boolean and has no NaN values
if "critical" in loads.columns:
    loads["critical"] = loads["critical"].fillna(False)
    # If user entered strings like "Yes"/"No" or "True"/"False"
    loads["critical"] = loads["critical"].astype(str).str.lower().map({
        'true': True, 'yes': True, '1': True,
        'false': False, 'no': False, '0': False 
    }).fillna(False)
else:
    loads["critical"] = False  # fallback if column missing

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
    # The cleanup above ensures 'surge_w', 'power_w', and 'qty' are numbers
    loads['net_surge'] = loads.apply(
        lambda row: max(0, row['surge_w'] - (row['power_w'] * row['qty'])), axis=1
    )
    max_net_surge = loads['net_surge'].max()
    
    # Required surge capacity = Total Continuous Load + Max Net Surge from a single device
    # We use inverter_surge here directly
    inverter_surge = ceil(continuous_load + max_net_surge)
else:
    continuous_load = 0.0
    # Set inverter_surge to 0.0 directly when no loads exist
    inverter_surge = 0.0 

inverter_continuous = ceil(continuous_load * 1.25)

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
        "Inverter (pure sinewave)",
        "Cables, Breakers,Fuses"
    ],
    "Qty (Full)": [
        num_panels_full,
        num_batt_full,
        1,
        1,
        '- '
    ],
    "Qty (Critical)": [
        num_panels_crit,
        num_batt_crit,
        1,
        1,
        '- '
    ],
    "Notes": [
        "Verify Voc (Open Circuit Voltage) and optimize string configuration.",
        "Configure series/parallel groups to match system voltage. A dedicated Battery Management System (BMS) is mandatory for Li-ion/LiFePO4.",
        f"MPPT current rating must be > {controller_current}A. Verify maximum array Voc is within the controller's input voltage window.",
        f"Inverter continuous power rating must be > {inverter_continuous}W. Required surge capacity: {inverter_surge}W.",
        "Use correctly sized cables, DC breakers, fuses per local code"
    ]
}
bom_df = pd.DataFrame(bom)
st.dataframe(
    bom_df,
    use_container_width=True,
    height=450, # Set height to give space for wrapped text
    row_height=80,
    column_config={
        "Notes": st.column_config.Column(
            "Notes",
            # Set the desired width (e.g., 200 pixels or use 'auto')
            width=200, 
            # Make the text visible without truncation
            help="Technical specifications and installation checks.")
    }
)


# Apply the sanitizer to the relevant columns of the BOM DataFrame before export
bom_df_sanitized = bom_df.copy()
bom_df_sanitized['Item'] = bom_df_sanitized['Item'].apply(sanitize_text)
bom_df_sanitized['Notes'] = bom_df_sanitized['Notes'].apply(sanitize_text)
csv = bom_df_sanitized.to_csv(index=False).encode("utf-8")
st.download_button("Download BOM CSV", data=csv, file_name="solar_bom_full.csv", mime="text/csv")

st.markdown("---")


# ---------------------------
# 5) PDF / Spec Sheet Export
# ---------------------------

# --- CHART GENERATION AND DISPLAY TOGGLE ---
chart_image_bytes = create_and_save_chart(loads)

st.subheader("PDF Generation & Graphical Summary")

show_chart = st.checkbox("Show/Hide Graphical Summary (Top 5 Loads)", value=True, help="Toggle the bar chart visualization.")
if show_chart:
    if chart_image_bytes:
        st.image(chart_image_bytes, caption="Top Energy Consuming Appliances (Wh/day)")
    else:
        st.info("No sufficient load data available to generate the energy consumption chart.")

st.markdown("---")


# --- PDF generator function ---
def generate_pdf(loads_df, summary_lines, bom_df, chart_image_bytes): 
    """
    Generate a PDF summary report including the chart image of Energy Consumption Appliances.
    """

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Smart Solar System Sizing Report", ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, "", ln=True) # Blank line

    # --- CHART EMBEDDING SECTION ---
    if chart_image_bytes:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Load Consumption Chart:", ln=True)
        pdf.cell(0, 5, "", ln=True)
        
        # Prepare BytesIO object for fpdf.image
        img_io = io.BytesIO(chart_image_bytes)
        
        # image placement and size (140mm width, centered)
        image_w = 140
        x_center = (pdf.w - image_w) / 2
        
        # Image type is explicitly set to JPEG for clarity.
        pdf.image(img_io, x=x_center, w=image_w, type='JPEG')
        pdf.cell(0, 5, "", ln=True) # Spacer after image
        pdf.cell(0, 5, "", ln=True) 
    
    # --- SUMMARY SECTION ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "System Summary:", ln=True) 
    
    pdf.set_font("Arial", "", 12)
    
    for line in summary_lines:
        pdf.cell(0, 8, sanitize_text(line), ln=True) 

    pdf.cell(0, 10, "", ln=True)

    # --- LOAD TABLE SECTION ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Appliance Load Summary:", ln=True)
    pdf.set_font("Arial", "B", 11)
    
    # Table Header
    pdf.cell(60, 8, "Appliance", 1)
    pdf.cell(25, 8, "Power (W)", 1)
    pdf.cell(20, 8, "Qty", 1)
    pdf.cell(30, 8, "Hours/day", 1)
    pdf.cell(30, 8, "Energy (Wh)", 1)
    pdf.cell(25, 8, "Critical", 1, ln=True)

    pdf.set_font("Arial", "", 11)
    for _, row in loads_df.iterrows():
        pdf.cell(60, 8, sanitize_text(row.get("name", "")), 1)
        pdf.cell(25, 8, sanitize_text(f"{row.get('power_w', 0.0):.1f}"), 1) 
        pdf.cell(20, 8, sanitize_text(str(int(row.get('qty', 0)))), 1)        
        pdf.cell(30, 8, sanitize_text(f"{row.get('hours_per_day', 0.0):.1f}"), 1) 
        pdf.cell(30, 8, sanitize_text(f"{round(row.get('energy_wh', 0), 0):.0f}"), 1) 
        pdf.cell(25, 8, sanitize_text(str(row.get("critical", ""))), 1, ln=True)

    pdf.cell(0, 10, "", ln=True)

    # --- Bill of Materials (BOM) Section ---
    if bom_df is not None and not bom_df.empty:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Recommended Bill of Materials:", ln=True)
        pdf.set_font("Arial", "B", 11)
        
        # Define column widths 
        w_item, w_qty_f, w_qty_c, w_notes = 60, 25, 30, 75
        
        # Draw the header row
        pdf.cell(w_item, 8, "Item", 1)
        pdf.cell(w_qty_f, 8, "Qty (Full)", 1)
        pdf.cell(w_qty_c, 8, "Qty (Critical)", 1)
        pdf.cell(w_notes, 8, "Notes", 1, ln=True)

        pdf.set_font("Arial", "", 11)
        
        x_start = pdf.l_margin
        
        for _, row in bom_df.iterrows():
            notes_text = sanitize_text(row.get("Notes", ""))
            
            y_start = pdf.get_y()
            
            # calculate required height in the notes column
            pdf.set_xy(x_start + w_item + w_qty_f + w_qty_c, y_start) 
            pdf.multi_cell(w_notes, 4, notes_text, 0, 'L') 
            cell_height = pdf.get_y() - y_start
            cell_height = max(8, cell_height) 
            
            # Draw cells 1-3
            pdf.set_xy(x_start, y_start) 
            pdf.cell(w_item, cell_height, sanitize_text(row.get("Item", "")), 1)
            pdf.cell(w_qty_f, cell_height, sanitize_text(str(row.get("Qty (Full)", ""))), 1)
            pdf.cell(w_qty_c, cell_height, sanitize_text(str(row.get("Qty (Critical)", ""))), 1)
            
            # Draw multi-line notes cell
            pdf.set_xy(pdf.get_x(), y_start)
            pdf.multi_cell(w_notes, 4, notes_text, 1, 'L', False)
            
            # Advance to the start of the next row
            pdf.set_xy(x_start, y_start + cell_height) 


    # --- Output as bytes (safe for all FPDF versions) ---
    pdf_result = pdf.output(dest="S")

    if isinstance(pdf_result, str):
        pdf_bytes = pdf_result.encode("latin-1")
    else:
        pdf_bytes = bytes(pdf_result)

    return pdf_bytes


# PREPARE SUMMARY LINES
summary_lines = [
    f"System Voltage: {system_voltage} V",
    f"Battery Chemistry: {battery_chem}",
    f"Preferred Battery Module: {preferred_batt_ah} Ah",
    f"Preferred PV Module: {preferred_panel_w} W",
    f"Inverter continuous: {inverter_continuous} W, Surge: {inverter_surge} W",
    f"Charge Controller current: {controller_current} A"
]


pdf_bytes = generate_pdf(loads, summary_lines, bom_df, chart_image_bytes)
st.download_button("Download Spec Sheet (PDF)", data=pdf_bytes, file_name="solar_spec_full.pdf", mime="application/pdf")

st.success("✅ All done. Use the BOM table, tweak as needed, and hand the spec sheet to installers or vendors.")
