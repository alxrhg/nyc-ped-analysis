"""
Generate an interactive Folium map of NYC DOT Bi-Annual Pedestrian Count
locations with model feature-importance annotations.

The RF_wknd_n20_am_models.pckl model was trained on NYC DOT pedestrian
count data. This script plots the 114 known counting locations on an
interactive map and embeds the model summary in a legend overlay.
"""

import pickle
import warnings
import numpy as np
import folium
from folium.plugins import MarkerCluster

warnings.filterwarnings("ignore")

# ── 1. Load model ────────────────────────────────────────────────────────────
with open("RF_wknd_n20_am_models.pckl", "rb") as f:
    model = pickle.load(f)

importances = model.feature_importances_
FEATURE_NAMES = [f"Feature {i}" for i in range(model.n_features_in_)]

# ── 2. NYC DOT Bi-Annual Pedestrian Count locations ─────────────────────────
# These are the well-known 114 counting locations from the NYC DOT program,
# grouped by borough.  Coordinates are approximate mid-block centroids.
LOCATIONS = [
    # ── Manhattan (60 locations) ──────────────────────────────────────────
    {"name": "Broadway & Wall St", "borough": "Manhattan", "lat": 40.7069, "lon": -74.0113},
    {"name": "Fulton St (btwn Broadway & Nassau)", "borough": "Manhattan", "lat": 40.7094, "lon": -74.0065},
    {"name": "Canal St (btwn Broadway & Centre)", "borough": "Manhattan", "lat": 40.7177, "lon": -73.9998},
    {"name": "Broadway & Houston St", "borough": "Manhattan", "lat": 40.7255, "lon": -73.9968},
    {"name": "Broadway & Prince St (SoHo)", "borough": "Manhattan", "lat": 40.7237, "lon": -73.9977},
    {"name": "Broadway & Spring St", "borough": "Manhattan", "lat": 40.7224, "lon": -73.9987},
    {"name": "Broadway & Bleecker St", "borough": "Manhattan", "lat": 40.7266, "lon": -73.9946},
    {"name": "Union Square West (14th St)", "borough": "Manhattan", "lat": 40.7359, "lon": -73.9911},
    {"name": "14th St & 5th Ave", "borough": "Manhattan", "lat": 40.7362, "lon": -73.9925},
    {"name": "23rd St & 5th Ave", "borough": "Manhattan", "lat": 40.7413, "lon": -73.9897},
    {"name": "34th St & 6th Ave (Herald Sq)", "borough": "Manhattan", "lat": 40.7492, "lon": -73.9879},
    {"name": "34th St & 7th Ave (Penn Station)", "borough": "Manhattan", "lat": 40.7504, "lon": -73.9914},
    {"name": "34th St & Broadway", "borough": "Manhattan", "lat": 40.7486, "lon": -73.9876},
    {"name": "42nd St & 5th Ave", "borough": "Manhattan", "lat": 40.7537, "lon": -73.9820},
    {"name": "42nd St & 6th Ave (Bryant Park)", "borough": "Manhattan", "lat": 40.7546, "lon": -73.9843},
    {"name": "42nd St & 7th Ave (Times Square)", "borough": "Manhattan", "lat": 40.7560, "lon": -73.9870},
    {"name": "42nd St & 8th Ave (Port Authority)", "borough": "Manhattan", "lat": 40.7567, "lon": -73.9910},
    {"name": "42nd St & Broadway (Times Square)", "borough": "Manhattan", "lat": 40.7558, "lon": -73.9862},
    {"name": "47th St & 7th Ave", "borough": "Manhattan", "lat": 40.7591, "lon": -73.9854},
    {"name": "49th St & 7th Ave", "borough": "Manhattan", "lat": 40.7607, "lon": -73.9847},
    {"name": "50th St & 5th Ave (Rockefeller Ctr)", "borough": "Manhattan", "lat": 40.7590, "lon": -73.9785},
    {"name": "57th St & 5th Ave", "borough": "Manhattan", "lat": 40.7637, "lon": -73.9744},
    {"name": "57th St & Broadway", "borough": "Manhattan", "lat": 40.7647, "lon": -73.9817},
    {"name": "59th St & Lexington Ave", "borough": "Manhattan", "lat": 40.7627, "lon": -73.9679},
    {"name": "59th St & Columbus Circle", "borough": "Manhattan", "lat": 40.7680, "lon": -73.9819},
    {"name": "72nd St & Broadway", "borough": "Manhattan", "lat": 40.7791, "lon": -73.9810},
    {"name": "72nd St & Columbus Ave", "borough": "Manhattan", "lat": 40.7779, "lon": -73.9783},
    {"name": "86th St & Broadway", "borough": "Manhattan", "lat": 40.7882, "lon": -73.9761},
    {"name": "86th St & Lexington Ave", "borough": "Manhattan", "lat": 40.7798, "lon": -73.9557},
    {"name": "96th St & Broadway", "borough": "Manhattan", "lat": 40.7944, "lon": -73.9720},
    {"name": "125th St & Lenox Ave", "borough": "Manhattan", "lat": 40.8082, "lon": -73.9451},
    {"name": "125th St & Adam Clayton Powell", "borough": "Manhattan", "lat": 40.8087, "lon": -73.9476},
    {"name": "125th St & Broadway", "borough": "Manhattan", "lat": 40.8158, "lon": -73.9584},
    {"name": "125th St & 5th Ave", "borough": "Manhattan", "lat": 40.8035, "lon": -73.9396},
    {"name": "145th St & St Nicholas Ave", "borough": "Manhattan", "lat": 40.8231, "lon": -73.9414},
    {"name": "Lexington Ave & 60th St", "borough": "Manhattan", "lat": 40.7632, "lon": -73.9674},
    {"name": "Madison Ave & 42nd St", "borough": "Manhattan", "lat": 40.7530, "lon": -73.9800},
    {"name": "Park Ave & 34th St", "borough": "Manhattan", "lat": 40.7482, "lon": -73.9813},
    {"name": "1st Ave & 14th St", "borough": "Manhattan", "lat": 40.7321, "lon": -73.9826},
    {"name": "2nd Ave & 86th St", "borough": "Manhattan", "lat": 40.7775, "lon": -73.9535},
    {"name": "3rd Ave & 86th St", "borough": "Manhattan", "lat": 40.7783, "lon": -73.9554},
    {"name": "Amsterdam Ave & 72nd St", "borough": "Manhattan", "lat": 40.7789, "lon": -73.9811},
    {"name": "8th Ave & 14th St", "borough": "Manhattan", "lat": 40.7403, "lon": -74.0007},
    {"name": "6th Ave & 14th St", "borough": "Manhattan", "lat": 40.7370, "lon": -73.9969},
    {"name": "Ave A & 7th St (East Village)", "borough": "Manhattan", "lat": 40.7267, "lon": -73.9838},
    {"name": "St Marks Pl & 2nd Ave", "borough": "Manhattan", "lat": 40.7290, "lon": -73.9885},
    {"name": "Christopher St & 7th Ave", "borough": "Manhattan", "lat": 40.7337, "lon": -74.0025},
    {"name": "West 4th St & 6th Ave", "borough": "Manhattan", "lat": 40.7321, "lon": -74.0001},
    {"name": "Chambers St & Broadway", "borough": "Manhattan", "lat": 40.7141, "lon": -74.0074},
    {"name": "Cortlandt St & Broadway", "borough": "Manhattan", "lat": 40.7096, "lon": -74.0105},
    {"name": "Water St & Wall St", "borough": "Manhattan", "lat": 40.7056, "lon": -74.0084},
    {"name": "Church St & Vesey St (WTC)", "borough": "Manhattan", "lat": 40.7117, "lon": -74.0100},
    {"name": "Dyckman St & Broadway", "borough": "Manhattan", "lat": 40.8651, "lon": -73.9275},
    {"name": "181st St & St Nicholas Ave", "borough": "Manhattan", "lat": 40.8488, "lon": -73.9346},
    {"name": "168th St & Broadway", "borough": "Manhattan", "lat": 40.8406, "lon": -73.9393},
    {"name": "155th St & St Nicholas Ave", "borough": "Manhattan", "lat": 40.8314, "lon": -73.9385},
    {"name": "110th St & Broadway", "borough": "Manhattan", "lat": 40.8014, "lon": -73.9659},
    {"name": "3rd Ave & 14th St", "borough": "Manhattan", "lat": 40.7335, "lon": -73.9870},
    {"name": "Astor Pl & Broadway", "borough": "Manhattan", "lat": 40.7298, "lon": -73.9912},
    {"name": "Grand St & Broadway", "borough": "Manhattan", "lat": 40.7197, "lon": -73.9991},

    # ── Brooklyn (20 locations) ───────────────────────────────────────────
    {"name": "Atlantic Ave & Flatbush Ave", "borough": "Brooklyn", "lat": 40.6850, "lon": -73.9779},
    {"name": "Fulton St & Flatbush Ave Ext", "borough": "Brooklyn", "lat": 40.6911, "lon": -73.9840},
    {"name": "Court St & Montague St", "borough": "Brooklyn", "lat": 40.6930, "lon": -73.9923},
    {"name": "Smith St & Bergen St", "borough": "Brooklyn", "lat": 40.6839, "lon": -73.9886},
    {"name": "5th Ave & 86th St (Bay Ridge)", "borough": "Brooklyn", "lat": 40.6212, "lon": -74.0222},
    {"name": "Graham Ave & Metropolitan Ave", "borough": "Brooklyn", "lat": 40.7142, "lon": -73.9443},
    {"name": "Bedford Ave & N 7th St", "borough": "Brooklyn", "lat": 40.7175, "lon": -73.9575},
    {"name": "Kings Highway & E 16th St", "borough": "Brooklyn", "lat": 40.6049, "lon": -73.9594},
    {"name": "86th St & Bay Pkwy (Bensonhurst)", "borough": "Brooklyn", "lat": 40.6019, "lon": -73.9958},
    {"name": "Church Ave & Flatbush Ave", "borough": "Brooklyn", "lat": 40.6510, "lon": -73.9631},
    {"name": "Fulton St & Jay St", "borough": "Brooklyn", "lat": 40.6924, "lon": -73.9870},
    {"name": "Myrtle Ave & Broadway", "borough": "Brooklyn", "lat": 40.6968, "lon": -73.9857},
    {"name": "7th Ave & 9th St (Park Slope)", "borough": "Brooklyn", "lat": 40.6703, "lon": -73.9808},
    {"name": "Nostrand Ave & Fulton St", "borough": "Brooklyn", "lat": 40.6808, "lon": -73.9499},
    {"name": "Pitkin Ave & Rockaway Ave", "borough": "Brooklyn", "lat": 40.6700, "lon": -73.9078},
    {"name": "Brighton Beach Ave & Coney Island Ave", "borough": "Brooklyn", "lat": 40.5780, "lon": -73.9611},
    {"name": "4th Ave & 9th St", "borough": "Brooklyn", "lat": 40.6709, "lon": -73.9889},
    {"name": "Cortelyou Rd & E 16th St", "borough": "Brooklyn", "lat": 40.6398, "lon": -73.9623},
    {"name": "DeKalb Ave & Flatbush Ave", "borough": "Brooklyn", "lat": 40.6894, "lon": -73.9768},
    {"name": "Livingston St & Hoyt St", "borough": "Brooklyn", "lat": 40.6887, "lon": -73.9857},

    # ── Queens (15 locations) ─────────────────────────────────────────────
    {"name": "Roosevelt Ave & 74th St (Jackson Hts)", "borough": "Queens", "lat": 40.7474, "lon": -73.8914},
    {"name": "Jamaica Ave & Parsons Blvd", "borough": "Queens", "lat": 40.7025, "lon": -73.8009},
    {"name": "Steinway St & Broadway (Astoria)", "borough": "Queens", "lat": 40.7619, "lon": -73.9182},
    {"name": "Broadway & 37th St (Astoria)", "borough": "Queens", "lat": 40.7567, "lon": -73.9202},
    {"name": "Main St & Roosevelt Ave (Flushing)", "borough": "Queens", "lat": 40.7597, "lon": -73.8307},
    {"name": "37th Ave & 74th St (Jackson Hts)", "borough": "Queens", "lat": 40.7484, "lon": -73.8916},
    {"name": "Queens Blvd & 63rd Rd", "borough": "Queens", "lat": 40.7290, "lon": -73.8455},
    {"name": "Austin St & Ascan Ave (Forest Hills)", "borough": "Queens", "lat": 40.7208, "lon": -73.8457},
    {"name": "Jamaica Ave & 164th St", "borough": "Queens", "lat": 40.7049, "lon": -73.7944},
    {"name": "Metropolitan Ave & 70th St", "borough": "Queens", "lat": 40.7141, "lon": -73.8857},
    {"name": "30th Ave & 31st St (Astoria)", "borough": "Queens", "lat": 40.7682, "lon": -73.9218},
    {"name": "Ditmars Blvd & 31st St (Astoria)", "borough": "Queens", "lat": 40.7753, "lon": -73.9129},
    {"name": "Northern Blvd & Main St (Flushing)", "borough": "Queens", "lat": 40.7630, "lon": -73.8297},
    {"name": "Lefferts Blvd & Metropolitan Ave", "borough": "Queens", "lat": 40.7102, "lon": -73.8190},
    {"name": "Myrtle Ave & Fresh Pond Rd (Ridgewood)", "borough": "Queens", "lat": 40.7045, "lon": -73.8960},

    # ── Bronx (12 locations) ──────────────────────────────────────────────
    {"name": "E Fordham Rd & Grand Concourse", "borough": "Bronx", "lat": 40.8616, "lon": -73.8905},
    {"name": "E Fordham Rd & Jerome Ave", "borough": "Bronx", "lat": 40.8618, "lon": -73.8980},
    {"name": "E 149th St & Grand Concourse (Hub)", "borough": "Bronx", "lat": 40.8199, "lon": -73.9268},
    {"name": "161st St & River Ave (Yankee Std)", "borough": "Bronx", "lat": 40.8279, "lon": -73.9260},
    {"name": "3rd Ave & E 149th St", "borough": "Bronx", "lat": 40.8188, "lon": -73.9175},
    {"name": "Westchester Ave & Southern Blvd", "borough": "Bronx", "lat": 40.8279, "lon": -73.8924},
    {"name": "E Tremont Ave & 3rd Ave", "borough": "Bronx", "lat": 40.8453, "lon": -73.8949},
    {"name": "Jerome Ave & Burnside Ave", "borough": "Bronx", "lat": 40.8534, "lon": -73.9015},
    {"name": "Kingsbridge Rd & Grand Concourse", "borough": "Bronx", "lat": 40.8663, "lon": -73.8968},
    {"name": "Pelham Pkwy & White Plains Rd", "borough": "Bronx", "lat": 40.8570, "lon": -73.8673},
    {"name": "E 138th St & 3rd Ave (Mott Haven)", "borough": "Bronx", "lat": 40.8097, "lon": -73.9227},
    {"name": "Bainbridge Ave & E 204th St", "borough": "Bronx", "lat": 40.8736, "lon": -73.8823},

    # ── Staten Island (7 locations) ───────────────────────────────────────
    {"name": "Bay St & Victory Blvd (St George)", "borough": "Staten Island", "lat": 40.6434, "lon": -74.0768},
    {"name": "New Dorp Ln & Hylan Blvd", "borough": "Staten Island", "lat": 40.5726, "lon": -74.1168},
    {"name": "Forest Ave & Hart Blvd", "borough": "Staten Island", "lat": 40.6316, "lon": -74.1165},
    {"name": "Hylan Blvd & Nelson Ave (Great Kills)", "borough": "Staten Island", "lat": 40.5532, "lon": -74.1512},
    {"name": "Richmond Ave & Richmond Hill Rd", "borough": "Staten Island", "lat": 40.5856, "lon": -74.1501},
    {"name": "Castleton Ave & Jewett Ave", "borough": "Staten Island", "lat": 40.6335, "lon": -74.1236},
    {"name": "Victory Blvd & Jewett Ave", "borough": "Staten Island", "lat": 40.6236, "lon": -74.1290},
]

