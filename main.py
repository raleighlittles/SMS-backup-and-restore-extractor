import base64
import os
import random
import string

import lxml.etree

if __name__ == "__main__":
    for filename in os.listdir("input"):
        if filename.endswith(".xml") and filename.startswith("sms"):
            parser = lxml.etree.XMLParser(recover=True)
            root = lxml.etree.parse(os.path.join("input", filename), parser=parser).getroot()
            # Support for regular expressions in XPath expressions is lackluster at best.
            b64_png = [(b.attrib['data'], b.attrib['name']) for b in root.findall(".//part[@ct='image/png']")]
            b64_jpg = [(b.attrib['data'], b.attrib['name']) for b in root.findall(".//part[@ct='image/jpeg']")]

            for (data, name) in b64_png + b64_jpg:
                if name == "" or name == "null":
                    name = "".join(random.sample(string.ascii_letters, 10))
                with open(os.path.join("output", name), 'wb') as f:
                    f.write(base64.b64decode(data))
