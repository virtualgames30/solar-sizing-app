import pandas as pd
import io
import matplotlib.pyplot as plt
from math import ceil

#Function to clean the text further before creating the PDF

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


# CALCULATION FUNCTIONS

# Function to compute required PV size ignoring losses:
def recommended_system(E_wh, ps_h, eta_inv, eta_batt, eta_misc, safety):
    E_from_panels = E_wh / (eta_inv * eta_batt)
    pv_watts = E_from_panels / (ps_h * eta_misc)
    pv_watts *= safety
    return E_from_panels, pv_watts

# Function for Battery sizing (nominal)
def battery_req(E_wh, autonomy, eta_batt, Vsys):
    wh = (E_wh * autonomy) / eta_batt
    ah = wh / Vsys
    return wh, ah
