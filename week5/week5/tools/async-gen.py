#!/usr/bin/python3

import json
import os
import re
import shutil
import subprocess as sp
import sys
import time


from parameter import args, main, designName

genDir = os.path.join(os.path.dirname(os.path.relpath(__file__)), "../")
srcDir = genDir + "src/"
flowDir = genDir + "flow/"
designDir = genDir + "designs/src/async/"
simDir = genDir + "simulations/"
commonDir = genDir + "../../common/"
platformDir = genDir + "../../common/platforms/" + args.platform + "/"
objDir = flowDir + "objects/" + args.platform + "/async/"

# ------------------------------------------------------------------------------
# Clean the workspace
# ------------------------------------------------------------------------------
print("#----------------------------------------------------------------------")
print("# Cleaning the workspace...")
print("#----------------------------------------------------------------------")
if args.clean:
    p = sp.Popen(["make", "clean_all"], cwd=genDir)
    p.wait()

p = sp.Popen(["git", "checkout", platformDir + "cdl/sky130_fd_sc_hd.spice"])
p.wait()

print("Loading platform_config file...")
print()
try:
    with open(genDir + "../../common/platform_config.json") as file:
        jsonConfig = json.load(file)
except ValueError as e:
    print("Error occurred opening or loading json file.")
    print >> sys.stderr, "Exception: %s" % str(e)
    sys.exit(1)

print("PDK_ROOT value: {}".format(os.getenv("PDK_ROOT")))

# TODO: GHA/GCP/Whatever check
pdk = None
if os.getenv("PDK_ROOT") is not None:
    pdk = os.path.join(os.environ["PDK_ROOT"], "sky130A")
else:
    open_pdks_key = "open_pdks"
    pdk = jsonConfig[open_pdks_key]

if not os.path.isdir(os.path.join(pdk, "libs.ref")):
    print("Cannot find libs.ref folder from open_pdks in " + pdk)
    sys.exit(1)
elif not os.path.isdir(os.path.join(pdk, "libs.tech")):
    print("Cannot find libs.tech folder from open_pdks in " + pdk)
    sys.exit(1)
else:
    sky130A_path = commonDir + "drc-lvs-check/sky130A/"
    if not os.path.isdir(sky130A_path):
        os.mkdir(sky130A_path)
    try:
        sp.Popen(
            [
                "sed -i 's/set PDKPATH \".*/set PDKPATH $env(PDK_ROOT)\/sky130A/' $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc"
            ],
            shell=True,
        ).wait()
    except:
        pass
    shutil.copy2(os.path.join(pdk, "libs.tech/magic/sky130A.magicrc"), sky130A_path)
    shutil.copy2(os.path.join(pdk, "libs.tech/netgen/sky130A_setup.tcl"), sky130A_path)


Fmin, Fmax, ninv = main()


print("Inv : ", ninv)
print("INV:{0}\n".format(ninv))

if args.ninv:
    print("target number of inverters: " + args.ninv)
    ninv = int(args.ninv)


print("#----------------------------------------------------------------------")
print("# Verilog Generation")
print("#----------------------------------------------------------------------")


if args.platform == "sky130hd":
    aux1 = "Ring_Osc_Analog"
    aux2 = "one_Bit_ADC"
elif args.platform == "sky130hs":
    aux1 = "Ring_Osc_Analog_hs"
    aux2 = "one_Bit_ADC_hs"

with open(srcDir + "/async_updo.v", "r") as file:
    filedata = file.read()
if args.mode == "verilog":
    with open(flowDir+ "design/src/async/async_updo.v", "w") as file:
        file.write(filedata)

with open(srcDir + "/Ring_Osc_Analog.v", "r") as file:
    filedata = file.read()
if args.mode == "verilog":
    with open(flowDir+ "design/src/async/Ring_Osc_Analog.v", "w") as file:
        file.write(filedata)

with open(srcDir + "/one_Bit_ADC.v", "r") as file:
    filedata = file.read()
if args.mode == "verilog":
    with open(flowDir+ "design/src/async/one_Bit_ADC.v", "w") as file:
        file.write(filedata)
        
with open(srcDir + "/vanshika_tff.v", "r") as file:
    filedata = file.read()
if args.mode == "verilog":
    with open(flowDir+ "design/src/async/vanshika_tff.v", "w") as file:
        file.write(filedata)
        
print("# 4 Bit Asynchronous UP Counter - Behavioural Verilog Generated")
print("#----------------------------------------------------------------------")
print("# Verilog Generated")
print("#----------------------------------------------------------------------")
print()
if args.mode == "verilog":
    print("Exiting tool....")
    exit()

print("#----------------------------------------------------------------------")
print("# Run Synthesis")
print("#----------------------------------------------------------------------")

p = sp.Popen(["make", "synth"], cwd=flowDir)
p.wait()
if p.returncode:
    print("[Error] Synthesis failed. Refer to the log file")
    exit(1)

print("#----------------------------------------------------------------------")
print("# Synthesis finished")
print("#----------------------------------------------------------------------")

print("#----------------------------------------------------------------------")
print("# Run Floorplan")
print("#----------------------------------------------------------------------")
p = sp.Popen(["make", "floorplan"], cwd=flowDir)
p.wait()
if p.returncode:
    print("[Error] Floorplan failed. Refer to the log file")
    exit(1)
print("#----------------------------------------------------------------------")
print("# Floorplan finished")
print("#----------------------------------------------------------------------")

print("#----------------------------------------------------------------------")
print("# Run Placement")
print("#----------------------------------------------------------------------")
p = sp.Popen(["make", "place"], cwd=flowDir)
p.wait()
if p.returncode:
    print("[Error] Placement failed. Refer to the log file")
    exit(1)
print("#----------------------------------------------------------------------")
print("# Placement finished")
print("#----------------------------------------------------------------------")

print("#----------------------------------------------------------------------")
print("# Run Routing")
print("#----------------------------------------------------------------------")
p = sp.Popen(["make", "finish"], cwd=flowDir)
p.wait()
if p.returncode:
    print("[Error] Place and route failed. Refer to the log file")
    exit(1)
print("#----------------------------------------------------------------------")
print("# Place and Route finished")
print("#----------------------------------------------------------------------")
