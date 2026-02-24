"""
NYC Subway Station 5-Minute Walk Radius Map

Generates an interactive map showing the area reachable within a 5-minute walk
(~400 meters) from every NYC subway station. Inspired by similar transit
accessibility maps used in urban planning.
"""

import folium
from folium import Circle, CircleMarker, Popup
import json

# 5-minute walk ≈ 400 meters at standard pedestrian speed (~4.8 km/h)
WALK_RADIUS_METERS = 400

# NYC subway line color scheme (official MTA colors)
LINE_COLORS = {
    "1": "#EE352E", "2": "#EE352E", "3": "#EE352E",
    "4": "#00933C", "5": "#00933C", "6": "#00933C",
    "7": "#B933AD",
    "A": "#0039A6", "C": "#0039A6", "E": "#0039A6",
    "B": "#FF6319", "D": "#FF6319", "F": "#FF6319", "M": "#FF6319",
    "G": "#6CBE45",
    "J": "#996633", "Z": "#996633",
    "L": "#A7A9AC",
    "N": "#FCCC0A", "Q": "#FCCC0A", "R": "#FCCC0A", "W": "#FCCC0A",
    "S": "#808183",
}

# Comprehensive NYC subway station data: (name, latitude, longitude, routes)
# Sources: MTA GTFS data, NYC Open Data
STATIONS = [
    ("Bay Ridge-95 St", 40.616624, -74.030964, "R"),
    ("86 St", 40.622715, -74.028368, "R"),
    ("77 St", 40.629702, -74.025514, "R"),
    ("Bay Ridge Ave", 40.634945, -74.023411, "R"),
    ("59 St", 40.641426, -74.017972, "N-R"),
    ("53 St", 40.644959, -74.014034, "R"),
    ("Bowling Green", 40.704782, -74.014099, "4-5"),
    ("Rector St", 40.70784, -74.013691, "1"),
    ("Wall St", 40.707466, -74.011867, "2-3"),
    ("8 Ave", 40.635011, -74.011717, "N"),
    ("Cortlandt St", 40.710454, -74.011324, "R-W"),
    ("Broad St", 40.706539, -74.011052, "J-Z"),
    ("World Trade Ctr", 40.712557, -74.009807, "E"),
    ("45 St", 40.648866, -74.010086, "R"),
    ("Chambers St", 40.715436, -74.009335, "1-2-3"),
    ("Park Place", 40.713061, -74.008777, "2-3"),
    ("Fulton St", 40.709938, -74.007983, "2-3-4-5-A-C-J-Z"),
    ("Chambers St/Murray St", 40.713086, -74.007232, "A-C"),
    ("Franklin St", 40.719323, -74.006953, "1"),
    ("Canal St", 40.722819, -74.006267, "1"),
    ("Ft Hamilton Pkwy", 40.631428, -74.005387, "N"),
    ("Houston St", 40.728202, -74.005344, "1"),
    ("Brooklyn Bridge-City Hall", 40.713159, -74.003917, "4-5-6"),
    ("Spring St", 40.726202, -74.003627, "C-E"),
    ("36 St", 40.65515, -74.003477, "D-N-R"),
    ("Christopher St-Sheridan Sq", 40.733405, -74.002898, "1"),
    ("14 St", 40.740388, -74.002104, "1-2-3"),
    ("18 Ave", 40.607958, -74.001782, "N"),
    ("W 4 St-Washington Sq", 40.732251, -74.000559, "A-B-C-D-E-F-M"),
    ("79 St", 40.613513, -74.000645, "N"),
    ("71 St", 40.619588, -73.998842, "D"),
    ("20 Ave", 40.604798, -73.998456, "N"),
    ("25 St", 40.660481, -73.998059, "R"),
    ("23 St", 40.745924, -73.998005, "C-E"),
    ("18 St", 40.741096, -73.997877, "1"),
    ("Prince St", 40.724332, -73.997684, "N-R-W"),
    ("Spring St", 40.722397, -73.997211, "6"),
    ("14 St/6 Ave", 40.737348, -73.9969, "F-M-L-1-2-3"),
    ("New Utrecht Ave", 40.625419, -73.996632, "D-N"),
    ("Broadway-Lafayette", 40.725297, -73.996204, "B-D-F-M"),
    ("Smith-9 St", 40.673714, -73.996139, "F-G"),
    ("Bleecker St", 40.725665, -73.995645, "4-6"),
    ("Carroll St", 40.680231, -73.99498, "F-G"),
    ("50 St", 40.636232, -73.994765, "D"),
    ("9 Ave", 40.646343, -73.994551, "D"),
    ("Ft Hamilton Pkwy", 40.640872, -73.994229, "D"),
    ("Grand St", 40.718542, -73.994164, "B-D"),
    ("Bowery", 40.720315, -73.994014, "J-Z"),
    ("Bay Pkwy", 40.601898, -73.993821, "N"),
    ("34 St-Penn Sta", 40.752247, -73.993456, "1-2-3"),
    ("28 St", 40.747224, -73.99336, "1"),
    ("Clark St", 40.697356, -73.992888, "2-3"),
    ("Prospect Ave", 40.665405, -73.992877, "R"),
    ("23 St", 40.742868, -73.99277, "F-M"),
    ("8 St-NYU", 40.730348, -73.992705, "N-R-W"),
    ("Astor Place", 40.730056, -73.991042, "4-6"),
    ("Bergen St", 40.686154, -73.990881, "F-G"),
    ("14 St-Union Sq", 40.734836, -73.990688, "4-5-6-N-Q-R-W-L"),
    ("High St", 40.699316, -73.990474, "A-C"),
    ("East Broadway", 40.713647, -73.990152, "F"),
    ("Borough Hall", 40.692404, -73.990151, "4-5-2-3"),
    ("2 Ave", 40.723291, -73.989873, "F"),
    ("42 St-Port Authority", 40.757303, -73.989787, "A-C-E"),
    ("23 St", 40.741006, -73.989315, "N-R-W"),
    ("9 St-4 Ave", 40.67032, -73.988757, "F-G-R"),
    ("28 St", 40.745574, -73.988682, "N-R-W"),
    ("33 St", 40.748931, -73.988113, "6"),
    ("34 St-Herald Sq", 40.749533, -73.987899, "B-D-F-M-N-Q-R-W"),
    ("Essex St/Delancey St", 40.71838, -73.987813, "F-J-M-Z"),
    ("Jay St-MetroTech", 40.692338, -73.987342, "A-C-F-R"),
    ("3 Ave", 40.733243, -73.987169, "L"),
    ("25 Ave", 40.597873, -73.986955, "D"),
    ("York St", 40.699756, -73.98689, "F"),
    ("42 St-Times Sq", 40.755905, -73.986504, "1-2-3-7-N-Q-R-W-S"),
    ("Hoyt-Schermerhorn", 40.688465, -73.985474, "A-C-G"),
    ("20 Ave", 40.617373, -73.985088, "D"),
    ("Hoyt St", 40.690547, -73.985066, "2-3"),
    ("42 St-Bryant Pk", 40.754198, -73.984573, "B-D-F-M"),
    ("28 St", 40.743095, -73.984251, "6"),
    ("49 St", 40.760139, -73.984112, "N-R-W"),
    ("50 St", 40.761675, -73.983908, "1"),
    ("Bay 50 St", 40.588879, -73.983629, "D"),
    ("Union St", 40.677302, -73.983135, "R"),
    ("66 St-Lincoln Ctr", 40.773424, -73.982234, "1"),
    ("Bay Pkwy", 40.612006, -73.982009, "D"),
    ("5 Ave-Bryant Pk", 40.753824, -73.981966, "7"),
    ("72 St", 40.778575, -73.981912, "1-2-3"),
    ("59 St-Columbus Circle", 40.76811, -73.981891, "1-A-B-C-D"),
    ("DeKalb Ave", 40.690612, -73.981848, "B-D-N-Q-R"),
    ("33 St", 40.746119, -73.981826, "4-6"),
    ("1 Ave", 40.730901, -73.981719, "L"),
    ("7 Ave-53 St", 40.762877, -73.98159, "B-D-E"),
    ("47-50 St-Rockefeller Ctr", 40.758652, -73.981311, "B-D-F-M"),
    ("Stillwell Ave-Coney Island", 40.577423, -73.981225, "D-F-N-Q"),
    ("Kings Hwy", 40.603967, -73.980668, "N"),
    ("57 St-7 Ave", 40.764755, -73.980646, "N-Q-R-W"),
    ("Nevins St", 40.688269, -73.980453, "2-3-4-5"),
    ("7 Ave-Park Slope", 40.666276, -73.980324, "F-G"),
    ("79 St", 40.783872, -73.979938, "1"),
    ("Church Ave", 40.644039, -73.979541, "F-G"),
    ("15 St-Prospect Park", 40.660376, -73.979509, "F-G"),
    ("Ave U", 40.597482, -73.979359, "N"),
    ("86 St", 40.592676, -73.978243, "D"),
    ("Ditmas Ave", 40.63615, -73.978179, "F"),
    ("57 St", 40.763625, -73.977449, "F"),
    ("Atlantic Ave-Barclays Ctr", 40.684063, -73.977417, "2-3-4-5-B-D-N-Q-R"),
    ("18 Ave", 40.629881, -73.977149, "F"),
    ("Grand Central-42 St", 40.751849, -73.976945, "4-5-6-7-S"),
    ("72 St", 40.775545, -73.976398, "2-3"),
    ("86 St", 40.788844, -73.97599, "1"),
    ("W 8 St-NY Aquarium", 40.576152, -73.975925, "F-Q"),
    ("Ft Hamilton Pkwy", 40.650722, -73.975818, "F-G"),
    ("Ave I", 40.625305, -73.975732, "F"),
    ("Fulton St", 40.68713, -73.975346, "G"),
    ("5 Ave-53 St", 40.760179, -73.975196, "E-M"),
    ("Bergen St", 40.680801, -73.975132, "2-3"),
    ("Neptune Ave", 40.580992, -73.974531, "F"),
    ("Ave X", 40.589547, -73.974295, "F"),
    ("Ave N", 40.615174, -73.974166, "F"),
    ("Lafayette Ave", 40.68617, -73.973908, "C"),
    ("5 Ave-59 St", 40.764909, -73.973372, "N-R-W"),
    ("Ave U", 40.596065, -73.973329, "F"),
    ("Ave P", 40.609147, -73.972986, "F"),
    ("7 Ave", 40.677172, -73.972514, "B-Q"),
    ("96 St", 40.79388, -73.972363, "1-2-3"),
    ("Kings Hwy", 40.603234, -73.972342, "B-Q"),
    ("81 St-Museum of Natural History", 40.781435, -73.972149, "B-C"),
    ("51 St", 40.757108, -73.97187, "4-6"),
    ("Grand Army Plaza", 40.675219, -73.971012, "2-3"),
    ("Lexington Ave-53 St", 40.75753, -73.969102, "E-M"),
    ("86 St", 40.785822, -73.968952, "4-5-6"),
    ("Ocean Pkwy", 40.576298, -73.968523, "Q"),
    ("103 St", 40.799354, -73.968329, "1"),
    ("Lexington Ave-59 St", 40.762796, -73.967686, "4-5-6-N-R-W"),
    ("Clinton-Washington Aves", 40.688123, -73.966742, "G"),
    ("110 St-Cathedral", 40.804032, -73.966742, "1"),
    ("96 St", 40.791654, -73.964682, "Q"),
    ("Beverly Rd", 40.643982, -73.96451, "B-Q"),
    ("Eastern Pkwy-Brooklyn Museum", 40.672013, -73.96436, "2-3"),
    ("116 St-Columbia", 40.80819, -73.964124, "1"),
    ("68 St-Hunter College", 40.768143, -73.964016, "4-6"),
    ("Cortelyou Rd", 40.640905, -73.963866, "B-Q"),
    ("Church Ave", 40.650494, -73.962836, "B-Q"),
    ("Newkirk Ave", 40.635059, -73.962793, "B-Q"),
    ("Prospect Park", 40.661596, -73.962193, "B-Q-S"),
    ("Brighton Beach", 40.577961, -73.961806, "B-Q"),
    ("Ave H", 40.629164, -73.961678, "B-Q"),
    ("103 St", 40.796105, -73.961399, "B-C"),
    ("Parkside Ave", 40.655053, -73.961227, "B-Q"),
    ("Ave J", 40.625028, -73.960819, "B-Q"),
    ("Classon Ave", 40.688855, -73.960025, "G"),
    ("77 St", 40.773636, -73.959875, "6"),
    ("Ave M", 40.617568, -73.95936, "B-Q"),
    ("Botanic Garden-Franklin Ave", 40.670499, -73.958759, "2-3-4-5-S"),
    ("125 St", 40.815596, -73.958395, "1"),
    ("Cathedral Pkwy-110 St", 40.800637, -73.958201, "B-C"),
    ("Franklin Ave", 40.670711, -73.958051, "C-S"),
    ("Park Place", 40.67491, -73.957794, "S"),
    ("Kings Hwy", 40.608691, -73.957772, "B-Q"),
    ("Marcy Ave", 40.708377, -73.957751, "J-M-Z"),
    ("Bedford Ave", 40.717241, -73.956614, "L"),
    ("Franklin Ave", 40.681159, -73.956056, "A-C"),
    ("Ave U", 40.599307, -73.955916, "B-Q"),
    ("86 St", 40.779485, -73.955541, "4-5-6"),
    ("Neck Rd", 40.595234, -73.95509, "B-Q"),
    ("116 St", 40.805072, -73.954833, "B-C"),
    ("Greenpoint Ave", 40.731324, -73.954425, "G"),
    ("Sheepshead Bay", 40.58681, -73.954167, "B-Q"),
    ("137 St-City College", 40.821994, -73.953674, "1"),
    ("Vernon Blvd-Jackson Ave", 40.742624, -73.953545, "7"),
    ("Hewes St", 40.706994, -73.953481, "J-M"),
    ("Bedford-Nostrand Aves", 40.689636, -73.953459, "G"),
    ("Roosevelt Island", 40.759123, -73.953266, "F"),
    ("125 St", 40.811056, -73.952386, "A-B-C-D"),
    ("110 St-Central Park North", 40.79911, -73.951807, "2-3"),
    ("Lorimer St", 40.713875, -73.951592, "L"),
    ("Metropolitan Ave", 40.712774, -73.951427, "G"),
    ("Nassau Ave", 40.724608, -73.951271, "G"),
    ("96 St", 40.785822, -73.95097, "Q"),
    ("President St", 40.667879, -73.950648, "2-5"),
    ("Sterling St", 40.662752, -73.950605, "2-5"),
    ("Nostrand Ave", 40.669735, -73.950455, "3"),
    ("145 St", 40.826426, -73.950412, "1"),
    ("Broadway", 40.7061, -73.950348, "G"),
    ("Nostrand Ave", 40.68041, -73.950326, "A-C"),
    ("Flushing Ave", 40.700374, -73.950284, "J-M"),
    ("21 St-Van Alst", 40.743973, -73.949876, "G"),
    ("116 St", 40.802098, -73.949625, "2-3"),
    ("Church Ave", 40.650843, -73.949575, "2-5"),
    ("Myrtle-Willoughby Aves", 40.694568, -73.949046, "G"),
    ("Beverly Rd", 40.645089, -73.948975, "2-5"),
    ("Hunters Point Ave", 40.74238, -73.948889, "7"),
    ("Newkirk Ave-Little Haiti", 40.639961, -73.948352, "2-5"),
    ("135 St", 40.817902, -73.947644, "2-3"),
    ("Flatbush Ave-Brooklyn College", 40.632836, -73.947642, "2-5"),
    ("103 St", 40.790582, -73.947473, "6"),
    ("Lorimer St", 40.703855, -73.947387, "J-M"),
    ("125 St", 40.808076, -73.945906, "2-3"),
    ("Court Sq-45 Rd", 40.747029, -73.94537, "7"),
    ("Court Sq-23 St", 40.747257, -73.945112, "E-M-G"),
    ("157 St", 40.833879, -73.944726, "1"),
    ("110 St", 40.795066, -73.944297, "6"),
    ("145 St", 40.824787, -73.944232, "3"),
    ("Graham Ave", 40.71459, -73.944104, "L"),
    ("21 St", 40.7541, -73.94258, "N-W"),
    ("Kingston Ave", 40.669409, -73.942173, "3"),
    ("Flushing Ave", 40.700244, -73.941658, "J-M"),
    ("116 St", 40.798574, -73.941593, "6"),
    ("155 St", 40.830551, -73.941486, "C"),
    ("135 St", 40.814459, -73.940992, "B-C"),
    ("Kingston-Throop Aves", 40.679921, -73.940858, "A-C"),
    ("Grand St", 40.711874, -73.94067, "L"),
    ("Queensboro Plaza", 40.750508, -73.940177, "7-N-W"),
    ("168 St", 40.840778, -73.940091, "1"),
    ("Montrose Ave", 40.707889, -73.940005, "L"),
    ("163 St-Amsterdam Ave", 40.835957, -73.939898, "C"),
    ("175 St", 40.847369, -73.939683, "A"),
    ("155 St", 40.829934, -73.938632, "B-D"),
    ("181 St", 40.851686, -73.937967, "A"),
    ("125 St", 40.804406, -73.937452, "4-5-6"),
    ("Queens Plaza", 40.748948, -73.937194, "E-M-R"),
    ("148 St-Lenox Terminal", 40.823877, -73.936443, "3"),
    ("145 St", 40.820402, -73.936315, "A-B-C-D"),
    ("Myrtle Ave", 40.697266, -73.935692, "J-M-Z"),
    ("190 St", 40.859022, -73.93419, "A"),
    ("181 St", 40.849495, -73.933632, "1"),
    ("Morgan Ave", 40.706148, -73.93316, "L"),
    ("Crown Hts-Utica Ave", 40.669279, -73.932967, "3-4"),
    ("39 Ave-Beebe Ave", 40.753076, -73.93271, "N-W"),
    ("33 St-Rawson St", 40.744558, -73.930993, "7"),
    ("Utica Ave", 40.679279, -73.930585, "A-C"),
    ("138 St-Grand Concourse", 40.813208, -73.929877, "4-5"),
    ("191 St", 40.855176, -73.929384, "1"),
    ("36 Ave", 40.756977, -73.929373, "N-W"),
    ("Kosciuszko St", 40.693329, -73.928826, "J"),
    ("36 St", 40.75202, -73.92874, "N-W"),
    ("Central Ave", 40.697673, -73.927131, "M"),
    ("Dyckman St-200 St", 40.865286, -73.92698, "A"),
    ("149 St-Grand Concourse", 40.818429, -73.926927, "2-4-5"),
    ("3 Ave-138 St", 40.810512, -73.926165, "6"),
    ("161 St-Yankee Stadium", 40.827888, -73.925736, "4-B-D"),
    ("Dyckman St", 40.860523, -73.925575, "1"),
    ("Broadway", 40.761959, -73.925382, "N-W"),
    ("40 St-Lowery St", 40.743778, -73.923998, "7"),
    ("Jefferson St", 40.706636, -73.922925, "L"),
    ("Sutter Ave-Rutland Rd", 40.664591, -73.922668, "3"),
    ("Gates Ave", 40.689652, -73.922281, "J-Z"),
    ("30 Ave-Grand Ave", 40.766843, -73.921423, "N-W"),
    ("167 St", 40.835535, -73.92138, "4"),
    ("Ralph Ave", 40.678815, -73.920801, "A-C"),
    ("Steinway St", 40.756864, -73.920736, "M-R"),
    ("Inwood-207 St", 40.868045, -73.919921, "A"),
    ("Knickerbocker Ave", 40.698666, -73.919685, "M"),
    ("Brook Ave", 40.808044, -73.919234, "6"),
    ("207 St", 40.864653, -73.918719, "1"),
    ("DeKalb Ave", 40.703839, -73.91844, "L"),
    ("167 St", 40.833773, -73.91843, "B-D"),
    ("46 St-Bliss St", 40.743079, -73.918419, "7"),
    ("170 St", 40.840048, -73.917775, "4"),
    ("149 St-3 Ave", 40.816132, -73.917754, "2-5"),
    ("Astoria Blvd-Hoyt Ave", 40.770426, -73.917614, "N-W"),
    ("Halsey St", 40.68617, -73.916337, "J"),
    ("Saratoga Ave", 40.661466, -73.916316, "3"),
    ("215 St", 40.869359, -73.915329, "1"),
    ("Mt Eden Ave", 40.844406, -73.914621, "4"),
    ("Cypress Ave", 40.805737, -73.914471, "6"),
    ("170 St", 40.839301, -73.913355, "B-D"),
    ("46 St", 40.756312, -73.913333, "M-R"),
    ("176 St", 40.848635, -73.912497, "4"),
    ("52 St-Lincoln Ave", 40.744103, -73.912497, "7"),
    ("Ditmars Blvd", 40.774984, -73.912067, "N-W"),
    ("Rockaway Ave", 40.67836, -73.911939, "A-C"),
    ("Myrtle Ave", 40.699707, -73.91181, "M"),
    ("Chauncey St", 40.682867, -73.91048, "J-Z"),
    ("Marble Hill-225 St", 40.874551, -73.909879, "1"),
    ("Rockaway Ave", 40.662541, -73.908763, "3"),
    ("Jackson Ave", 40.816505, -73.907797, "2-5"),
    ("Seneca Ave", 40.702798, -73.907776, "M"),
    ("Burnside Ave", 40.85339, -73.907733, "4"),
    ("E 143 St-St Mary's St", 40.808742, -73.90769, "6"),
    ("Northern Blvd", 40.752898, -73.905973, "M-R"),
    ("Bushwick Ave-Aberdeen St", 40.682558, -73.905501, "L"),
    ("Tremont Ave", 40.850307, -73.905244, "B-D"),
    ("231 St", 40.878867, -73.904858, "1"),
    ("Broadway-East New York", 40.678848, -73.904139, "J-Z"),
    ("E 149 St", 40.812104, -73.904085, "6"),
    ("Halsey St", 40.695607, -73.904021, "L"),
    ("Wilson Ave", 40.688676, -73.903999, "L"),
    ("183 St", 40.858389, -73.903828, "4"),
    ("Forest Ave", 40.704424, -73.903077, "M"),
    ("61 St-Woodside", 40.745623, -73.902969, "7"),
    ("Atlantic Ave", 40.675496, -73.902819, "L"),
    ("Junius St", 40.663419, -73.902454, "3"),
    ("Sutter Ave", 40.669376, -73.902047, "L"),
    ("Rockaway Pkwy-Canarsie", 40.64666, -73.901832, "L"),
    ("Prospect Ave", 40.819396, -73.901467, "2-5"),
    ("Fordham Rd", 40.862941, -73.901199, "4"),
    ("238 St", 40.884821, -73.900759, "1"),
    ("182-183 Sts", 40.856085, -73.900695, "B-D"),
    ("Livonia Ave", 40.663801, -73.900444, "L"),
    ("East 105 St", 40.650625, -73.899558, "L"),
    ("New Lots Ave", 40.658748, -73.899472, "3"),
    ("Alabama Ave", 40.677107, -73.898871, "J"),
    ("242 St-Van Cortlandt Park", 40.889185, -73.898549, "1"),
    ("65 St", 40.749663, -73.898485, "M-R"),
    ("Kingsbridge Rd", 40.867899, -73.897326, "4"),
    ("Intervale Ave", 40.822172, -73.896747, "2-5"),
    ("Liberty Ave", 40.674552, -73.896554, "J"),
    ("69 St-Fisk Ave", 40.746325, -73.896403, "7"),
    ("Longwood Ave", 40.816083, -73.89606, "6"),
    ("Pennsylvania Ave", 40.664884, -73.894258, "3-4"),
    ("Simpson St", 40.82417, -73.893228, "2-5"),
    ("Freeman St", 40.829966, -73.891876, "2-5"),
    ("Van Siclen Ave", 40.678018, -73.891726, "J-Z"),
    ("Flushing-Main St", 40.759578, -73.830056, "7"),
    ("Roosevelt Ave-Jackson Hts", 40.746655, -73.891361, "E-F-M-R-7"),
    ("Hunts Point Ave", 40.820889, -73.890567, "6"),
    ("Bedford Park Blvd", 40.873399, -73.890084, "4"),
    ("Metropolitan Ave", 40.711353, -73.88958, "M"),
    ("Van Siclen Ave", 40.665405, -73.889451, "3"),
    ("174-175 Sts", 40.845892, -73.910136, "B-D"),
    ("Whitlock Ave", 40.826508, -73.886425, "6"),
    ("Cleveland St", 40.679938, -73.884687, "J"),
    ("Mosholu Pkwy", 40.87963, -73.884666, "4"),
    ("New Lots Ave", 40.666252, -73.884087, "L"),
    ("82 St-Jackson Hts", 40.747647, -73.883786, "7"),
    ("Elmhurst Ave", 40.742445, -73.882005, "M-R"),
    ("Shepherd Ave", 40.674161, -73.880761, "A-C"),
    ("Norwood Ave", 40.681598, -73.880074, "J"),
    ("E Tremont Ave", 40.840097, -73.879774, "2-5"),
    ("Elder Ave", 40.828894, -73.879559, "6"),
    ("Norwood-205 St", 40.874827, -73.878872, "D"),
    ("Woodlawn", 40.885973, -73.878851, "4"),
    ("Grand Ave-Newtown", 40.736998, -73.877242, "M-R"),
    ("90 St-Elmhurst Ave", 40.748541, -73.876791, "7"),
    ("Morrison Ave-Soundview", 40.829495, -73.874559, "6"),
    ("Crescent St", 40.683209, -73.873765, "J-Z"),
    ("E 180 St", 40.841882, -73.873551, "2-5"),
    ("Cypress Hills", 40.689945, -73.872564, "J"),
    ("Euclid Ave", 40.675382, -73.87207, "A-C"),
    ("Junction Blvd", 40.749143, -73.869452, "7"),
    ("Woodhaven Blvd", 40.73308, -73.869259, "M-R"),
    ("Bronx Park East", 40.848797, -73.868465, "2-5"),
    ("St Lawrence Ave", 40.8315, -73.867623, "6"),
    ("Pelham Pkwy", 40.857188, -73.867607, "5"),
    ("Allerton Ave", 40.865481, -73.867393, "2-5"),
    ("Elderts Lane", 40.69132, -73.867135, "J-Z"),
    ("Burke Ave", 40.871387, -73.867135, "2-5"),
    ("Gun Hill Rd", 40.877796, -73.866341, "2-5"),
    ("Grant Ave", 40.677107, -73.865376, "A"),
    ("219 St", 40.883767, -73.862736, "2-5"),
    ("103 St-Corona Plaza", 40.749858, -73.862672, "7"),
    ("63 Dr-Rego Park", 40.729869, -73.86161, "M-R"),
    ("Morris Park", 40.854137, -73.860977, "5"),
    ("E 177 St-Parkchester", 40.833246, -73.860805, "6"),
    ("225 St", 40.887887, -73.860505, "2-5"),
    ("Forest Pkwy", 40.692304, -73.860151, "J"),
    ("80 St-Hudson St", 40.679369, -73.85896, "A"),
    ("233 St", 40.893386, -73.857265, "2-5"),
    ("Pelham Pkwy", 40.858973, -73.855355, "5"),
    ("111 St", 40.75176, -73.855183, "7"),
    ("Nereid Ave-238 St", 40.898382, -73.854389, "2-5"),
    ("67 Ave", 40.726462, -73.85263, "M-R"),
    ("Woodhaven Blvd", 40.693866, -73.851568, "A"),
    ("88 St-Boyd Ave", 40.679857, -73.851492, "A"),
    ("Castle Hill Ave", 40.834255, -73.851222, "6"),
    ("Wakefield-241 St", 40.903085, -73.850591, "2"),
    ("Zerega Ave", 40.83646, -73.846471, "6"),
    ("Mets-Willets Point", 40.754622, -73.845625, "7"),
    ("Forest Hills-71 Ave", 40.721681, -73.84439, "E-F-M-R"),
    ("104 St", 40.695184, -73.844326, "A"),
    ("Rockaway Blvd", 40.680429, -73.843853, "A"),
    ("Westchester Sq-E Tremont Ave", 40.839892, -73.842952, "6"),
    ("Baychester Ave", 40.878656, -73.838596, "5"),
    ("104 St-Oxford Ave", 40.681745, -73.837631, "A"),
    ("Rockaway Park-Beach 116 St", 40.580454, -73.837459, "A-S"),
    ("75 Ave", 40.718477, -73.837223, "E-F"),
    ("Middletown Rd", 40.843635, -73.836687, "6"),
    ("111 St", 40.697405, -73.836354, "A"),
    ("Aqueduct-North Conduit Ave", 40.668234, -73.834058, "A"),
    ("Buhre Ave", 40.846817, -73.832545, "6"),
    ("Greenwood Ave-111 St", 40.684364, -73.832181, "A"),
    ("Union Tpke-Kew Gardens", 40.714444, -73.830979, "E-F"),
    ("Dyre Ave", 40.888244, -73.83085, "5"),
    ("Howard Beach-JFK Airport", 40.660476, -73.830301, "A"),
    ("121 St", 40.700536, -73.828382, "J-Z"),
    ("Pelham Bay Park", 40.852465, -73.828125, "6"),
    ("Beach 105 St", 40.583542, -73.82643, "A-S"),
    ("Lefferts Blvd", 40.685975, -73.824713, "A"),
    ("Van Wyck Blvd", 40.709174, -73.820593, "E"),
    ("Beach 98 St", 40.585514, -73.820143, "A-S"),
    ("Jamaica-Van Wyck", 40.702566, -73.816859, "E"),
    ("Broad Channel", 40.608693, -73.816068, "A-S"),
    ("Beach 90 St", 40.588032, -73.813684, "A-S"),
    ("Sutphin Blvd", 40.705416, -73.810562, "E"),
    ("Parsons Blvd", 40.707564, -73.803326, "F"),
    ("Jamaica Center-Parsons/Archer", 40.702131, -73.80111, "E-J-Z"),
    ("Beach 67 St", 40.590867, -73.797011, "A"),
    ("169 St", 40.710459, -73.7936, "F"),
    ("Beach 60 St", 40.592334, -73.788493, "A"),
    ("179 St", 40.712622, -73.783815, "F"),
    ("Beach 44 St", 40.593214, -73.776433, "A"),
    ("Beach 36 St", 40.595381, -73.768194, "A"),
    ("Beach 25 St", 40.600138, -73.76152, "A"),
    ("Far Rockaway-Mott Ave", 40.603983, -73.755383, "A"),
    ("Whitehall St-South Ferry", 40.703082, -74.012983, "1-R-W"),
]


