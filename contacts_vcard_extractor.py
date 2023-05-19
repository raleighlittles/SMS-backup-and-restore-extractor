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


# v2.1 and v3.0 require the first, v4.0 requires the second.
# However, I've seen some created vCard files that have neither...
CONTACT_ID_KEY, CONTACT_SECONDARY_ID_KEY = "N", "FN"

def parse_vcard_line(file_line : str) -> dict:
    """
    Takes the line of a VCF file, and extracts the property and value, returning it
    """

    print(f"[DEBUG] Parsing line | {file_line}")

    contact = dict()

    # This only works because none of the 'simple' key names is a substring of any other key name
    if any([file_line.startswith(key) for key in vcf_field_parser.SIMPLE_KEYS]):

        file_line_split = file_line.split(":")

        key = file_line_split[0]

        # NOTE-1: Needs to be able to handle multiple colons in the key, in the case of a URL
        # ie "AGENT:http://mi6.gov.uk/007" has 3 colons, but we want only 2 groups
        value = "".join(file_line_split[1::])
        contact[key] = value

    # With the simple keys out of the way, parse the remaining keys
    else:
        if file_line.startswith("ADR"):
            contact["ADR"] = vcf_field_parser.parse_address_tag(file_line)


        elif file_line.startswith("CATEGORIES"):
            contact["CATEGORIES"] = vcf_field_parser.parse_categories_tag(file_line)

        elif file_line.startswith("CLIENTPIDMAP"):
            contact["CLIENTPIDMAP"] = vcf_field_parser.parse_clientpidmap_tag(file_line)

        elif file_line.startswith("EMAIL"):
            contact["EMAIL"] = vcf_field_parser.parse_email_tag(file_line)
        
        elif file_line.startswith("GEO"):
            contact["GEO"] = vcf_field_parser.parse_geo_tag(file_line)

        elif file_line.startswith("IMPP"):
            contact["IMPP"] = vcf_field_parser.parse_instant_messenger_handle_tag(file_line)

        elif file_line.startswith("LABEL"):
            contact["LABEL"] = vcf_field_parser.parse_mailing_label_tag(file_line)
            
        elif file_line.startswith("MEMBER"):
            contact["MEMBER"] = vcf_field_parser.parse_member_tag(file_line)

        elif file_line.startswith("N"):
            contact["N"] = vcf_field_parser.parse_name_tag(file_line)

        elif file_line.startswith("ORG"):
            contact["ORG"] = vcf_field_parser.parse_organization_tag(file_line)

        elif file_line.startswith("RELATED"):
            contact["RELATED"] = vcf_field_parser.parse_related_tag(file_line)

        elif file_line.startswith("TEL"):
            contact["TEL"] = vcf_field_parser.parse_telephone_tag(file_line)

        elif file_line.startswith("UID"):
            contact["UID"] = vcf_field_parser.parse_uuid_tag(file_line)

        # The advanced key types
        else:
            multimedia_keys = vcard_multimedia_helper.get_advanced_key_names()

            for key in multimedia_keys:

                if file_line.startswith(key):
                    # Remove the actual tag name from the string that gets sent for parsing
                    # tag_info_field_1, tag_info_field_2 = vcf_field_parser.parse_multimedia_tag(file_line[len(key):])
                    # contact[key] = dict({tag_info_field_1, tag_info_field_2})
                    contact[key] = vcf_field_parser.parse_multimedia_tag(file_line[len(key):])
            
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