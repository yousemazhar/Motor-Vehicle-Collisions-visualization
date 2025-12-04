


##  Project Overview

This project is part of **Data Engineering & Visualization – Milestone 1**.
We built an **interactive analytical dashboard** for *NYC Motor Vehicle Collisions* using:
ML project : https://github.com/yousemazhar/DataOrbit-Fraud-Detection.git
* **Python**
* **Gradio**
* **Plotly**
* **Pandas**
* **Integrated Crash + Person datasets**
* **Natural-Language Smart Search**
* **Dynamic visual reports (9 charts + summary)**

The dashboard supports **real-time filtering**, **trend analysis**, **heatmaps**, **distribution visualizations**, and **geospatial mapping** with a responsive UI deployed on **Hugging Face Spaces**.

---

##  Live Demo (Hugging Face Space)


 **https://huggingface.co/spaces/DataVizSem5/Motor-Vehicle-Collisions-visualization**

---

#  Project Structure

```
├── app.py                     # Main Gradio application
├── nyc_crashes_integrated_clean.parquet   # Cleaned, integrated dataset
├── requirements.txt           # Python dependencies
├── README.md                  # Documentation (this file)
└── assets/                    # (Optional) any helper scripts or images
```

---

#  Data Engineering Summary 

## **1. Data Sources**

We used the official NYC Open Data resources:

* **Crashes dataset**
  [https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95)
* **Person dataset**
  [https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Person/f55k-p6yu](https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Person/f55k-p6yu)

Integrated using **COLLISION_ID**.

---

## **2. Pre-Integration Cleaning**

Cleaning steps completed before joining:

### **✔ Handling missing values**

* Dropped unusable rows (missing primary identifiers)
* Imputed minor categorical noise using consistent labels (e.g., vehicle types)
* Converted date and time fields into:

    * `CRASH_YEAR`
    * `CRASH_MONTH`
    * `CRASH_DAYOFWEEK`
    * `CRASH_HOUR`

### **✔ Removing outliers**

* Removed invalid coordinates (lat < 40 or lat > 41)
* Removed invalid ages and impossible numeric values

### **✔ Standardization**

* Uniform case normalization (vehicle types, person types, borough names)
* Standard date formatting

---

## **3. Integration Step**

**Joined Crash + Person datasets** using `COLLISION_ID`.

### After join, performed:

* Removal of duplicate joined records
* Consistency checks between injury fields
* Standardization of categorical values
* Clean-up of redundant columns

Final integrated dataset saved as:

`nyc_crashes_integrated_clean.parquet`

---

## **📊 Visualizations Included**

The dashboard generates **9 interactive charts**:

1. Trend analysis (line chart)
2. Person type distribution (pie)
3. Categorical analysis (bar)
4. Time distribution (bar)
5. Contributing factor analysis – vehicle 1
6. Contributing factor analysis – vehicle 2
7. Injury & fatality rate comparison
8. Day × hour heatmap
9. Geographic crash map

Plus a full **summary statistics section** and **insights under every visualization**.

---

# Smart Search Capability

The app supports **natural-language queries**, such as:

* “Brooklyn 2022 pedestrian crashes”
* “Manhattan weekend taxi injuries”
* “Queens Friday night motorcycle fatalities”

The smart parser automatically detects:

* Borough
* Year
* Month
* Day of week
* Time of day
* Vehicle type
* Person type
* Severity
* Gender

---

#  Local Setup Instructions

### **1. Clone the repository**

```bash
git clone https://github.com/yousemazhar/Motor-Vehicle-Collisions-visualization.git
cd https://github.com/yousemazhar/Motor-Vehicle-Collisions-visualization.git
```

### **2. Create virtual environment (optional but recommended)**

