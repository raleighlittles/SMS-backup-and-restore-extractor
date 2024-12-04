import typing

# locals
from . import vcard_multimedia_helper

TAG_FIELD_SEPARATOR = ";"
KEY_VALUE_SEPARATOR = ":"
TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR = "="

# These are properties that are declared with just a simple key-value pair, and no additional processing, like so:
# ANNIVERSARY:19901021
# FN:Dr. John Doe
# GENDER:F
SIMPLE_KEYS = ["AGENT", "ANNIVERSARY", "BDAY", "CALADRURI", "CALURI", "CLASS", "FBURL", "FN", "GENDER", "KIND", "LANG", "MAILER", "NICKNAME", "NOTE", "PRODID", "PROFILE", "REV", "ROLE", "SORT-STRING", "SOURCE", "TITLE", "TZ", "URL", "VERSION", "XML"]

def parse_simple_tag(file_line) -> str:

    # NOTE-1: Needs to be able to handle multiple colons in the key, in the case of a URL
    # ie "AGENT:http://mi6.gov.uk/007" has 3 colons, but we want only 2 groups

    return "".join(file_line.split(KEY_VALUE_SEPARATOR)[1::])


def parse_address_tag(address_line) -> dict:

    # Split the string on semi-colons, then iterate backwards until you reach the label
    # thus giving you the address.
    # Some fields might be empty, for example an address could contain a street and a state, but no city or zip code

    addr_line_split = address_line.split(TAG_FIELD_SEPARATOR)

    address_components_reverse = []

    for elem in addr_line_split[::-1]:
        if (KEY_VALUE_SEPARATOR in elem):
            break
        else:
            address_components_reverse.append(elem)

    address = " ".join(address_components_reverse[::-1])

    address_type = ""

    # Note: each address line can only have one address, and thus, at most one 'type' of address
    if (addr_line_split[1].startswith("TYPE")):
        address_type = (addr_line_split[1].split(TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR)[1]).split(KEY_VALUE_SEPARATOR)[0]

    else:
        address_type = addr_line_split[1]

    return dict({address_type: address.strip()})


def parse_categories_tag(category_line) -> tuple:
    """
    Split the following:
        CATEGORIES:swimmer,biker
          into
        ["biker", "swimmer"]
    """
    return sorted(("".join(category_line.split(KEY_VALUE_SEPARATOR)[1::])).split(","))


def parse_clientpidmap_tag(clientpidmap_line) -> dict:
    
    clientpidmap_split = clientpidmap_line.split(TAG_FIELD_SEPARATOR)
    urn = clientpidmap_split[1]
    pid_source_identifier = clientpidmap_split[0].split(KEY_VALUE_SEPARATOR)[1]

    return dict({pid_source_identifier : urn})


def parse_email_tag(email_line) -> dict:
    return helper_match_generic_label_and_types(email_line)


def parse_geo_tag(geo_line) -> dict:

    geo_line_split = geo_line.split(":")

    lat, lon = "", ""

    if (len(geo_line_split) == 2): # Using VCARD version 2 or 3 format
        lat, lon = geo_line_split[1].split(TAG_FIELD_SEPARATOR)

    elif (len(geo_line_split) == 3): # Using VCARD version 4 format
        lat, lon = geo_line_split[2].split(",")

    return dict({"latitude" : lat, "longitude": lon})
        

def parse_instant_messenger_handle_tag(impp_line) -> dict:

    _, impp_type, impp_handle = impp_line.split(KEY_VALUE_SEPARATOR)

    return dict({"type": impp_type, "handle": impp_handle})


def parse_mailing_label_tag(label_line) -> dict:
    return helper_match_generic_label_and_types(label_line)
    

def parse_member_tag(member_line) -> dict:

    member_line_split = member_line.split(KEY_VALUE_SEPARATOR)
    _, member_id_type = member_line_split[0], member_line_split[1]
    member_id_value = KEY_VALUE_SEPARATOR.join(member_line_split[2:])

    return dict({ member_id_type : member_id_value })


def parse_name_tag(name_line) -> tuple:

    name_line_split = name_line.split(TAG_FIELD_SEPARATOR)

    subname_key_types = ["family_name", "given_name", "additional_middle_names", "honorific_prefixes", "honorific_suffixes"]

    return helper_match_subkey_types_and_values(subname_key_types, name_line_split)


def return_name_tag_formatted(name_tag_field : dict) -> str:
    """
    Takes in a name label, and returns all fields from it
    so: {'family_name': 'Kennedy', 'given_name': 'John', 'additional_middle_names': 'F'}

    would return:

    'KennedyJohnF'
    """

    name = ""

    for name_label in name_tag_field:
        name += name_tag_field[name_label]

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


def parse_related_tag(related_line) -> dict:
    return helper_match_generic_label_and_types(related_line)


def parse_telephone_tag(telephone_textline) -> dict:
    return helper_match_generic_label_and_types(telephone_textline)


def parse_uuid_tag(uuid_textline) -> dict:

    uid_line_split = uuid_textline.split(KEY_VALUE_SEPARATOR)
    uid_type = uid_line_split[1]
    uid_data = KEY_VALUE_SEPARATOR.join(uid_line_split[2:])
    return dict({uid_type : uid_data })


def parse_multimedia_tag(multimedia_tag_line) -> tuple:
    """
    Parse the multimedia tag and return both of its properties

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

## --------------
## Helper methods
## --------------

def helper_match_subkey_types_and_values(subkey_names : typing.List, values : typing.List, contains_tag_name = True) -> tuple:
    """
    Given a set of X labels, and a set of Y values, this matches them into a dictionary:
    { X[0] : Y[0], X[1] : Y[1], ... }
    """

    if (contains_tag_name):
        # Strip the actual tag name
        values[0] = values[0].split(":")[1]

    if (len(subkey_names) != len(values)):
        raise Exception(f"Contents of line don't match specifications! Only {len(values)} subfields found, but {len(subkey_names)} are required")
    
    label_and_data_pairs =  tuple([subtype for subtype in zip(subkey_names, values) if subtype[1] != ""])

    result_dict = dict()
    
    for idx in range(0, len(label_and_data_pairs)):
        result_dict.update({label_and_data_pairs[idx][0] : label_and_data_pairs[idx][1]})

    return result_dict


def helper_match_generic_label_and_types(text_line) -> dict:
    """
    Convenience method for matching lines of the form:
    <KEY>;TYPE=<KEY_TYPE>:<KEY_DATA>
    """

    text_line_split = text_line.split(":")
    data = KEY_VALUE_SEPARATOR.join(text_line_split[1::])

    data_type = ""

    if TYPE_ASSIGNMENT_OR_LABEL_SEPARATOR in text_line_split[0]:
        data_type = text_line_split[0].split("=")[1]

    else:
        data_type = text_line_split[0].split(";")[1]

    return dict({data_type: data})
