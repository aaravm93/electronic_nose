import serial
import csv
import time
import sys


PORT="/dev/ttyACM0"

label=sys.argv[1]


ser=serial.Serial(
PORT,
115200
)


file=open(
"data/samples.csv",
"a",
newline=""
)


writer=csv.writer(file)


print("Collecting:",label)


while True:

    line=ser.readline().decode().strip()


    if line.startswith("DATA"):

        values=line.split(",")


        writer.writerow(
        values[1:]+[label]
        )


        file.flush()


        print(values)

