import os

user_profile_dir = 'profiles_out'
profile_txt = 'user_profiles_2.txt'

with open (profile_txt, encoding='utf-8') as f:
    for lines in f.readlines():
        line_split = lines.split('\t')

        user_id = line_split[0]

        profile_info = lines.replace(user_id + '\t', '')
        profile_info = profile_info.replace('\n', '')

        #print (str(profile_info))

        try:
            with open(user_profile_dir + os.sep + user_id + '.profile', 'w') as out:
                out.write(str(profile_info))
        except:
            pass