import sys

NAMES = ['smith',
         'jones',
         'williams',
         'brown',
         'wilson',
         'taylor',
         'johnson',
         'white',
         'martin',
         'anderson']

def get_substring(selected_name, all_names):
    # iterate through lengths
    for length in [l+1 for l in range(len(selected_name))]:
        # get name from start->length to (end-length)->end
        for offset in range(0, len(selected_name)-length+1):
            substring = selected_name[offset:offset+length]
            if not any([substring in name
                        for name in all_names
                        if name != selected_name]):
                return substring
    return None

def go():
    try:
        name = sys.argv[1]
        substring = get_substring(name, NAMES)
        print("Shortest unique substring: {}".format(substring))
    except IndexError:
        print("Specify a name")
        return

if __name__ == '__main__':
    go()