```bash
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### **3. Install dependencies**

```bash
pip install -r requirements.txt
```

### **4. Run the app locally**

```bash
python app.py
```

The dashboard opens automatically at:
 **[http://127.0.0.1:7860](http://127.0.0.1:7860)**

---

#  Deployment Instructions , Hugging Face Spaces

Deploying to HF Spaces is easy and requires only:

* `app.py`
* `requirements.txt`
* the dataset (`.parquet`)

### **1. Create a New Space**

Go to:
[https://huggingface.co/spaces](https://huggingface.co/spaces)

Choose:

* **Space type:** Gradio
* **Hardware:** CPU
* **Visibility:** Public (or Private)

### **2. Upload the project files**

Upload:

```
app.py
nyc_crashes_integrated_clean.parquet
requirements.txt
```

Your `requirements.txt` should include at minimum:

```
gradio
pandas
plotly
numpy
pyarrow
```

### **3. Commit and wait for the build**

Hugging Face automatically:

* installs dependencies
* runs `app.py`
* launches your Space

### **4. Access the Live App**

It will appear at:

```
https://huggingface.co/spaces/<username>/<space-name>
```

---

#  Testing After Deployment

Verify that:

✔ UI loads correctly
✔ “Smart Search” auto-fills filters
✔ “Generate Report” renders all charts
✔ Map loads correctly
✔ Reset button restores all defaults
✔ Performance is stable with filters

---
Here is your **clean, professional, submission-ready Contribution Documentation section** that fits perfectly into the README and clearly reflects everyone’s work **while referencing the project description requirements** (Milestone 1).
You can paste this directly under the “Contribution Documentation” section.

---

#  Contribution Documentation

This project was completed by a team of five members: **Yousef, Jana, Lakshy, Engy, and Ziad**.
According to the Milestone 1 project description (Data Engineering & Visualization, WS2025), each member contributed to the core areas: **Research Questions**, **Data Cleaning**, **Integration**, and **Interactive Website Development**.

Below is a clear summary of each member’s primary responsibilities, while acknowledging that the entire team collaborated across all tasks.

---

##  Individual Contributions

### **🧑‍💻 Yousef**

* Co-developed the full interactive dashboard using **Gradio + Plotly**
* Implemented the **Generate Report pipeline** (filters, charts, insights)
* Integrated **Smart Search** into the UI
* Helped in debugging filtering logic and UI layout
* Contributed to dataset validation and cleaning decisions

---

### **🧑‍💻 Jana**

* Co-developed UI components and layout using **Gradio Blocks**
* Worked on **visualization refinement** (color schemes, readability, labels)
* Assisted with **synchronizing dropdowns and filters**
* Participated in preparing the **final deployed version**
* Supported documentation and project structuring

---

### **🧑‍💻 Lakshy**

* Major contributor to **front-end interactions** and responsive layout
* Helped implement **chart settings panel**, dropdown logic, and plot organization
* Performed the **Hugging Face deployment** setup
* Contributed to the deployment process on **Hugging Face Spaces**
* Assisted with error handling and resolving UI inconsistencies

---

### **🧑‍🎓 Engy**

* Led the creation of **research questions** as required by the Milestone (per-member requirement)
* Validated questions against the data availability and project goals
* Contributed to EDA and ensured questions aligned with generated insights
* Assisted in documenting cleaning and integration choices

---

### **🧑‍🔬 Ziad**

* Led **data processing, cleaning, and integration**, including:

    * Handling missing values
    * Outlier detection
    * Standardizing temporal fields
    * Merging Crashes + Person datasets using `COLLISION_ID`
* Ensured the final cleaned dataset met all requirements specified by the project
* Supported the team by preparing the enriched dataset used by the dashboard

---

##  Team-Wide Collaboration

While each member held certain responsibilities, **the entire team contributed to all parts of the project** including:

* Exploring the dataset (EDA)
* Deciding how to clean and prepare the data
* Designing the final dashboard layout
* Testing filters, charts, and smart search
* Documenting process and ensuring requirements were met

This collaborative workflow aligns fully with the **Milestone 1 project description**, which requires students to:

* Explore, clean, and integrate datasets
* Develop an interactive visualization website
* Produce research questions and document cleaning decisions
* Deploy the final product

---
