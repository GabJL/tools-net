import sys
sys.path.append('..')
from utils import flowcontrollib

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <Protocol configuration (json)>")
    else:
        try:
            prot = flowcontrollib.Protocol(sys.argv[1])
            prot.run()
            prot.write()
        except flowcontrollib.ProtocolError as e:
            print(e)
