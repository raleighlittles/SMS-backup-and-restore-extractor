import base64
import datetime
import hashlib
import lxml.etree
import os
import random
import string
import sys
import time


def get_datetime_from_epoch_milliseconds(epoch_milliseconds: str) -> str:
    """
    Converts the epoch time in milliseconds to a human-readable date and time string
    """
    return datetime.datetime.fromtimestamp(int(epoch_milliseconds) / 1000).strftime('%Y%m%d-%H%M%S')


def reconstruct_sms_images(sms_xml_dir: dir, output_images_dir: str) -> None:

    if not os.path.exists(output_images_dir):
        os.makedirs(output_images_dir, exist_ok=False)

    start_time = time.time()

    orig_files_count = 0

    for filename in os.listdir(sms_xml_dir):

        if filename.endswith(".xml") and filename.startswith("sms"):

            parser = lxml.etree.XMLParser(recover=True)

            root = lxml.etree.parse(os.path.join(
                sms_xml_dir, filename), parser=parser).getroot()

            if root is None:
                print(f"ERROR: {
                      filename} cannot be parsed as an XML document. Verify it's a valid XML file")
                sys.exit(1)
            else:
                b64_results_list = []

                # '*' technically isn't a valid MIME type but for some reason this application uses it
                # https://www.iana.org/assignments/media-types/media-types.xhtml#image
                image_ext_types = ["avif", "bmp", "gif", "heic",
                                   "heif", "jpeg", "tiff", "png", "webp", "*"]
                xpath_search_str_base = ".//part[@ct='image/"

                for ext in image_ext_types:

                    # see https://www.synctech.com.au/sms-backup-restore/fields-in-xml-backup-files/ for a description of the XML fields
                    xpath_search_expr = xpath_search_str_base + ext + "']"

                    for b in root.findall(xpath_search_expr):

                        image_date_field = b.getparent(
                        ).getparent().attrib["date"]
                        image_sender_phone_num_field = b.getparent(
                        ).getparent().attrib["address"]

                        b64_results_list.append(
                            [(image_date_field, "".join(char for char in image_sender_phone_num_field if char.isdigit()), b.attrib['data'], b.attrib['cl'], ext)])

                for result_type in b64_results_list:

                    for (epoch_milliseconds, image_sender_phone_number, data, content_location, ext) in result_type:

                        # If it's empty, just assign it a random 10-letter string (so that it doesn't conflict with other unnamed files)
                        if content_location == "" or content_location == "null":
                            content_location = "".join(random.sample(
                                string.ascii_letters, 10)) + "." + ext

                        # this ensures the filename has an extension, if it doesn't (likely) have one
                        output_filename = get_datetime_from_epoch_milliseconds(epoch_milliseconds) + "_" + image_sender_phone_num_field + "_" + (content_location if '.' in content_location else (
                            content_location + "." + ext))

                        with open(os.path.join(output_images_dir, output_filename), mode="wb") as extracted_mms_image:

                            extracted_mms_image.write(base64.b64decode(data))
                            orig_files_count += 1

        else:
            print(
                f"ERROR: {filename} does not match the specified pattern for SMS backup files")

    num_dup_files = remove_duplicate_files(output_images_dir)

    end_time = time.time()
    print(f"{orig_files_count} images found in messages, {
          num_dup_files} duplicates removed. Time elapsed: {round(end_time - start_time, 2)} seconds")


def remove_duplicate_files(output_images_dir: str) -> int:

    duplicate_files_count = 0
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
            sys.exit(1)

    return duplicate_files_count
