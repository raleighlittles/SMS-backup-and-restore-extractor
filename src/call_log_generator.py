import csv
import os
import xml.etree.ElementTree


def get_human_readable_duration(duration_raw_s: str) -> str:
    """
    Converts the number of seconds into a formatted and correctly pluralized reading of hours, minutes, and seconds
    e.g "192" --> "3 minutes, 12 seconds"
    e.g. "0" --> "0 seconds"
    """

    duration_s = int(duration_raw_s)

    # Kudos to https://stackoverflow.com/questions/775049
    time_divisor = 60

    minutes, seconds = divmod(duration_s, time_divisor)
    hours, minutes = divmod(minutes, time_divisor)

    formatted_str = ""

    if (hours > 0):
        formatted_str += ("{} hours".format(hours))

    if (minutes > 0):
        formatted_str += (", " if (formatted_str != "") else "") + \
            "{} ".format(minutes) + "minute" + ("s" if minutes > 1 else "")

    # We still need the seconds field to show up if there wasn't already an hours or minutes included in the string
    # Example: in the case a call is exactly 0 seconds long
    if (seconds > 0) or ((seconds == 0) and (formatted_str == "")):
        formatted_str += (", " if (formatted_str != "") else "") + \
            "{} ".format(seconds) + "second" + ("s" if seconds != 1 else "")

    return formatted_str


def create_call_log(calls_xml_dir) -> None:

    all_calls_list = []

    # https://developer.android.com/reference/android/provider/CallLog.Calls#TYPE
    call_type_map = {"1": "Incoming", "2": "Outgoing", "3": "Missed"}

    # Used to maintain uniqueness among calls, since multiple calls cannot happen at the same time
    call_timestamps = set()

    call_timestamp_key_name = "Call Date (timestamp)"

    num_calls = 0

    for filename in os.listdir(calls_xml_dir):

        if filename.endswith(".xml") and filename.startswith("calls"):
            xml_tree = xml.etree.ElementTree.parse(
                os.path.join(calls_xml_dir, filename))

            for call_entry_xml in xml_tree.findall(".//call"):

                # Make sure this call hasn't already been logged before
                if not call_entry_xml.attrib['date'] in call_timestamps:

                    call_entry_obj = dict()

                    call_timestamp = call_entry_xml.attrib["date"]

                    call_entry_obj.update({call_timestamp_key_name: call_timestamp,
                                           "Call date": call_entry_xml.attrib["readable_date"]})

                    call_type = call_type_map[call_entry_xml.attrib["type"]]
                    call_entry_obj["Call type"] = call_type

                    call_entry_obj["Caller name"] = call_entry_xml.attrib["contact_name"]
                    call_entry_obj["Caller #"] = call_entry_xml.attrib["number"]

                    # Missed calls don't have "duration"
                    # But sometimes, incoming/outgoing calls do have a duration of 0 if you hang up really fast
                    call_duration_raw = call_entry_xml.attrib["duration"]

                    if call_type != "Missed":
                        # the 'raw' value
                        call_entry_obj["Call duration (s)"] = call_duration_raw
                        call_entry_obj["Call duration"] = get_human_readable_duration(
                            call_duration_raw)

                    else:
                        # The CSV writer is a bit finnicky, so we need to make sure that all dictionaries
                        # have the same key names, ie we can't just leave off these 2 or that'll mess up the columns
                        call_entry_obj["Call duration (s)"] = "N/A"
                        call_entry_obj["Call duration"] = "N/A"

                    call_entry_obj["Call Id #"] = num_calls

                    call_timestamps.add(call_timestamp)

                    all_calls_list.append(call_entry_obj)

                    num_calls += 1

        print(
            f'[DEBUG] Finished processing file {filename} .. now at {num_calls} calls total')

    # All calls have been created. Now write the entire log to csv file

    with open('call_log.csv', 'w') as csv_file_handle:
        csv_writer = csv.writer(csv_file_handle)

        # Write the header
        csv_writer.writerow(all_calls_list[0].keys())

        for call_entry in sorted(all_calls_list, key=lambda k: k[call_timestamp_key_name]):
            csv_writer.writerow(list(call_entry.values()))
