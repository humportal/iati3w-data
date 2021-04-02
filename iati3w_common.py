""" Common variables and functions for all scripts

"""

import json, re, string

from hxl.datatypes import is_empty

#
# Keys for classifying things
#
ROLES = ["implementing", "programming", "funding",]
SCOPES = ["local", "regional", "international", "unknown",]
SECTOR_TYPES = ["dac", "humanitarian",]
LOCATION_TYPES = ["admin1", "admin2", "unclassified",]


#
# Utility functions
#

def add_unique (element, l, key=None):
    """ Add an element to a list if it's not already in a list and isn't falsey
    If key is not None, assume the value to add is a dict and use the key for uniqueness.
    """

    if not element:
        # don't add if the item is falsely
        pass
    elif key is None:
        # if there's no key, assume a string or something that can be forced to one
        s = str(element)
        if not is_empty(s) and not s in l:
            l.append(element)
    else:
        s = str(element.get(key, ""))
        if not is_empty(s) and not s in [str(v1.get(key, None)) for v1 in l]:
            l.append(element)

    return l

def normalise_string (s):
    """ Normalise whitespace in a string.
    Preserve character case and punctuation

    """
    if not s:
        return None
    else:
        return re.sub(r'\s+', ' ', s.strip())

def make_token (s):
    """ Create a lookup token from a string.
    Normalise space, convert to lowercase, and remove punctuation

    """
    return re.sub(r'\W+', ' ', s).lower().strip()

def fix_location (s):
    if s:
        return string.capwords(normalise_string(s))
    else:
        return ""

def flatten (map, excludes=[]):
    """ Flatten a dict of lists into a single list, with duplicates removed """
    result = []
    for key in map:
        if key in excludes:
            continue
        for s in map[key]:
            if not s in result:
                result.append(s)
    return result


#
# Look up and manage JSON datasets
#

datasets_loaded = {}

def get_dataset (path):
    global datasets_loaded
    if not path in datasets_loaded:
        with open(path, "r") as input:
            datasets_loaded[path] = json.load(input)
    return datasets_loaded[path]


#
# Lookup tables (transformed from JSON maps)
#

lookup_tables_loaded = {}

def get_lookup_table (path):
    """ Make a lookup table, including synonyms
    Keys will be tokenized

    """
    global lookup_tables_loaded
    if not path in lookup_tables_loaded:
        result = {}
        map = get_dataset(path)
        for key, info in map.items():
            result[make_token(key)] = info
            if "name" in info:
                result.setdefault(make_token(info["name"]), info)
            for synonym in info.get("synonyms", []):
                result.setdefault(make_token(synonym), info)
        lookup_tables_loaded[path] = result
    return lookup_tables_loaded[path]


def lookup_org (name):
    """ Look up an org by name """
    if name is None:
        return None
    name = str(name)
    if is_empty(name):
        return None
    token = make_token(name)
    table = get_lookup_table("inputs/org-map.json")
    if token in table:
        return table[token]
    else:
        import sys
        print("Failed lookup |{}|".format(token), file=sys.stderr)
        return {
            "name": normalise_string(name),
            "scope": "unknown",
        }
    

#
# Special lookup tables for locations (which are hierarchical)
#

location_lookup_table = None

def get_location_lookup_table ():
    """ Load and transform the location table if needed, then return """
    global location_lookup_table

    if location_lookup_table is None:
        location_lookup_table = {}

        map = get_dataset("inputs/location-map.json")

        for name1, info1 in map.items():

            # add the region
            token1 = make_token(name1)
            location_lookup_table[token1] = info1

            # add the districts
            for name2, info2 in info1.get("admin2", {}).items():
                token2 = make_token(name2)
                info2["admin1"] = info1["name"]
                location_lookup_table.setdefault(token2, info2) # only if doesn't exist

                # add the unclassified locations
                for name3, info3 in info2.get("unclassified", {}).items():
                    token3 = make_token(name3)
                    info3["admin1"] = info1["name"]
                    info3["admin2"] = info2["name"]
                    location_lookup_table.setdefault(token3, info3) # only if doesn't exist

                    # add the synonyms for unclassified locations
                    for name4 in info3.get("synonyms", []):
                        location_lookup_table.setdefault(make_token(name4), info3) # only if doesn't exist

                # add the synonyms for the districts
                for name3 in info2.get("synonyms", []):
                    location_lookup_table.setdefault(make_token(name3), info2) # only if doesn't exist

            # add the synonyms for the regions
            for name2 in info1.get("synonyms", []):
                location_lookup_table.setdefault(make_token(name2), info1) # only if doesn't exist

    return location_lookup_table


def lookup_location (name, loctype="unclassified"):
    """ Look up a location name and see what we can do with it """

    # we don't care about empty names
    if is_empty(name):
        return None

    # return the lookup if it exists, or just a cleaned-up name
    return get_location_lookup_table().get(make_token(name), {
        "level": loctype,
        "name": normalise_string(name),
    });

