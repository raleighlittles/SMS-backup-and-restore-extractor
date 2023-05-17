import typing

def parse_address_tag(address_line) -> tuple:

    # Split the string on semi-colons, then iterate backwards until you reach an empty string,
    # thus giving you the address

    addr_line_split = address_line.split(";")

    address_components_reverse = []

    for elem in addr_line_split[::-1]:
        if (elem == ""):
            break
        else:
            address_components_reverse.append(elem)

    address = " ".join(address_components_reverse[::-1])

    address_type = ""

    # Note: each address line can only have one address, and thus, at most one 'type' of address
    if (addr_line_split[1].startswith("TYPE")):
        address_type = (addr_line_split[1].split("=")[1]).split(":")[0]

    else:
        address_type = addr_line_split[1]

    return tuple([address_type, address])


def parse_clientpidmap_tag(clientpidmap_line) -> tuple:
    
    clientpidmap_split = clientpidmap_line.split(";")
    urn = clientpidmap_split[1]
    pid_source_identifier = clientpidmap_split[0].split(":")[1]

    return tuple([pid_source_identifier, urn])

def parse_email_tag(email_line) -> tuple:
    return helper_match_generic_label_and_types(email_line)

def parse_geo_tag(geo_line) -> tuple:

    geo_line_split = geo_line.split(":")

    lat, lon = "", ""

    if (len(geo_line_split) == 2): # Using VCARD version 2 or 3 format
        lat, lon = geo_line_split[1].split(";")

    elif (len(geo_line_split) == 3): # Using VCARD version 4 format
        lat, lon = geo_line_split[2].split(",")

    return tuple(["latitude", lat, "longitude", lon])
        
def parse_encryption_key_tag(key_line) -> tuple:
    pass

def parse_mailing_label_tag(label_line) -> tuple:
    return helper_match_generic_label_and_types(label_line)
    

def parse_name_tag(name_line) -> tuple:

    name_line_split = name_line.split(";")

    subname_key_types = ["family_name", "given_name", "additional_middle_names", "honorific_prefixes", "honorific_suffixes"]

    # Don't include the subname if it's empty!
    #return tuple([subname for subname in zip(subname_key_types, name_line_split) if subname[1] != ""])

    return helper_match_subkey_types_and_values(subname_key_types, name_line_split)
    
def parse_organization_tag(organzation_line) -> tuple:

    organzation_line_split = organzation_line.split(";")

    # Comes from here https://www.itu.int/ITU-T/formal-language/itu-t/x/x520/2012/SelectedAttributeTypes.html
    sub_org_key_types = ["organization_name", "collective_organization_name", "organizational_unit_name"]

    return helper_match_subkey_types_and_values(sub_org_key_types, organzation_line_split)

def parse_related_tag(related_line) -> tuple:
    return helper_match_generic_label_and_types(related_line)

def parse_telephone_tag(telephone_textline) -> tuple:
    return helper_match_generic_label_and_types(telephone_textline)

def parse_multimedia_tag(multimedia_tag_line) -> tuple:
    """
    Returns 
    """

## Helper methods

def helper_match_subkey_types_and_values(subkey_names : typing.List, values : typing.List, contains_tag_name = True) -> tuple:

    if (contains_tag_name):
        # Strip the actual tag name
        values[0] = values[0].split(":")[1]

    if (len(subkey_names) != len(values)):
        raise Exception(f"Contents of line don't match specifications! Only {len(values)} subfields found, but {len(subkey_names)} are required")
    return tuple([subtype for subtype in zip(subkey_names, values) if subtype[1] != ""])

def helper_match_generic_label_and_types(text_line) -> tuple:
    text_line_split = text_line.split(":")
    data = ":".join(text_line_split[1::])

    data_type = ""

    if "=" in text_line_split[0]:
        data_type = text_line_split[0].split("=")[1]

    else:
        data_type = text_line_split[0].split(";")[1]

    return tuple([data_type, data])
