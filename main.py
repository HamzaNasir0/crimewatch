import requests
import folium
import webbrowser
import os
import math

def get_coords(postcode):
    url = f"https://api.postcodes.io/postcodes/{postcode}"
    res = requests.get(url).json()
    return (res['result']['latitude'], res['result']['longitude']) if res['status'] == 200 else (None, None)

def get_crime_style(category):
    # Comprehensive mapping of all Police API categories to your severity ranking
    crime_map = {
        'robbery': ('#000000', 'Robbery'),                       # Black (Worst)
        'possession-of-weapons': ('#8B0000', 'Weapons'),        # Dark Red
        'violence-and-sexual-offences': ('#FF0000', 'Violent'), # Red
        'criminal-damage-arson': ('#FF4500', 'Arson/Damage'),   # Orange-Red
        'burglary': ('#FF8C00', 'Burglary'),                    # Dark Orange
        'vehicle-crime': ('#FFA500', 'Vehicle Crime'),          # Orange
        'drugs': ('#FFD700', 'Drugs'),                          # Gold
        'theft-from-the-person': ('#EEEE00', 'Theft Person'),   # Neon Yellow
        'shoplifting': ('#FFFF00', 'Shoplifting'),              # Yellow
        'other-theft': ('#DA70D6', 'Other Theft'),              # Orchid/Purple
        'bicycle-theft': ('#D8BFD8', 'Bicycle Theft'),          # Thistle/Light Purple
        'public-order': ('#ADFF2F', 'Public Order'),            # Green-Yellow
        'anti-social-behaviour': ('#90EE90', 'ASB'),            # Light Green
        'other-crime': ('#00FF00', 'Other Crime'),              # Lime Green (Least)
    }
    return crime_map.get(category, ('#808080', 'Unknown'))

def get_bounding_poly(lat, lng, miles):
    lat_change = miles / 69.0
    lng_change = miles / (69.0 * math.cos(math.radians(lat)))
    n = f"{lat + lat_change},{lng}"
    s = f"{lat - lat_change},{lng}"
    e = f"{lat},{lng + lng_change}"
    w = f"{lat},{lng - lng_change}"
    return f"{n}:{e}:{s}:{w}"

def create_crime_map(postcode, radius_miles=2):
    lat, lng = get_coords(postcode)
    if not lat:
        print("Invalid postcode.")
        return

    poly = get_bounding_poly(lat, lng, radius_miles)
    police_url = "https://data.police.uk/api/crimes-street/all-crime"
    
    print(f"Fetching full crime data for {radius_miles} mile(s) around {postcode}...")
    response = requests.get(police_url, params={'poly': poly})
    
    if response.status_code != 200:
        print("Error: Radius too large or API unavailable. Try 1 or 2 miles.")
        return
        
    crimes = response.json()
    m = folium.Map(location=[lat, lng], zoom_start=14, tiles="cartodbpositron")

    layers = {}
    for crime in crimes:
        c_lat, c_lng = float(crime['location']['latitude']), float(crime['location']['longitude'])
        cat_id = crime['category']
        color, label = get_crime_style(cat_id)
        display_name = cat_id.replace('-', ' ').title()
        
        if display_name not in layers:
            layers[display_name] = folium.FeatureGroup(name=display_name)

        popup_content = f"""
        <div style="font-family: Arial; width: 180px;">
            <b style="color:{color};">{display_name}</b><br>
            <small>{crime.get('month', '')}</small><br>
            <hr style="margin:5px 0;">
            {crime['location']['street']['name']}
        </div>
        """
        
        folium.CircleMarker(
            location=[c_lat, c_lng],
            radius=7,
            popup=folium.Popup(popup_content, max_width=250),
            color=color,
            fill=True,
            fill_opacity=0.7,
            weight=1
        ).add_to(layers[display_name])

    for layer in sorted(layers.keys()):
        layers[layer].add_to(m)

    legend_html = '''
     <div style="position: fixed; bottom: 30px; left: 30px; width: 200px; 
     background-color: white; border:2px solid grey; z-index:9999; font-size:11px;
     padding: 10px; border-radius: 5px; line-height: 1.4; max-height: 400px; overflow-y: auto;">
     <b>Severity Key</b><br>
     <i class="fa fa-circle" style="color:#000000"></i> Robbery<br>
     <i class="fa fa-circle" style="color:#8B0000"></i> Weapons<br>
     <i class="fa fa-circle" style="color:#FF0000"></i> Violent Crime<br>
     <i class="fa fa-circle" style="color:#FF4500"></i> Arson / Damage<br>
     <i class="fa fa-circle" style="color:#FF8C00"></i> Burglary<br>
     <i class="fa fa-circle" style="color:#FFA500"></i> Vehicle Crime<br>
     <i class="fa fa-circle" style="color:#FFD700"></i> Drugs<br>
     <i class="fa fa-circle" style="color:#EEEE00"></i> Theft From Person<br>
     <i class="fa fa-circle" style="color:#FFFF00"></i> Shoplifting<br>
     <i class="fa fa-circle" style="color:#DA70D6"></i> Other Theft<br>
     <i class="fa fa-circle" style="color:#D8BFD8"></i> Bicycle Theft<br>
     <i class="fa fa-circle" style="color:#ADFF2F"></i> Public Order<br>
     <i class="fa fa-circle" style="color:#90EE90"></i> ASB<br>
     <i class="fa fa-circle" style="color:#00FF00"></i> Other Crime<br>
     </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

    folium.LayerControl(collapsed=True).add_to(m)
    folium.Marker([lat, lng], icon=folium.Icon(color='blue', icon='home')).add_to(m)

    file_path = "complete_crime_map.html"
    m.save(file_path)
    webbrowser.open('file://' + os.path.realpath(file_path))
    print(f"Map generated! Found {len(crimes)} total crime reports.")

if __name__ == "__main__":
    pc = input("Enter UK Postcode (e.g. SW1A 1AA, SW1A 0AA, SE1 7PB etc): ").strip()
    rad = input("Enter search radius in miles (1, 2, or 3): ").strip()
    create_crime_map(pc, float(rad))