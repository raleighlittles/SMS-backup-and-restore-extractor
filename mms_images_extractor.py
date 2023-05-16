import base64
import hashlib
import lxml.etree
import os
import random
import string
import typing


def reconstruct_sms_images(sms_xml_dir : dir, output_images_dir : str) -> None:

    orig_files_count = 0

    for filename in os.listdir(sms_xml_dir):
        if filename.endswith(".xml") and filename.startswith("sms"):
            parser = lxml.etree.XMLParser(recover=True)
            root = lxml.etree.parse(os.path.join(
                sms_xml_dir, filename), parser=parser).getroot()
            b64_results_list = []

            # '*' technically isn't a valid MIME type but for some reason this application uses it
            # https://www.iana.org/assignments/media-types/media-types.xhtml#image
            image_ext_types = ["avif", "bmp", "gif", "heic", "heif", "jpeg", "tiff", "png", "webp", "*"]
            xpath_search_str_base = ".//part[@ct='image/"

            for ext in image_ext_types:
                # see https://www.synctech.com.au/sms-backup-restore/fields-in-xml-backup-files/ for a description of the XML fields
                xpath_search_expr = xpath_search_str_base + ext + "']"
                b64_results_list.append(
                    [(b.attrib['data'], b.attrib['cl'], ext) for b in root.findall(xpath_search_expr)])

            for result_type in b64_results_list:
                for (data, content_location, ext) in result_type:
                    # If it's empty, just assign it a random 10-letter string (so that it doesn't conflict with other unnamed files)
                    if content_location == "" or content_location == "null":
                        content_location = "".join(random.sample(string.ascii_letters, 10)) + "." + ext

                    # this ensures the filename has an extension, if it doesn't (likely) have one
                    output_filename = (content_location if '.' in content_location else (content_location + "." + ext))
                    with open(os.path.join(output_images_dir, output_filename), 'wb') as f:
                        f.write(base64.b64decode(data))
                        orig_files_count += 1

    print(f"{orig_files_count} files created... Automatically removing duplicates")

    duplicate_files_count = 0
    # Once files are created, go through and delete duplicates
    unique_files_hash_list = []
    for filename in os.listdir(output_images_dir):
        file_path = os.path.join(output_images_dir, filename)
        if os.path.isfile(file_path):
            file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
            if file_hash not in unique_files_hash_list:
                unique_files_hash_list.append(file_hash)

            else:
                os.remove(file_path)
                duplicate_files_count += 1
        else:
            print("ERROR: Subdirectory found in output directory")
            return 1

    print(f"{duplicate_files_count} files removed")
