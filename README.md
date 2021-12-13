# About

The *SMS Backup & Restore* app on [Google Play](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore&hl=en_US) (official name: `com.riteshsahu.SMSBackupRestore`) has the option of storing images from MMS messages as part of the backup. I wrote an extremely simple Python script that allows you to easily extract the images out of these backups.

Currently only images are supported (jpg/png/gif).

# Details

The app saves backups of your SMS messages, images included, in an xml file that looks like `sms-<timestamp>.xml`. The images that were stored as MMS messages are then encoded as [Base64](https://en.wikipedia.org/wiki/Base64). 

All this script does is search XML files for MMS messages, then decode the data from them to convert to regular images.

# Usage

## Prerequisites
* Python 3 (tested on v3.8)
* [LXML](https://lxml.de/)

## Steps
* Make sure your SMS backups are stored in a directory labelled `input` that is created at the root of this repository.
* Make sure the SMS backups files start with `sms-` and have the `.xml` extension.
* Create a directory named `output` at the root of this repository.
* Run `$ python3 main.py`.

## Output
* The `output` directory will be populated with images. 
* If the metadata of the MMS message included a filename, then that will be used for the output, otherwise a random 10-letter filename will be created.

# Feature wishlist/TODO
This project is a very early work in progress!

Ideally, I'd like to add...

* Support for extraction of other file types (including audio and video)
* Populate metadata of output images when available (for example, EXIF data)
* Use argparse to allow users to choose input and output directories
