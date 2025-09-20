# This module has been replaced by mms_media_extractor

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
    return datetime.datetime.fromtimestamp(int(epoch_milliseconds) / 1000).strftime('%Y%m%d-%H%M%S')


def safe_filename(base_dir: str, filename: str, max_len=200) -> str:
    full_path = os.path.join(base_dir, filename)
    if len(full_path) <= 255:
        return filename  # It's already safe enough for most filesystems

    base, ext = os.path.splitext(filename)
    hashed = hashlib.md5(base.encode('utf-8')).hexdigest()[:8]
    short_base = base[:50]
    short_filename = f"{short_base}_{hashed}{ext}"

    full_path = os.path.join(base_dir, short_filename)
    if len(full_path) > 255:
        # fallback if still too long
        short_filename = hashed + ext

    return short_filename


def reconstruct_sms_images(sms_xml_dir: str, output_images_dir: str) -> None:
    if not os.path.exists(output_images_dir):
        os.makedirs(output_images_dir, exist_ok=False)

    start_time = time.time()
    orig_files_count = 0
    image_ext_types = {"avif", "bmp", "gif", "heic", "heif",
                       "jpeg", "tiff", "png", "webp", "*"}

    for filename in os.listdir(sms_xml_dir):
        if filename.endswith(".xml") and filename.startswith("sms"):
            file_path = os.path.join(sms_xml_dir, filename)

            context = lxml.etree.iterparse(
                file_path,
                events=('end',),
                huge_tree=True,
                recover=True
            )

            for event, elem in context:
                if elem.tag == 'part':
                    ct_attr = elem.get('ct', '').lower()
                    if ct_attr.startswith('image/'):
                        ext_candidate = ct_attr.split('/')[-1]
                        if ext_candidate in image_ext_types:
                            parent_parts = elem.getparent()  # <parts>
                            if parent_parts is not None:
                                mms_node = parent_parts.getparent()  # <mms>
                                if mms_node is not None:
                                    image_date_field = mms_node.get('date', '')
                                    image_sender_field = mms_node.get('address', '')

                                    data = elem.get('data', '')
                                    content_location = elem.get('cl', '')

                                    # Clean phone number
                                    clean_phone = "".join(
                                        c for c in image_sender_field if c.isdigit()
                                    )

                                    # If empty, give random name
                                    if not content_location or content_location == 'null':
                                        content_location = (
                                            "".join(random.sample(string.ascii_letters, 10))
                                            + f".{ext_candidate}"
                                        )

                                    # Build base filename
                                    base_name = (
                                        get_datetime_from_epoch_milliseconds(image_date_field)
                                        + f"_{clean_phone}_{content_location}"
                                    )
                                    # If there's no '.' in content_location, add the extension
                                    if '.' not in content_location:
                                        base_name += f".{ext_candidate}"

                                    # Now ensure it fits the filesystem limit
                                    final_filename = safe_filename(output_images_dir, base_name)
                                    output_file_path = os.path.join(output_images_dir, final_filename)

                                    # Write decoded data
                                    try:
                                        with open(output_file_path, 'wb') as out_f:
                                            out_f.write(base64.b64decode(data))
                                            orig_files_count += 1
                                    except Exception as e:
                                        print(f"ERROR writing file {output_file_path}: {e}")

                # Free memory by clearing processed element
                elem.clear()
                # Option A: remove from parent
                parent = elem.getparent()
                if parent is not None:
                    parent.remove(elem)

            # Done parsing this file
            del context

        else:
            print(f"ERROR: {filename} does not match the specified pattern for SMS backup files")

    # Remove duplicates after extraction
    num_dup_files = remove_duplicate_files(output_images_dir)
    end_time = time.time()
    print(f"{orig_files_count} images found in messages, "
          f"{num_dup_files} duplicates removed. Time elapsed: "
          f"{round(end_time - start_time, 2)} seconds")


def remove_duplicate_files(output_images_dir: str) -> int:
    duplicate_files_count = 0
    unique_hashes = set()

    for filename in os.listdir(output_images_dir):
        file_path = os.path.join(output_images_dir, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            if file_hash in unique_hashes:
                os.remove(file_path)
                duplicate_files_count += 1
            else:
                unique_hashes.add(file_hash)
        else:
            print("ERROR: Subdirectory found in output directory")
            sys.exit(1)

    return duplicate_files_count
