""" Create a JSON index with information about each location in the activities

Usage:

python3 index-locations.py output/activities.json > output/location-index.json

Started 2021-03 by David Megginson

"""

import json, sys

from iati3w_common import * # common variables and functions

index = {}
""" The index that we will export as JSON """


#
# Check command-line usage
#
if len(sys.argv) != 2:
    print("Usage: {} <activity-file>".format(sys.argv[0]), file=sys.stderr)
    sys.exit(2)

#
# Loop through all the activities in the JSON file specified
#
with open(sys.argv[1], "r") as input:

    activities = json.load(input)
    for activity in activities:

        #
        # Loop through the subnational location types
        #
        for loctype in LOCATION_TYPES:

            # Add the type if it's not in the index yet
            index.setdefault(loctype, {})

            #
            # Loop through each location of each type
            #
            for location in activity["locations"].get(loctype, []):

                # Skip blank locations
                if not location:
                    continue

                # Clean whitespace
                location = location.strip()

                # Add a default record if this is the first time we've seen the location
                index[loctype].setdefault(location, {
                    "activities": [],
                    "orgs": {},
                    "sectors": {},
                })

                # This is the location index entry we'll be working on
                entry = index[loctype][location]

                # Add this activity
                entry["activities"].append({
                    "identifier": activity["identifier"],
                    "title": activity["title"],
                    "source": activity["source"],
                })

                # Add the activity orgs (don't track roles here)
                for role in ROLES:
                    for org in activity["orgs"].get(role, []):
                        if not org:
                            continue
                        org = org.strip()
                        entry["orgs"].setdefault(org, 0)
                        entry["orgs"][org] += 1

                # Add the sectors for each type
                for type in SECTOR_TYPES:
                    entry["sectors"].setdefault(type, {})
                    for sector in activity["sectors"].get(type, []):
                        if not sector:
                            continue
                        sector = sector.strip()
                        entry["sectors"][type].setdefault(sector, 0)
                        entry["sectors"][type][sector] += 1
                        

# Dump the index as JSON to stdout
print(json.dumps(index, indent=4))

# end

