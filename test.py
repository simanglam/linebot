import re
def check_msg (msg: str,):
    regex = re.compile('\s+') 
    msg_split = regex.split(msg)
    tex = False
    for i in msg_split:
        print(msg)
        if i == ".tex":
            msg = msg[len(i)+1:]
            tex = True
        elif i == "insert" and tex:
            return 
        elif i == "replace" and tex:
            return 3
        elif tex:
            return 5
        else:
            print("Error")
            return 4

print(check_msg(".tex \\c \\s"))
            