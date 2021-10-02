import os

def print_hi(name):
    try:
        for count, filename in enumerate(os.listdir("img/tile/weapons/")):
            print ("count:" + str(count))
            print("filename:" + filename)
            dst = "img/tile/weapons/renamed/" + str(count) + ".png"

            src = "img/tile/weapons/" + filename

            print ("src:" + src)
            print ("destination:" + dst)

            # rename() function will
            # rename all the files
            os.rename(src, dst)
    except():
        print("An exception was thrown")

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')