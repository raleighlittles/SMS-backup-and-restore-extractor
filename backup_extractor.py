import argparse
from argparse import RawTextHelpFormatter

# locals
import src.call_log_generator
import src.mms_media_extractor
import src.contacts_vcard_extractor

if __name__ == "__main__":

    argparse_parser = argparse.ArgumentParser(
        description="Extracts media files, call logs, or vcf/vCard media, from an SMS Backup & Restore backup archive.",
        formatter_class=RawTextHelpFormatter,
        epilog='''Examples:
  To extract all MMS media attachments:
     backup_extractor.py -t sms -i input_dir -o output_dir

  To extract only Video files:
     backup_extractor.py -t sms -i input_dir -o output_dir --no-images --no-audio --no-pdfs

  To extract a de-duplicated call log:
     backup_extractor.py -t calls -i input_dir -o output_dir

  To extract VCF/vCard media:
     backup_extractor.py -t vcf -i input_dir -o output_dir
 
'''
    )

    argparse_parser.add_argument("-i", "--input-dir", type=str, required=True,
                                 help="The directory where XML files (for calls or messages) are located")
    argparse_parser.add_argument("-t", "--backup-type", type=str, required=True,
                                 help="The type of extraction. Either 'sms' for message media files, or 'calls' to create a call log, or 'vcf' to extract media from a VCF/vCard file")
    argparse_parser.add_argument("-o", "--output-dir", type=str, required=True,
                                 help="The directory where media files that are found, will be extracted to")

    argparse_parser.add_argument("--no-images", action='store_false',
                                 help="Don't extract image files from messages")
    argparse_parser.add_argument("--no-videos", action='store_false',
                                 help="Don't extract video files from messages")
    argparse_parser.add_argument("--no-audio", action='store_false',
                                 help="Don't extract audio files from messages")
    argparse_parser.add_argument("--no-pdfs", action='store_false',
                                 help="Don't extract PDF files from messages")

    argparse_args = argparse_parser.parse_args()

    if (argparse_args.backup_type == "sms"):
        src.mms_media_extractor.reconstruct_mms_media(
            argparse_args.input_dir, argparse_args.output_dir,
            argparse_args.no_images, argparse_args.no_videos,
            argparse_args.no_audio, argparse_args.no_pdfs)

    elif (argparse_args.backup_type == "calls"):
        src.call_log_generator.create_call_log(argparse_args.input_dir)

    elif (argparse_args.backup_type == "vcf"):
        src.contacts_vcard_extractor.parse_contacts_from_vcf_files(
            argparse_args.input_dir, argparse_args.output_dir)
