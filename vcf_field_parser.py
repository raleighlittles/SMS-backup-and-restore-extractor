import typing
import pdb

TAG_FIELD_SEPARATOR = ";"
KEY_VALUE_SEPARATOR = ":"
TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR = "="

import vcard_multimedia_helper

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

def return_name_tag_formatted(name_tag_field : tuple) -> str:

    name = ""

    for (tag_label, tag_value) in name_tag_field:
        name += tag_value

    return name
    
def parse_organization_tag(organization_line) -> tuple:
    """
    Parses the ORGANIZATION line. It can either be simple, eg. just one value
    or have subfields.
    """

    organzation_line_split = organization_line.split(";")

    if (len(organzation_line_split) == 1):
        return organization_line.split(KEY_VALUE_SEPARATOR)[1]
    
    else:
        # Comes from here https://www.itu.int/ITU-T/formal-language/itu-t/x/x520/2012/SelectedAttributeTypes.html
        sub_org_key_types = ["organization_name", "collective_organization_name", "organizational_unit_name"]

        return helper_match_subkey_types_and_values(sub_org_key_types, organzation_line_split)

def parse_related_tag(related_line) -> tuple:
    return helper_match_generic_label_and_types(related_line)

def parse_telephone_tag(telephone_textline) -> tuple:
    return helper_match_generic_label_and_types(telephone_textline)

def parse_multimedia_tag(multimedia_tag_line) -> tuple:
    """
    Parse the multimedia tag and return all of its available properties

    Multimedia tags have the same 6 different cases:

    <TAG-NAME>;<TAG-TYPE>:<TAG-DATA-URL>                            <-- Case 1

    <TAG-NAME>;<TAG-TYPE>;ENCODING=BASE64:[base64-data]             <-- Case 2
    <TAG-NAME>;ENCODING=BASE64;<TAG-TYPE>:[base64-data]             <-- Case 2a*

    <TAG-NAME>;TYPE=<TAG-TYPE>:<TAG-DATA-URL>                       <-- Case 3

    <TAG-NAME>;TYPE=<TAG-TYPE>;ENCODING=b:[base64-data]             <-- Case 4

    <TAG-NAME>;MEDIATYPE=<TAG-MIME-TYPE>:<TAG-DATA-URL>             <-- Case 5
    <TAG-NAME>:data:<TAG-MIME-TYPE>;base64,[base64-data]            <-- Case 6

    *Case 2a isn't actually documented in the wiki as a supported form, but the .vcf file I have uses it
    for the 'PHOTO' tag, so...
    """

    multimedia_tag_line_split = multimedia_tag_line.split(";")

    tag_type, tag_data, tag_url, tag_mime_type = "", "", "", ""

    if (len(multimedia_tag_line_split) == 3): # Case 2, 2a, or 4

        if (TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR in multimedia_tag_line_split[1]):
            if (multimedia_tag_line_split[1] == "ENCODING=BASE64"): # Case 2a
                tag_type, tag_data = multimedia_tag_line_split[2].split(KEY_VALUE_SEPARATOR)

            else: # Case 4
                tag_type = multimedia_tag_line_split[1].split(TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR)[1]
                tag_data = multimedia_tag_line_split[2].split(KEY_VALUE_SEPARATOR)[1]

        else: # Case 2
            tag_type = (multimedia_tag_line_split[2].split(KEY_VALUE_SEPARATOR))[0]
            tag_data = multimedia_tag_line_split[-1].split(KEY_VALUE_SEPARATOR)[1]

    elif (len(multimedia_tag_line_split) == 2): # Case 1, 3, 5, or 6

        if (multimedia_tag_line_split[1].startswith("TYPE")): # Case 3

            multimedia_type_decl_split = multimedia_tag_line_split[1].split(KEY_VALUE_SEPARATOR)
            tag_type = multimedia_type_decl_split[0].split(TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR)[1]
            tag_url = multimedia_type_decl_split[1]

        elif (multimedia_tag_line_split[1].startswith("MEDIATYPE")): # Case 5
            multimedia_mediatype_decl_split = multimedia_tag_line_split[1].split(KEY_VALUE_SEPARATOR)
            tag_mime_type = multimedia_mediatype_decl_split[0].split(TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR)[1]
            tag_url = multimedia_mediatype_decl_split[1]

        elif (multimedia_tag_line_split[1].startswith("base64")): # Case 6
            tag_mime_type = multimedia_tag_line_split[0].split(KEY_VALUE_SEPARATOR)[-1]
            tag_data = multimedia_tag_line_split[1].split(",")[1]

        else: # Must be case 1
            tag_type_and_url_split = multimedia_tag_line_split[1].split(KEY_VALUE_SEPARATOR)
            tag_type = tag_type_and_url_split[0]
            tag_url = ":".join(tag_type_and_url_split[1:])

    else:
        raise Exception(f"[ERROR] Can't parse multimedia tag: '{multimedia_tag_line}'")
    
    return helper_match_subkey_types_and_values(vcard_multimedia_helper.get_multimedia_tag_list(), [tag_type, tag_data, tag_url, tag_mime_type], contains_tag_name=False)


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
