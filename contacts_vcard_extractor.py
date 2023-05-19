import base64
import os
import pdb
import sys
import requests
import os
import string
import random
import typing

# local
import vcf_field_parser
import vcard_multimedia_helper


# These are properties that are declared with just a simple key-value pair, and no additional processing, like so:
# ANNIVERSARY:19901021
# FN:Dr. John Doe
# GENDER:F
SIMPLE_KEYS = ["AGENT", "ANNIVERSARY", "BDAY", "CALADRURI", "CALURI", "CLASS", "FBURL", "FN", "GENDER", "KIND", "LANG", "MAILER", "NICKNAME", "NOTE", "PRODID", "PROFILE", "REV", "ROLE", "SORT-STRING", "SOURCE", "TITLE", "TZ", "URL", "VERSION", "XML"]

# These are keys that require some processing
INTERMEDIATE_KEYS = ["ADR", "CATEGORIES", "CLIENTPIDMAP", "EMAIL", "GEO", "IMPP", "LABEL", "MEMBER", "N", "ORG", "RELATED", "TEL", "UID"]

# v2.1 and v3.0 require the first, v4.0 requires the second.
# However, I've seen some created vCard files that have neither...
CONTACT_ID_KEY, CONTACT_SECONDARY_ID_KEY = "N", "FN"

def parse_vcard_line(file_line : str) -> dict:
    """
    Takes the line of a VCF file, and extracts the property and value, returning it
    """

    print(f"[DEBUG] Parsing line | {file_line}")

    # These are properties that are declared with just a simple key-value pair, and no additional processing, like so:
    # ANNIVERSARY:19901021
    # FN:Dr. John Doe
    # GENDER:F
    # simple_keys = ["AGENT", "ANNIVERSARY", "BDAY", "CALADRURI", "CALURI", "CLASS", "FBURL", "FN", "GENDER", "KIND", "LANG", "MAILER", "NICKNAME", "NOTE", "PRODID", "PROFILE", "REV", "ROLE", "SORT-STRING", "SOURCE", "TITLE", "TZ", "URL", "VERSION", "XML"]

    contact = dict()

    # This only works because none of the 'simple' key names is a substring of any other key name
    if any([file_line.startswith(key) for key in SIMPLE_KEYS]):

        file_line_split = file_line.split(":")

        key = file_line_split[0]

        # NOTE-1: Needs to be able to handle multiple colons in the key, in the case of a URL
        # ie "AGENT:http://mi6.gov.uk/007" has 3 colons, but we want only 2 groups
        value = "".join(file_line_split[1::])
        contact[key] = value

    # With the simple keys out of the way, parse the remaining keys
    else:
        if file_line.startswith("ADR"):
            addr_type, address = vcf_field_parser.parse_address_tag(file_line)
            contact["ADR"] = dict({addr_type : address})

        elif file_line.startswith("CATEGORIES"):
            # Split the following:
            # CATEGORIES:swimmer,biker
            # into
            # ["biker", "swimmer"]
            user_categories : typing.List = sorted(("".join(file_line.split(":")[1::])).split(","))
            contact["CATEGORIES"] = user_categories

        elif file_line.startswith("CLIENTPIDMAP"):
            pid_source_id, urn = vcf_field_parser.parse_clientpidmap_tag(file_line)
            contact["CLIENTPIDMAP"] = dict({pid_source_id : urn})

        elif file_line.startswith("EMAIL"):
            email_type, email_address = vcf_field_parser.parse_email_tag(file_line)
            contact["EMAIL"] = dict({ email_type : email_address })
        
        elif file_line.startswith("GEO"):
            specifier_1, coordinate_1, specifier_2, coordinate_2 = vcf_field_parser.parse_geo_tag(file_line)
            contact["GEO"] = dict({specifier_1 : coordinate_1, specifier_2: coordinate_2})

        elif file_line.startswith("IMPP"):
            key, impp_type, impp_handle = file_line.split(":")
            contact[key] = dict({impp_type : impp_handle})

        elif file_line.startswith("LABEL"):
            label_type, label_data = vcf_field_parser.parse_mailing_label_tag(file_line)
            contact["LABEL"] = dict({ label_type : label_data })
            
        elif file_line.startswith("MEMBER"):
            file_line_split = file_line.split(":")
            key, member_id_type = file_line_split[0], file_line_split[1]
            member_id_value = ":".join(file_line_split[2:])
            contact[key] = dict({ member_id_type : member_id_value })

        elif file_line.startswith("N"):
            name_fields = vcf_field_parser.parse_name_tag(file_line)
            contact["N"] = name_fields

        elif file_line.startswith("ORG"):
            org_fields = vcf_field_parser.parse_organization_tag(file_line)
            contact["ORG"] = org_fields

        elif file_line.startswith("RELATED"):
            related_type, related_data = vcf_field_parser.parse_related_tag(file_line)
            contact["RELATED"] = dict({ related_type : related_data })

        elif file_line.startswith("TEL"):
            telephone_type, telephone_number = vcf_field_parser.parse_telephone_tag(file_line)
            contact["TEL"] = dict({ telephone_type : telephone_number })

        elif file_line.startswith("UID"):
            uid_line_split = file_line.split(":")
            uid_type = uid_line_split[1]
            uid_data = ":".join(uid_line_split[2:])
            contact[uid_line_split[0]] = dict({uid_type : uid_data })

        # The advanced key types
        else:
            multimedia_keys = vcard_multimedia_helper.get_advanced_key_names()

            for key in multimedia_keys:

                if file_line.startswith(key):
                    # Remove the actual tag name from the string that gets sent for parsing
                    tag_info_field_1, tag_info_field_2 = vcf_field_parser.parse_multimedia_tag(file_line[len(key):])

                    contact[key] = dict({tag_info_field_1, tag_info_field_2})
            
    return contact


