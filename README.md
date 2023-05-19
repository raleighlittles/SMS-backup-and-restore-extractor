![app-store-listing-image](https://images-na.ssl-images-amazon.com/images/I/71VnjnwSr4L.png)

# About

The *SMS Backup & Restore* app on [Google Play](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore&hl=en_US) (official name: `com.riteshsahu.SMSBackupRestore`) allows you to backup:

*  your entire SMS history (including attachments)
* your whole or partial call history
* your Contacts ('Address book')

I wrote a  Python script to extract data from those backups. Right now the script can:

1. extract the images out of your sent/received MMS messages
2. create a  de-duplicated call log out of your entire call history
3.  :construction: (NEW) :construction: extract any saved images, media, or keys from a user's contact files. ie. you chose a custom photo for someone in your contacts, made a backup, and now you want that photo back

# Details

## Messages/Backup format

The app saves backups of your SMS messages, images included, in an xml file that looks like `sms-<timestamp>.xml`. The images that were stored as MMS messages are then encoded as [Base64](https://en.wikipedia.org/wiki/Base64).

This script searches for XML files for MMS messages, then decode the data from them to convert to regular images.

Calls are also saved in XML files, named `calls-<timestamp>.xml`. This script creates a CSV file out of all of your call backups, while accounting for duplicates.

## V-Card/VCF parser

This app also lets you backup your contacts to one large [VCF](https://en.wikipedia.org/wiki/VCard) file. There are 3 different standards for V-Card files, but thankfully this parser supports all 3: version 2.1, version 3, and version 4. 

Any of the following Vcard tags:

* `PHOTO`
* `SOUND`
* `LOGO`
* `KEY`

will be either downloaded (if they're stored) as a URL, or otherwise decoded (from Base64).

# Usage

## Prerequisites

* Python 3 (tested on Python 3.10.4)
* [LXML](https://lxml.de/)

## Steps

* Make sure the backups files start with either `sms-` or `calls-`, have the `.xml` extension, and are in their own directory.
* Make sure the contacts files all end in `.vcf` and are in their own directory

## Usage

```
usage: backup_extractor.py [-h] [-i INPUT_DIR] [-t BACKUP_TYPE] [-o OUTPUT_DIR]

options:
  -h, --help            show this help message and exit
  -i INPUT_DIR, --input-dir INPUT_DIR
                        The directory where XML files (for calls or messages) are located
  -t BACKUP_TYPE, --backup-type BACKUP_TYPE
                        The type of extraction. Either 'sms' for message images or 'calls' to create a call log, or 'vcf' to extract media from a VCF/Vcard file
  -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                        The directory where media files that are found, will be extracted to

```

## Output info

* For extracting images **from SMS backups** only: if the metadata of the MMS message included a filename, then that will be used for the output, otherwise a random 10-letter filename will be created. At the end, duplicates will be removed.

* For creating call log, a file named `call_log.csv` will be created, that looks like:

```
Call Date (timestamp),Call date,Call type,Caller name,Caller #,Call duration (s),Call duration,Call Id #
1451965221740,"Jan 4, 2016 7:40:21 PM",Incoming,Dad,+18183457890,65,"1 minute, 5 seconds",0
1452020364934,"Jan 5, 2016 10:59:24 AM",Missed,(Unknown),+11234560987,N/A,N/A,1
1452107940226,"Jan 6, 2016 11:19:00 AM",Incoming,Michael Jordan,+11234567890,194,"3 minutes, 14 seconds",2
```

* For extracting images **from VCard files** only: the user's name will be stored in the filename. If no name is present then a random 10-letter filename will be used.

### Limitations

* The image portions of the backup don't contain date information associated with them, so it's impossible to determine when an image was created

* EXIF data is lost when restoring images

The backups I had only contained image data, not audio or videos. I don't know if that's because there were no video sent, or because the app didn't backup messages with audio or videos in them

### Future Roadmap

- [ ] Refactoring of the VCard/VCF parser
- [ ] Add the ability to convert export messages to a CSV file