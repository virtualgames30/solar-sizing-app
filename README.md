
---

````markdown
# Smart Solar System Sizing Calculator (Streamlit + Python)

---

## Concept Overview

The **Smart Solar System Sizing Calculator** is an intelligent tool built with **Python and Streamlit** to help homeowners, engineers, and technicians design an optimal solar energy system based on their appliance load requirements and preferences.  

It enables users to input:

- A list of appliances (e.g., TV, fan, refrigerator, laptop)
- The **power rating (Watts)** and **usage duration (hours/day)** of each appliance  
- Whether each appliance is **critical** (i.e., essential for backup during power outages)  
- The **battery type** (Lithium, Tubular, Lead Acid, etc.)  
- The **preferred solar panel size** (e.g., 300W, 400W, 550W)  
- The **system voltage** (12V, 24V, or 48V)  
- The **average sun hours per day**

After submission, the calculator performs a full energy audit and sizing computation to recommend:

1. Total daily energy consumption (Wh/day)
2. Required solar panel capacity (W)
3. Suggested number and size of batteries
4. Recommended inverter rating (W)
5. Charge controller capacity (A)
6. Component summary and graphical visualization of energy usage per load

---

## The Design Idea

The system functions as an **AI-like solar design assistant**. It shows how different design choices affect system sizing.  

For instance:

- If you mark a load as **non-critical**, it’s excluded from backup sizing.  
- If you select **Lithium** batteries, the tool assumes:
  - Higher efficiency ≈ 95%
  - Deeper discharge (DoD ≈ 90%)
- If you choose **Lead-Acid**, it assumes:
  - DoD ≈ 50%
  - Efficiency ≈ 80%

It also factors in:
- Solar panel efficiency
- Derating factor (to account for losses)
- Sunlight hours (PSH – Peak Sun Hours)

---

## Impact of Ticking a Load as “Critical”

The Critical Flag allows users to identify essential devices that must remain operational during outages or backup operation (e.g., lights, routers).
When selected, the calculator filters these loads and performs a separate sizing calculation for a smaller “Critical Load (Backup) System".

### Daily Energy Consumption for Critical Loads (E₍critical₎)
- **How it works:**  
  The calculator filters loads using  
  ```python
  E_critical = loads.loc[loads["critical"], "energy_wh"].sum()
````

This sums only the energy (Wh/day) of appliances marked as *critical = True*.

* **Impact:**
  This creates the variable **E₍critical₎**, representing the total daily energy required for backup-essential devices.
  By definition, **E₍critical₎ ≤ E₍total₎**.

### What It Does *Not* Affect

* **Full System Sizing:** Based solely on E₍total₎ (sum of all loads).
* **Inverter Sizing:** Determined by total instantaneous wattage and startup surge — unaffected by critical flags. The inverter must always handle the maximum total load, regardless of critical status, since all appliances could potentially be used at once.
* **Charge Controller:** Sized based on full PV capacity (PV₍full₎).

**In summary:**
The feature provides a secondary, typically smaller, and more cost-effective system design for powering essential items (lights, routers, fans, etc.) during outages.

---

## Step-by-Step Functionality

### 1. User Input

* Add appliances (name, wattage, hours/day, and critical load toggle)
* Choose:

  * Battery type
  * Solar panel size
  * System voltage
  * Sun hours/day

### 2. Computation Engine

Uses fundamental solar engineering equations:

| Formula                                                                                                 | Description                              |
| ------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| **Daily Energy Consumption (Wh)** = Σ(Power × Hours)                                                    | Total energy used per day                |
| **Required Battery Capacity (Ah)** = Total Load (Wh) / (System Voltage × DoD × Efficiency)              | Determines storage requirement           |
| **Number of Batteries** = Required Capacity (Ah) / Selected Battery Rating (Ah)                         | Calculates how many batteries are needed |
| **Required Solar Panel Power (W)** = Total Load (Wh) / (Sun Hours × Panel Efficiency × Derating Factor) | Calculates panel size                    |
| **Inverter Size (W)** = 1.3 × Total Load (W)                                                            | Adds 30% safety margin for surges        |

**Abbreviations Used:**

* **Wh** – Watt-hour
* **Ah** – Amp-hour
* **DoD** – Depth of Discharge
* **PV** – Photovoltaic (solar panel system)
* **PSH** – Peak Sun Hours

### 3. Visualization

A **horizontal bar chart** displays the **top 5 appliances** with the highest daily energy consumption (Wh/day).
This helps users quickly identify which appliances contribute most to total energy demand and where energy savings or optimization may be achieved.

### 4. Recommendations

After computing, the system displays:

| Component         | Suggested Specification | Quantity |
| ----------------- | ----------------------- | -------- |
| Solar Panel       | 400W Monocrystalline    | 5        |
| Battery           | 200Ah Lithium           | 2        |
| Inverter          | 3.5 kVA                 | 1        |
| Charge Controller | 60A MPPT                | 1        |

---

## Technical Architecture

| Layer                  | Purpose                                   | Tools                   |
| ---------------------- | ----------------------------------------- | ----------------------- |
| **Frontend/UI**        | Interactive input forms and visualization | Streamlit               |
| **Computation Logic**  | Load analysis and system sizing           | Python, pandas          |
| **Data Handling**      | Appliance and spec data                   | CSV/JSON                |
| **Visualization**      | Energy consumption plots                  | Matplotlib              |
| **PDF Report**         | PDF summary generation                    | FPDF                    |
| **Future Add-ons**     | AI-based cost optimization                | OpenAI / ML Integration |

---

## Summary

The **Smart Solar System Sizing Calculator** is a transparent, educational, and practical tool that transforms traditional manual solar sizing into an automated visually interactive experience.

It empowers users to:

* Understand their daily energy profile
* Compare full-load vs critical-load systems
* Visualize top energy-consuming appliances

---

````