def generate_multimedia_of_contact(contact : dict, output_dir : str):

    # The generated media needs something in the filename that is unique and identifiable to the user

    unique_contact_field = ""

    if CONTACT_ID_KEY in contact:
        unique_contact_field = vcf_field_parser.return_name_tag_formatted(contact[CONTACT_ID_KEY])

    elif CONTACT_SECONDARY_ID_KEY in contact:
        unique_contact_field = contact[CONTACT_SECONDARY_ID_KEY]

    else:
        # This should never happen (it violates the specification), yet a few of my Dad's VCF files somehow have contacts with no name field
        unique_contact_field = "".join(random.sample(string.ascii_letters, 10))
        
    # A unique prefix to the filename so that there's no conflicts
    base_filename = unique_contact_field

    vcard_multimedia_helper.extract_key_multimedia(contact, os.path.join(output_dir, base_filename))


def parse_contacts_from_vcf_files(vcf_files_dir : str, output_media_dir : str) -> None:

    all_contacts = []

    for filename in os.listdir(vcf_files_dir):

        num_contacts_in_file = 0

        print(f"[DEBUG] Parsing {filename}")

        if filename.endswith(".vcf"):

            vcf_file_lines = []
            
            with open(os.path.join(vcf_files_dir, filename), 'r') as vcf_file_hndl:
                vcf_file_lines = vcf_file_hndl.readlines()

            curr_contact = dict()
            currently_in_contact = False
            has_multimedia = False

            line_num = 0

            #for line_num, line_content in enumerate(vcf_file_lines):
            while line_num < len(vcf_file_lines):

                line_content = vcf_file_lines[line_num]

                if (line_content.strip() == "BEGIN:VCARD"):
                    if (currently_in_contact):
                        print(f"[ERROR] Missing end tag, at line {line_num}")
                        sys.exit(1)

                    else:
                        currently_in_contact = True

                elif (line_content.strip() == "END:VCARD"):
                    currently_in_contact = False
                    all_contacts.append(curr_contact)
                    num_contacts_in_file += 1
                    print(f"[DEBUG] End of Vcard reached! New contact added from file, # of contacts is now {num_contacts_in_file} (Total) {len(all_contacts)}")
                    if has_multimedia:
                        generate_multimedia_of_contact(curr_contact, output_media_dir)
                    
                    # Reset things for the next contact
                    has_multimedia = False
                    curr_contact = dict()

                else:
                    # TODO: I'd ideally, like NOT to have to rearrange the input file just to make parsing easier...
                    # Check the "advanced" case first, then the simple case
                    if (any([line_content.startswith(key) for key in vcard_multimedia_helper.get_advanced_key_names()])):

                        has_multimedia = True

                        multimedia_tag_line = line_content.strip()
                        next_line_num = line_num + 1

                        while (":" not in vcf_file_lines[next_line_num]):

                            multimedia_tag_line += vcf_file_lines[next_line_num].strip()

                            if ((vcf_file_lines[next_line_num]) == ""): # Empty line means done parsing
                                break

                            next_line_num += 1


                        new_contact_info = parse_vcard_line(multimedia_tag_line.strip())
                        curr_contact.update(new_contact_info)
                        line_num = next_line_num

                        continue

                    else:
                        new_contact_info = parse_vcard_line(line_content.strip())

                        if new_contact_info is not None:
                            curr_contact.update(new_contact_info)
                        else:
                            raise Exception(f"[ERROR] Couldn't parse file line #{line_num} : '{line_content}")

                # Always increment!
                line_num += 1