import typing
import os
import requests
import pdb
import base64

# Multimedia key constants
MULTIMEDIA_TAG_TAG_TYPE_KEY = "tag_type"
MULTIMEDIA_TAG_TAG_DATA_KEY = "tag_data"
MULTIMEDIA_TAG_TAG_URL_KEY = "tag_url"
MULTIMEDIA_TAG_TAG_MIME_TYPE_KEY = "tag_mime_type"

def get_advanced_key_names() -> typing.List:
    """
    Key names that might have multi-line content.
    """
    return ["KEY", "LOGO", "PHOTO", "SOUND"]

def get_multimedia_tag_list() -> typing.List:
    return [MULTIMEDIA_TAG_TAG_TYPE_KEY, MULTIMEDIA_TAG_TAG_DATA_KEY, MULTIMEDIA_TAG_TAG_URL_KEY, MULTIMEDIA_TAG_TAG_MIME_TYPE_KEY]

def extract_key_multimedia(contact : dict, base_filename : str) -> str:

    for key_name in get_advanced_key_names():

        if key_name in contact:

            # First determine the extension, either from the field directly or indirectly from the MIME type
            file_extension = ""

            if (MULTIMEDIA_TAG_TAG_TYPE_KEY in contact[key_name]):
                file_extension = contact[key_name][MULTIMEDIA_TAG_TAG_TYPE_KEY]

            else:
                if (MULTIMEDIA_TAG_TAG_MIME_TYPE_KEY in contact[key_name]):
                    file_extension = contact[key_name][MULTIMEDIA_TAG_TAG_MIME_TYPE_KEY].split("/")[1]

                else:
                    raise Exception(f"Couldn't determine extension, contents of {key_name} didn't match expected format")
                
            
            filename = (base_filename) + "." + file_extension

            isUrl = (MULTIMEDIA_TAG_TAG_URL_KEY in contact[key_name])
                
            decode_multimedia_data_field(contact[key_name][MULTIMEDIA_TAG_TAG_URL_KEY] if isUrl else contact[key_name][MULTIMEDIA_TAG_TAG_DATA_KEY], isUrl, filename)
            

def decode_multimedia_data_field(data_or_url : str, isUrl : bool, output_filename : str):
    
    with open(output_filename, 'wb') as file_handle:

        if isUrl:
            net_resp = requests.get(data_or_url, stream=True)

            if not net_resp.ok:
                raise Exception(f"Couldn't download media from URL '{data_or_url}', error='{net_resp}'")
            
            for block in net_resp.iter_content(1024):
                if not block:
                    break
                else:
                    file_handle.write(block)

        else:
            file_handle.write(base64.b64decode(data_or_url))

    



                