def get_line_color(routes):
    """Return the color for a station based on its first route."""
    for route in routes.replace("-", " ").split():
        route = route.strip()
        if route in LINE_COLORS:
            return LINE_COLORS[route]
    return "#0039A6"  # default MTA blue


def create_subway_walk_map():
    """Create an interactive Folium map with 5-min walk radius circles."""

    # Center on Manhattan
    nyc_center = [40.7128, -74.0060]

    m = folium.Map(
        location=nyc_center,
        zoom_start=12,
        tiles="CartoDB positron",
        attr="Map tiles by CartoDB, Data by OpenStreetMap",
    )

    # Add walk-radius circles and station markers
    for name, lat, lon, routes in STATIONS:
        color = get_line_color(routes)
        routes_display = routes.replace("-", " ")

        # 5-minute walk radius circle
        Circle(
            location=[lat, lon],
            radius=WALK_RADIUS_METERS,
            color=color,
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.18,
            popup=Popup(
                f"<b>{name}</b><br>"
                f"Lines: {routes_display}<br>"
                f"5-min walk ({WALK_RADIUS_METERS}m radius)",
                max_width=250,
            ),
        ).add_to(m)

        # Station marker dot
        CircleMarker(
            location=[lat, lon],
            radius=3,
            color="white",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=1.0,
        ).add_to(m)

    # Legend
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px; left: 30px;
        z-index: 1000;
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 13px;
        line-height: 1.6;
        max-width: 200px;
    ">
        <b style="font-size:14px;">NYC Subway<br>5-Min Walk Radius</b>
        <hr style="margin:6px 0;">
        <div><span style="color:#EE352E;">&#9679;</span> 1 2 3</div>
        <div><span style="color:#00933C;">&#9679;</span> 4 5 6</div>
        <div><span style="color:#B933AD;">&#9679;</span> 7</div>
        <div><span style="color:#0039A6;">&#9679;</span> A C E</div>
        <div><span style="color:#FF6319;">&#9679;</span> B D F M</div>
        <div><span style="color:#6CBE45;">&#9679;</span> G</div>
        <div><span style="color:#996633;">&#9679;</span> J Z</div>
        <div><span style="color:#A7A9AC;">&#9679;</span> L</div>
        <div><span style="color:#FCCC0A;">&#9679;</span> N Q R W</div>
        <div><span style="color:#808183;">&#9679;</span> S</div>
        <hr style="margin:6px 0;">
        <div style="font-size:11px; color:#666;">
            Circle = 400m (~5 min walk)<br>
            {num_stations} stations shown
        </div>
    </div>
    """.format(num_stations=len(STATIONS))

    m.get_root().html.add_child(folium.Element(legend_html))

    # Title
    title_html = """
    <div style="
        position: fixed;
        top: 15px; left: 50%;
        transform: translateX(-50%);
        z-index: 1000;
        background: white;
        padding: 10px 24px;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-size: 18px;
        font-weight: bold;
    ">
        NYC Subway Stations &mdash; 5-Minute Walk Coverage
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    return m


if __name__ == "__main__":
    print(f"Generating map with {len(STATIONS)} subway stations...")
    print(f"Walk radius: {WALK_RADIUS_METERS}m (~5 minutes)")
    m = create_subway_walk_map()
    output_file = "subway_walk_map_5min.html"
    m.save(output_file)
    print(f"Map saved to {output_file}")