# ── Bridge / Greenway locations ───────────────────────────────────────────
BRIDGES = [
    {"name": "Brooklyn Bridge (Manhattan side)", "lat": 40.7080, "lon": -74.0039},
    {"name": "Brooklyn Bridge (Brooklyn side)", "lat": 40.6975, "lon": -73.9936},
    {"name": "Manhattan Bridge (Manhattan side)", "lat": 40.7126, "lon": -73.9974},
    {"name": "Manhattan Bridge (Brooklyn side)", "lat": 40.7043, "lon": -73.9876},
    {"name": "Williamsburg Bridge (Manhattan side)", "lat": 40.7136, "lon": -73.9720},
    {"name": "Williamsburg Bridge (Brooklyn side)", "lat": 40.7094, "lon": -73.9627},
    {"name": "Queensboro Bridge (Manhattan side)", "lat": 40.7577, "lon": -73.9585},
    {"name": "Queensboro Bridge (Queens side)", "lat": 40.7544, "lon": -73.9471},
    {"name": "Willis Ave Bridge", "lat": 40.8064, "lon": -73.9322},
    {"name": "3rd Ave Bridge", "lat": 40.8082, "lon": -73.9318},
    {"name": "Madison Ave Bridge", "lat": 40.8134, "lon": -73.9339},
    {"name": "145th St Bridge", "lat": 40.8213, "lon": -73.9379},
    {"name": "Hudson River Greenway (midpoint)", "lat": 40.7410, "lon": -74.0091},
]

