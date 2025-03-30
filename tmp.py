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
# # print(config)
# from utilities import Utils


# def generate_random_notif_id():
#     utils = Utils()
#     logged_user_name = 'utils.get_logged_in_user_name()'
#     date_time_string = utils.get_datetime_string()
#     date_string = utils.get_date_string()
#     user_name_length = len(logged_user_name)
#     if user_name_length >= 10:
#         logged_user_name = logged_user_name[:9]
#         random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-5:]
#     else:
#         random_id = logged_user_name + "_" + date_string[:5] + date_time_string[-(14 - user_name_length):]
#     return random_id

# print(generate_random_notif_id())

# import required module
from cryptography.fernet import Fernet

# key generation
# key = Fernet.generate_key()
# print(f"Generated Key: {key.decode()}")

# key="DC3HN3PdUb5z_MyYbitSyVnPU_E_WOfZkUsYR8bWKzY="

# f = Fernet(key)

# token = f.encrypt(b"my deep dark secret")

# print(token)

# dec = f.decrypt("gAAAAABn4lHdfMxWfYLUF9HdSM245-iHNUvatXxllwgSB-hHyZWA2OLTPM0gva0dYAKQG-0ELa0OuHHBICYsNr2h0q7rmRfjTYUiQa35pM5NXqgZD1t7jNw=")
# print(dec.decode("utf-8"))

# Initialize a dictionary
my_dict = {'1': 'Alice', 'age': 25}

a=1
b=2
print(my_dict[str(a)])
my_dict[str(b)] = {"sno": "test"}
my_dict[str(b)] = {"sno1": "test1"}

print(my_dict)

# # Add a new key-value pair
# my_dict['city'] = {'cest': "tes"}

# my_dict['name'] = 'Test'
# print(my_dict)

# my_dict['city']['cest'] = 'tlsor'
# print(my_dict)

# from utilities import Utils

# utils = Utils()

# utils.encrypt_file("jinja2_template.html")