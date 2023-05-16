import base64
import os
import pdb
import requests


def get_photo_url_or_format(vcard_photo_decl) -> tuple:
    """
    According to RFC 6350, the photo data is either in a URL, or encoded in base 64
    This function always returns the extension, and optionally the URL, if there is one.
    Extensions can (theoretically? the RFC doesn't say?) be any of the https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
    """

    encoding, extension, url = "", "", ""

    ENCODING_TAG = "ENCODING"

    vcard_declr_split = vcard_photo_decl.split(";")

    if (len(vcard_declr_split) == 2):
        # Line looks something like...
        # PHOTO;JPEG:http://example.com/photo.jpg <-- Case 1
        # or
        # PHOTO;MEDIATYPE=image/jpeg:http://example.com/photo.jpg <-- Case 2

        if ("=" in vcard_declr_split[1]): # Case 2
            mediatype, url = vcard_declr_split[1].split(":")
            _, extension = mediatype.split("/")

        else: # Case 1
            extension, url = vcard_declr_split[1].split(":")

    elif (len(vcard_declr_split) == 3):
        # Line looks something like one of the options below:
        # PHOTO;JPEG;ENCODING=BASE64:[base64-data]
        # PHOTO;TYPE=JPEG;VALUE=URI:http://example.com/photo.jpg
        # PHOTO;TYPE=JPEG;ENCODING=b:[base64-data]
        # PHOTO;ENCODING=BASE64;TYPE=JPEG:[base64-data]

        # Cases 2 and 3
        if (vcard_declr_split[1].startswith("TYPE")):
            extension = vcard_declr_split[1].split("=")

            if (vcard_declr_split[2].startswith("VALUE")):
                url = vcard_declr_split[2].split(":")[1]

        # Case 4
        elif (vcard_declr_split[1].startswith(ENCODING_TAG)):
            extension = (vcard_declr_split[2].split("="))[1].split(":")

        # Case 1
        elif (vcard_declr_split[2].startswith(ENCODING_TAG)):
            extension = vcard_declr_split[1]

        else:
            print(f"[ERROR] Unsupported photo block declaration, can't parse {vcard_photo_decl}")

    else:
        print(f"[ERROR] Unsupported photo block declaration. Too many semicolons! Can't parse {vcard_photo_decl}")


    return tuple([extension, url])


def extract_images_from_vcf(vcf_files_dir : str, output_images : str) -> None:

    for filename in os.listdir(vcf_files_dir):

        print(f"[DEBUG] Parsing {filename}")

        if filename.endswith(".vcf"):

            vcf_file_lines = []

            ## TODO: You need to parse the VCF file itself here
            
            with open(filename, 'r') as vcf_file_hndl:
                vcf_file_lines = vcf_file_hndl.readlines()

            # https://en.wikipedia.org/wiki/VCard#Properties

            for line_num, line_content in enumerate(vcf_file_lines):
                
                if line_content.startswith("PHOTO"):
                    extension, url = get_photo_url_or_format(line_content)

                    