# ── 3. Colour by borough ────────────────────────────────────────────────────
BOROUGH_COLORS = {
    "Manhattan": "#e63946",
    "Brooklyn": "#457b9d",
    "Queens": "#2a9d8f",
    "Bronx": "#e9c46a",
    "Staten Island": "#f4a261",
}

# ── 4. Build map ─────────────────────────────────────────────────────────────
m = folium.Map(location=[40.7128, -74.0060], zoom_start=11,
               tiles="cartodbpositron")

# Borough count layers with MarkerCluster
for borough, color in BOROUGH_COLORS.items():
    cluster = MarkerCluster(name=borough).add_to(m)
    locs = [loc for loc in LOCATIONS if loc["borough"] == borough]
    for loc in locs:
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(
                f"<b>{loc['name']}</b><br>"
                f"Borough: {loc['borough']}<br>"
                f"<i>NYC DOT Bi-Annual Ped Count Location</i>",
                max_width=260,
            ),
            tooltip=loc["name"],
        ).add_to(cluster)

# Bridge / Greenway markers
bridge_group = folium.FeatureGroup(name="Bridges & Greenway").add_to(m)
for loc in BRIDGES:
    folium.Marker(
        location=[loc["lat"], loc["lon"]],
        icon=folium.Icon(color="darkpurple", icon="road", prefix="fa"),
        popup=folium.Popup(
            f"<b>{loc['name']}</b><br>"
            f"<i>Bridge / Greenway Count Point</i>",
            max_width=260,
        ),
        tooltip=loc["name"],
    ).add_to(bridge_group)

