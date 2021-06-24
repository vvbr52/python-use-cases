# import os
# from os.path import join
#
# lookfor = "python.exe"
# for root, dirs, files in os.walk('C:\\'):
#     print("searching", root)
#     if lookfor in files:
#         print("found: %s" % join(root, lookfor))
#         break

# Python code to search .mp3 files in current
# folder (We can change file type/name and path
# according to the requirements.
import os
dir_path = os.path.dirname(os.path.realpath(__file__))
dir_path='C:\\'
for root, dirs, files in os.walk(dir_path):
    for file in files:
        if file.find('.py') !=-1:
            print(root + '/' + str(file))