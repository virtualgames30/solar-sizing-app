import io
from fpdf import FPDF
import pandas as pd

# Import the sanitizer function from the utils file
from utils import sanitize_text

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
