Smart Solar System Sizing Calculator (Streamlit + Python)<!-- BADGES for a professional look -->⚡ Concept OverviewThe Smart Solar System Sizing Calculator is an intelligent, engineering-focused tool built with Python and Streamlit to help homeowners, engineers, and technicians design an optimal solar energy system. It accurately computes component requirements based on detailed load analysis and user preferences.The application enables users to input:A list of appliances (e.g., TV, fan, refrigerator) with their power rating (Watts) and usage duration (hours/day).A flag to designate whether each appliance is critical (essential for backup during power outages).System specifications like battery type (Lithium, Tubular, Lead Acid), preferred solar panel size (e.g., 400W), system voltage (12V, 24V, or 48V), and average sun hours per day.After computation, the system provides:Total daily energy consumption (Wh/day).Required PV (Photovoltaic) capacity (W) and number of panels.Suggested number and size of batteries (Ah).Recommended inverter rating (W).Charge controller capacity (A).A component summary and graphical visualization of energy usage.🧠 The Design Idea: An AI-like Sizing AssistantThe system functions as a transparent, AI-like solar design assistant, instantly showing how different choices affect the system sizing:Battery TypeKey Assumptions Used in CalculationLithiumHigh efficiency (≈ 95%) and deep discharge (DoD ≈ 90%).Lead-Acid/TubularStandard efficiency (≈ 80%) and conservative discharge (DoD ≈ 50%).The calculation engine also factors in Solar Panel Efficiency, a Derating Factor (to account for real-world losses), and Peak Sun Hours (PSH) for accurate sizing.🛠️ The Critical Load FeatureThe "Critical Flag" allows users to define essential devices that must operate during outages (like lights, routers, or medical devices).🎯 Daily Energy Consumption for Critical Loads ($E_{\text{critical}}$)When the flag is selected, the calculator filters these loads to perform a separate sizing calculation for a smaller "Critical Load (Backup) System."The calculation logic uses pandas to filter and sum only the required energy:E_critical = loads.loc[loads["critical"], "energy_wh"].sum()
This resulting variable, $E_{\text{critical}}$, represents the total daily energy (Wh/day) required for backup-essential devices. By definition, $E_{\text{critical}} \leq E_{\text{total}}$.What the Critical Flag Does Not AffectFull System Sizing: The main system sizing is based on $E_{\text{total}}$ (the sum of all loads).Inverter Sizing: The inverter rating is determined by the total instantaneous wattage and startup surge and must always handle the potential maximum total load.The feature provides a secondary, smaller, and more cost-effective system design specifically for powering essential items during outages.📋 Step-by-Step Functionality1. User Input and Data CollectionUsers populate a dynamic table with appliance details and select system parameters via Streamlit widgets.2. Computation EngineThe system uses fundamental solar engineering equations for deterministic and transparent results.1. Daily Energy Consumption (Wh) $$\text{E}_{\text{Total}} = \sum(\text{Power} \times \text{Hours})$$
*(Description: Total energy used per day by all appliances.)*

**2. Required Battery Capacity (Ah)** $$
\text{Ah}_{\text{Req}} = \frac{\text{E}_{\text{Total}} \times \text{Autonomy Days}}{\text{V}_{\text{System}} \times \text{DoD} \times \eta_{\text{Battery}}}
$$*(Description: Determines the total storage requirement based on voltage, depth of discharge, and battery efficiency.)*

**3. Required Solar Panel Power (W)** $$
\text{PV}*{\text{Req}} = \frac{\text{E}*{\text{Total}}}{\text{PSH} \times \eta\_{\text{Panel}} \times \text{Derating Factor}} \times \text{Safety Factor}

$$*(Description: Calculates the required panel array size considering sun hours and system losses.)*

**4. Inverter Size (W)** $$
\text{Inverter}*{\text{Size}} = 1.3 \times \text{P}*{\text{Max Load}}
$$*(Description: Adds a 30% safety margin to the maximum instantaneous load for startup surges.)*

**Key Abbreviations:**

| **Abbreviation** | **Meaning** |
| :--- | :--- |
| **Wh** | Watt-hour |
| **Ah** | Amp-hour |
| **DoD** | Depth of Discharge |
| **PV** | Photovoltaic (solar panel system) |
| **PSH** | Peak Sun Hours |

### 3\. Visualization

A **horizontal bar chart** is generated to display the **top 5 appliances** with the highest daily energy consumption (Wh/day). This visualization aids users in quickly identifying major energy consumers and potential areas for energy optimization.

### 4\. Recommendations & BOM Generation

The system outputs a detailed Bill of Materials (BOM) summary for both the Full System and the Critical Load System:

| **Component** | **Suggested Specification** | **Quantity** |
| :--- | :--- | :--- |
| Solar Panel | 400W Monocrystalline | 5 |
| Battery | 200Ah Lithium | 2 |
| Inverter | 3.5 kVA | 1 |
| Charge Controller | 60A MPPT | 1 |

## 📐 Technical Architecture

| **Layer** | **Purpose** | **Tools** |
| :--- | :--- | :--- |
| **Frontend/UI** | Interactive input forms and visualization | Streamlit |
| **Computation Logic** | Load analysis and system sizing | Python, pandas |
| **Visualization** | Energy consumption plots | Matplotlib |
| **PDF Report** | PDF summary and BOM generation | FPDF |
| **Future Add-ons** | AI-based cost optimization | OpenAI / ML Integration |

## 🚀 Get Started

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/virtualgames30/solar-sizing-app.git](https://github.com/virtualgames30/solar-sizing-app.git)
    cd solar-sizing-app
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**

    ```bash
    streamlit run streamlit_app.py
    ```$$