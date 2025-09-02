import base64
import datetime
import hashlib
import lxml.etree
import os
import random
import string
import sys
import time

# Constants
MAX_FILENAME_LENGTH = 200
MAX_FULLPATH_LENGTH = 252
    
CONTENT_TYPES = {"image", "video", "audio", "application"}
IMAGE_SUBTYPES = {"avif", "bmp", "gif", "heic", "heif", "jpeg", "pjpeg", "png", "tiff", "webp", "x-icon", "*"}
VIDEO_SUBTYPES = {"3gpp", "avi", "mp4", "mpeg", "ogg", "quicktime", "webm", "x-ms-wmv", "x-flv"}
AUDIO_SUBTYPES = {"3gpp", "amr", "flac", "mp4", "mpeg", "ogg", "webm", "wav"}
APPLICATION_SUBTYPES = {"pdf"}

def get_datetime_from_epoch_milliseconds(epoch_milliseconds: str) -> str:
    return datetime.datetime.fromtimestamp(int(epoch_milliseconds) / 1000).strftime('%Y%m%d-%H%M%S')

def safe_filename(base_dir: str, filename: str, max_len=MAX_FILENAME_LENGTH) -> str:
    full_path = os.path.join(base_dir, filename)
    if len(full_path) <= MAX_FULLPATH_LENGTH:
        return filename  # It's already safe enough for most filesystems

    base, ext = os.path.splitext(filename)
    hashed = hashlib.md5(base.encode('utf-8')).hexdigest()[:8]
    short_base = base[:50]
    short_filename = f"{short_base}_{hashed}{ext}"

    full_path = os.path.join(base_dir, short_filename)
    if len(full_path) > MAX_FULLPATH_LENGTH:
        # fallback if still too long
        short_filename = hashed + ext

    return short_filename

def handle_duplicate_name(base_dir: str, safe_filename: str) -> str:
    safe_filename_base, safe_filename_ext = os.path.splitext(safe_filename)
    unique_output_file = os.path.join(base_dir, safe_filename)
    i = 0
    while os.path.exists(unique_output_file):
        i += 1
        unique_output_file = os.path.join(base_dir, f"{safe_filename_base}-{i}{safe_filename_ext}")

    return unique_output_file

def is_valid_output_directory(output_media_dir: str) -> bool:
    if not os.path.exists(output_media_dir):
        os.makedirs(output_media_dir, exist_ok=False)
        return True

    if not os.path.isdir(output_media_dir):
        print(f"Error: OUTPUT_DIR is not a directory.")
        return False

    with os.scandir(output_media_dir) as entries:
        if any(entries):
            print(f"Error: OUTPUT_DIR is not empty.")
            return False

    return True

def reconstruct_mms_media(sms_xml_dir: str, output_media_dir: str, process_image: bool, process_video: bool, process_audio: bool, process_pdf: bool) -> None:
    if not is_valid_output_directory(output_media_dir):
        return

    start_time = time.time()
    orig_files_count = 0

    contentMsg = (f"Processing messages ({', '.join([x for cond, x in [
        (process_image, 'images'),
        (process_video, 'videos'),
        (process_audio, 'audio'),
        (process_pdf, 'PDFs')
    ] if cond])})...")

    print(contentMsg, end="", flush=True)
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
                    # Get MIME descrete-type/sub-type
                    ct_value = elem.get('ct', '').lower()
                    ct_type, _, ct_subtype = ct_value.partition('/')

                    if not (ct_type in CONTENT_TYPES):
                        # not an image/video/audio/application file. Skip it
                        continue

                    if (ct_type == 'image' and (not process_image or ct_subtype not in IMAGE_SUBTYPES)):
                        # skip this image file because we aren't extracting images, or it's an unsupported image subtype
                        continue
                    elif (ct_type == 'video' and (not process_video or ct_subtype not in VIDEO_SUBTYPES)):
                        # skip this video file because we aren't extracting videos, or it's an unsupported video subtype
                        continue 
                    elif (ct_type == 'audio' and (not process_audio or ct_subtype not in AUDIO_SUBTYPES)):
                        # skip this audio file because we aren't extracting audio, or it's an unsupported audio subtype
                        continue
                    elif (ct_type == 'application' and (not process_pdf or ct_subtype not in APPLICATION_SUBTYPES)):
                        # skip this audio file because we aren't extracting audio, or it's an unsupported application subtype
                        continue

                    # if we get here, then we have a image/video/audio attachment to process
                    parent_parts = elem.getparent()  # <parts>
                    if parent_parts is not None:
                        mms_node = parent_parts.getparent()  # <mms>
                        if mms_node is not None:
                            media_date_field = mms_node.get('date', '')
                            media_sender_field = mms_node.get('address', '')

                            data = elem.get('data', '')
                            content_location = elem.get('cl', '')

                            # Clean phone number
                            clean_phone = "".join(
                                c for c in media_sender_field if c.isdigit()
                            )

                            # If empty, give random name
                            if not content_location or content_location == 'null':
                                content_location = (
                                    "".join(random.sample(string.ascii_letters, 10))
                                    + f".{ct_subtype}"
                                )

                            # Build base filename
                            base_name = (
                                get_datetime_from_epoch_milliseconds(media_date_field)
                                + f"_{clean_phone}_{content_location}"
                            )

                            # If there's no '.' in content_location, add the subtype as extension
                            if '.' not in content_location:
                                base_name += f".{ct_subtype}"

                            # Now ensure it fits the filesystem limit
                            target_filename = safe_filename(output_media_dir, base_name)

                            # Messages with multiple attachments could have the same name.
                            # Create a unique output_file_path using the target_filename
                            output_file_path = handle_duplicate_name(output_media_dir, target_filename)

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

    print("complete.", flush=True)
    # Remove duplicates after extraction
    num_dup_files = remove_duplicate_files(output_media_dir)
    end_time = time.time()

    print(f"{orig_files_count} media files found in messages, "
          f"{num_dup_files} duplicates(or empty files) removed. Time elapsed: "
          f"{round(end_time - start_time, 2)} seconds")


def remove_duplicate_files(output_media_dir: str) -> int:
    duplicate_files_count = 0
    unique_hashes = set()
    
    print("Removing duplicates...", end="", flush=True)
    for filename in os.listdir(output_media_dir):
        file_path = os.path.join(output_media_dir, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            if file_hash in unique_hashes or (os.path.getsize(file_path) == 0):
                os.remove(file_path)
                duplicate_files_count += 1
            else:
                unique_hashes.add(file_hash)
        else:
            print("ERROR: Subdirectory found in output directory")
            sys.exit(1)

    print("complete.", flush=True)
    return duplicate_files_count
