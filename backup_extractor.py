import argparse

# locals
import src.call_log_generator
import src.mms_images_extractor
import src.contacts_vcard_extractor

if __name__ == "__main__":

    argparse_parser = argparse.ArgumentParser()

    argparse_parser.add_argument("-i", "--input-dir", type=str, required=True,
                                 help="The directory where XML files (for calls or messages) are located")
    argparse_parser.add_argument("-t", "--backup-type", type=str, required=True,
                                 help="The type of extraction. Either 'sms' for message images or 'calls' to create a call log, or 'vcf' to extract media from a VCF/Vcard file")
    argparse_parser.add_argument("-o", "--output-dir", type=str, required=True,
                                 help="The directory where media files that are found, will be extracted to")

    argparse_args = argparse_parser.parse_args()

    if (argparse_args.backup_type == "sms"):
        src.mms_images_extractor.reconstruct_sms_images(
            argparse_args.input_dir, argparse_args.output_dir)

    elif (argparse_args.backup_type == "calls"):
        src.call_log_generator.create_call_log(argparse_args.input_dir)

    elif (argparse_args.backup_type == "vcf"):
        src.contacts_vcard_extractor.parse_contacts_from_vcf_files(
            argparse_args.input_dir, argparse_args.output_dir)
