# UK Crime Map Suite 🔍

This repository contains two Python-based tools designed to visualize street-level crime data across the UK. By leveraging the **Postcodes.io API** for geocoding and the **UK Police Data API**, these scripts provide a spatial breakdown of criminal activity around a specific location.

---

## 🛠️ The Tools

### 1. `crime_map_app.py` (The Interactive Web App)
A modern, high-performance dashboard built with **Streamlit**. This is designed for users who want a polished, interactive interface with real-time statistics.

* **Dark & Light Mode:** Toggleable themes with a custom CSS UI.
* **Live Metrics:** Dynamic calculation of total incidents, unique categories, and the most common crime in the area.
* **Visual Breakdown:** A sidebar severity key and a horizontal bar chart showing the percentage distribution of crimes.
* **Persistent State:** Uses `st.session_state` so you can toggle themes without losing your current map data.

### 2. `main.py` (The Lightweight CLI)
A straightforward Command Line Interface (CLI) script for generating standalone HTML map files.

* **Portable:** Generates a `complete_crime_map.html` file that can be opened in any browser or shared.
* **Fast:** Quick input-to-result workflow without the overhead of a web server.
* **Layer Control:** Includes a Folium Layer Control to toggle specific crime types on and off directly on the map.

---

## 📊 Features

* **Severity Mapping:** Crimes are color-coded from **Black** (Robbery) to **Lime Green** (Other Crime) to help identify high-severity areas at a glance.
* **Bounding Polygon Logic:** Uses a mathematical bounding box (calculated in miles) to fetch data precisely within the requested radius.
* **Interactive Markers:** Each crime is represented by a circle marker; clicking it reveals the street name and the month of occurrence.
* **Smart Geocoding:** Automatically converts any UK postcode into latitude and longitude coordinates.

---

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* The following libraries:
    ```bash
    pip install requests folium streamlit streamlit-folium
    ```

### Running the Web App
```bash
streamlit run crime_map_app.py
