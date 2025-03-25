# import argparse
#
# parser = argparse.ArgumentParser(description="Just an example",
#                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# parser.add_argument("-a", "--archive", action="store_true", help="archive mode")
# parser.add_argument("-v", "--verbose", action="store_true", help="increase verbosity")
# parser.add_argument("-B", "--block-size", help="checksum blocksize")
# parser.add_argument("--ignore-existing", action="store_true", help="skip files that exist")
# parser.add_argument("--exclude", help="files to exclude")
# parser.add_argument("src", help="Source location")
# parser.add_argument("dest", help="Destination location")
# args = parser.parse_args()
# config = vars(args)
# print(config)
from utilities import Utils


def generate_random_notif_id():
    utils = Utils()
    logged_user_name = 'utils.get_logged_in_user_name()'
    date_time_string = utils.get_datetime_string()
    date_string = utils.get_date_string()
    user_name_length = len(logged_user_name)
    if user_name_length >= 10:
        logged_user_name = logged_user_name[:9]
        random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-5:]
    else:
        random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-(14 - user_name_length):]
    return random_id

print(generate_random_notif_id())