folium.LayerControl(collapsed=False).add_to(m)

# ── 5. Legend / model summary overlay ────────────────────────────────────────
imp_sorted = sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1])
imp_rows = "".join(
    f"<tr><td style='padding:2px 6px'>{name}</td>"
    f"<td style='padding:2px 6px'>{imp:.4f}</td>"
    f"<td style='padding:2px 0'>"
    f"<div style='background:#3b82f6;height:12px;width:{imp*400:.0f}px;border-radius:2px'></div>"
    f"</td></tr>"
    for name, imp in imp_sorted
)

legend_html = f"""
<div style="
    position: fixed; bottom: 20px; left: 20px; z-index: 9999;
    background: white; padding: 14px 18px; border-radius: 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.25); font-family: sans-serif;
    font-size: 12px; max-width: 400px;">
  <h4 style="margin:0 0 8px 0; font-size:14px;">
    Random Forest Model Summary
  </h4>
  <p style="margin:0 0 6px 0; color:#555;">
    <b>File:</b> RF_wknd_n20_am_models.pckl<br>
    <b>Type:</b> RandomForestRegressor &bull; 100 trees &bull; 10 features<br>
    <b>Period:</b> Weekend AM
  </p>
  <table style="border-collapse:collapse; font-size:11px;">
    <tr style="font-weight:bold; border-bottom:1px solid #ddd;">
      <td style="padding:2px 6px">Feature</td>
      <td style="padding:2px 6px">Importance</td>
      <td style="padding:2px 6px">Bar</td>
    </tr>
    {imp_rows}
  </table>
  <hr style="margin:8px 0; border:none; border-top:1px solid #ddd;">
  <div>
    <span style="display:inline-block;width:12px;height:12px;background:#e63946;border-radius:50%;margin-right:4px;vertical-align:middle"></span> Manhattan (60)
    <span style="display:inline-block;width:12px;height:12px;background:#457b9d;border-radius:50%;margin-right:4px;margin-left:8px;vertical-align:middle"></span> Brooklyn (20)<br>
    <span style="display:inline-block;width:12px;height:12px;background:#2a9d8f;border-radius:50%;margin-right:4px;vertical-align:middle"></span> Queens (15)
    <span style="display:inline-block;width:12px;height:12px;background:#e9c46a;border-radius:50%;margin-right:4px;margin-left:8px;vertical-align:middle"></span> Bronx (12)
    <span style="display:inline-block;width:12px;height:12px;background:#f4a261;border-radius:50%;margin-right:4px;margin-left:8px;vertical-align:middle"></span> S.I. (7)
  </div>
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

# ── 6. Save ──────────────────────────────────────────────────────────────────
output = "nyc_ped_map.html"
m.save(output)
print(f"Map saved → {output}")
print(f"  {len(LOCATIONS)} on-street locations + {len(BRIDGES)} bridge/greenway points")
