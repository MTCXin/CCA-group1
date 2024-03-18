import re


jobs = ['blackscholes', 'canneal', 'ferret', 'freqmine', 'dedup', 'radix', 'vips']
interferences = ['ibench-cpu', 'ibench-l1d', 'ibench-l1i', 'ibench-l2', 'ibench-llc', 'ibench-membw']

def extract_value(filename, key):
    with open(filename, 'r') as file:
        contents = file.read()
        pattern = r'{}\t([\w.]+)'.format(key)
        match = re.search(pattern, contents)
        if match:
            res = match.group(1)
            print(res)
            return res
        else:
            print("None")
            return None
        
def extract_seconds(contents):
    pattern = r'([0-9]+)m([0-9]+)\.([0-9]{3})s'
    match = re.search(pattern, contents)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2)) + int(match.group(3)) / 1000
        res = minutes * 60 + seconds
        print(res)
        return res
    else:
        print("None")
        return None 

all_real_values = []
all_user_values = []
all_sys_values = []
        
for job in jobs:

    real_values = []
    user_values = []
    sys_values = []

    # no interference - base case
    filename = 'parsec-{}-no-interference.txt'.format(job)
    print(filename)

    base_real_value = extract_seconds(extract_value(filename, "real"))
    real_values.append(base_real_value)

    base_user_value = extract_seconds(extract_value(filename, "user"))
    user_values.append(base_user_value)

    base_sys_value = extract_seconds(extract_value(filename, "sys"))
    sys_values.append(base_sys_value)

    for interf in interferences:
        filename = 'parsec-{}-{}.txt'.format(job, interf)
        print(filename)

        real_value = extract_seconds(extract_value(filename, "real"))
        real_values.append(real_value)

        user_value = extract_seconds(extract_value(filename, "user"))
        user_values.append(user_value)

        sys_value = extract_seconds(extract_value(filename, "sys"))
        sys_values.append(sys_value)
    
    print("Raw values for job ", job)
    print("interference: none, ", interferences)
    print("real: ", real_values)
    print("user: ", user_values)
    print("sys: ", sys_values)

    print("Normalized values for job ", job)
    print("interference: none, ", interferences)
    print("real: ", [round(v/real_values[0],2) for v in real_values])
    print("user: ", [round(v/user_values[0], 2) for v in user_values])
    print("sys: ", [round(v/sys_values[0], 2) for v in sys_values])


    all_real_values.append(real_values)
    all_user_values.append(user_values)
    all_sys_values.append(sys_values)

print("Overview normalized values for 'real'")
print("interference: none, {}".format(interferences))
for i in range(len(jobs)):
    real_values = all_real_values[i]
    normalized = [round(v/real_values[0],2) for v in real_values]
    print("{}\t{}".format(jobs[i].ljust(12), normalized))

 



