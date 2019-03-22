import sys


def analyze_file(filename):
    try:
        results = {}
        f = open(filename)
        for l in f.readlines():
            v = l.split()
            results[v[1]] = results.get(v[1], 0) + int(v[2])
        results = sorted(results.items(), key=lambda x: x[1], reverse=True)
        for k, v in results:
            print(f"{v} bytes send by {k}")
        f.close()
    except:
        print(f"{filename} doesn't found")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <datafile>")
        print("datafile is a file with multiple lines. Each line format is target mac, source mac, frame length.")
    else:
        analyze_file(sys.argv[1])
