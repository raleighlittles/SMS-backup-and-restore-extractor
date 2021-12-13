import base64
import hashlib
import lxml.etree
import os
import pdb
import random
import string

if __name__ == "__main__":

    input_dir, output_dir = "input", "output"
    orig_files_count = 0
    for filename in os.listdir(input_dir):
        if filename.endswith(".xml") and filename.startswith("sms"):
            parser = lxml.etree.XMLParser(recover=True)
            root = lxml.etree.parse(os.path.join("input", filename), parser=parser).getroot()
            b64_results_list = []

            # '*' technically isn't a valid MIME type but for some reason this application uses it
            # https://www.iana.org/assignments/media-types/media-types.xhtml#image
            image_ext_types = ["gif", "png", "jpeg", "*"]
            xpath_search_str_base = ".//part[@ct='image/"

            for ext in image_ext_types:
                xpath_search_expr = xpath_search_str_base + ext + "']"
                b64_results_list.append([(b.attrib['data'], b.attrib['name']) for b in root.findall(xpath_search_expr)])

            for result_type in b64_results_list:
                for (data, name) in result_type:
                    if name == "" or name == "null":
                        name = "".join(random.sample(string.ascii_letters, 10))
                    with open(os.path.join(output_dir, name), 'wb') as f:
                        f.write(base64.b64decode(data))
                        orig_files_count += 1

    print(f"{orig_files_count} files created... Automatically removing duplicates")

    duplicate_files_count = 0
    # Once files are created, go through and delete duplicates
    unique_files_hash_list = []
    for filename in os.listdir(output_dir):
        file_path = os.path.join(output_dir, filename)
        if os.path.isfile(file_path):
            file_hash = hashlib.md5(open(file_path, 'rb').read()).hexdigest()
            if file_hash not in unique_files_hash_list:
                unique_files_hash_list.append(file_hash)

            else:
                os.remove(file_path)
                duplicate_files_count += 1
        else:
            print("ERROR: Subdirectory found in output directory")

    print(f"{duplicate_files_count} files removed")