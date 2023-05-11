import argparse

# locals
import call_log_generator
import sms_extractor


if __name__ == "__main__":
    argparse_parser = argparse.ArgumentParser()

    argparse_parser.add_argument("-i", "--input-dir", type=str, help="The directory where XML files (for calls or messages) are located")
    argparse_parser.add_argument("-t", "--backup-type", type=str, help="The type of extraction. Either 'sms' for message images or 'calls' to create a call log")
    argparse_parser.add_argument("-o", "--output-dir", type=str, help="The directory where media files that are found, will be extracted to")

    argparse_args = argparse_parser.parse_args()

    if (argparse_args.backup_type == "sms"):
        sms_extractor.reconstruct_sms_images(argparse_args.input_dir, argparse_args.output_dir)

    elif (argparse_args.backup_type == "calls"):
        call_log_generator.create_call_log(argparse_args.input_dir)