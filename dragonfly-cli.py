import usb.core
import usb.util
import argparse
import time
from sys import exit
    
def init():
    global parser
    parser=argparse.ArgumentParser(description="A Python CLI tool to change polling rate and debounce setting of VGN/VXE Dragonfly mice using the 1K or 4K dongles")
    parser.add_argument("-p","--polling_rate",help="Polling rate to set device to (allowed values: 125, 250, 500, 1000, 2000, 4000)", type=int, choices=[125,250,500,1000,2000,4000])
    parser.add_argument("-d","--debounce", help="Debounce delay to set (allowed values: 0, 1, 2, 4, 8, 15, 20)", type=int, choices=[0,1,2,4,8,15,20])
    parser.add_argument("--product_id",help="Product ID matching the device (default: f505)", default=62725)
    parser.add_argument("--toggle_ms", help="Toggle MotionSync",choices=["on", "off"], type=str)
    global args
    args=parser.parse_args()

    
def main():
    # Get all cmd line arguments
    init()
    
    # Default product_id is 4K VGN Dongle, if it has been overwritten, then convert to int
    if args.product_id != 62725:
        args.product_id = "0x" + args.product_id
        args.product_id = int(args.product_id, 16)
    
    global dev
    # Find device with VGN/VXE vendor id and given product id
    dev = findDevice(0x3554,args.product_id)

    # If no polling rate or debounce settings set, then just end since there is nothing to change
    if (not is_polling_rate_valid()) and (not is_debounce_valid()) and (not is_ms_toggle_set()):
        parser.print_usage()
        exit(-1)
    
    # Detach kernel drivers for access
    detachKernelDrivers(getAmountInterfaces())
    
    # Once kernel drivers are detached, claim the interfaces of the dongle
    claimInterfaces(getAmountInterfaces())
    
    # If polling rate is valid, then set polling rate to given value
    if is_polling_rate_valid():
        setPollingRate()
    
    # If debounce setting valid, then set debounce to set value
    if is_debounce_valid():
        setDebounce()
        
    if is_ms_toggle_set():
        toggleMotionSync()
    
    # Once done with applying settings, release the interfaces and attack the kernel drivers again
    releaseInterfaces(getAmountInterfaces())
    attachKernelDrivers(getAmountInterfaces())
    usb.util.dispose_resources(dev)
    exit(0)

# This method verifies if the given polling rate argument is valid 
def is_polling_rate_valid():
    polling_rate = args.polling_rate
    if polling_rate == None:
        return False
    
    if (args.product_id == 62858 and polling_rate > 1000):
        print("1K Dongle detected, only up to 1k polling rate possible!")
        exit(-1)
        
    match polling_rate:
        case 125 | 250 | 500 | 1000 | 2000 | 4000:
            return True
        case _:
            print("Invalid polling rate!")
            return False

def is_ms_toggle_set():
    if args.toggle_ms == None:
        return False
    return True

# This method verifies if given debounce setting is valid
def is_debounce_valid():
    debounce = args.debounce
    if debounce == None:
        return False
    match debounce:
        case 0 | 1 | 2 | 4 | 8 | 15 | 20:
            return True
        case _:
            print("Invalid debounce!")
            return False

# Find the device we are looking for with given vendor and product ids
def findDevice(idVendor, idProduct):
    dev = usb.core.find(idVendor=idVendor, idProduct=idProduct)
    if dev is None:
        print("Device not found, try setting and product id")
        exit(-1)
    return dev

# Iterate through all interfaces for active config
# and detach kernel driver if active
def detachKernelDrivers(amountInterfaces):
    for x in range(amountInterfaces):
        if dev.is_kernel_driver_active(x):
            dev.detach_kernel_driver(x)

# Iterate through all interfaces for active config
# and attach kernel drivers if no longer active
def attachKernelDrivers(amountInterfaces):
    for x in range(amountInterfaces):
        if not dev.is_kernel_driver_active(x):
            dev.attach_kernel_driver(x)
    return True

# Claim interfaces so we can access them
def claimInterfaces(amountInterfaces):
    for x in range(amountInterfaces):
        usb.util.claim_interface(dev, x)

# Release interfaces so mouse can be used again        
def releaseInterfaces(amountInterfaces):
    for x in range(amountInterfaces):
        usb.util.release_interface(dev, x)

# From the currently active config, get the amount of interfaces available (for attaching and detaching)
def getAmountInterfaces():
    currentConfig = dev.get_active_configuration()
    return len(currentConfig.interfaces())

# This method sets the polling rate to the specified value
def setPollingRate():

    # Since polling rate is given through a command line argument,
    # just grab it through the global args var
    pollingRate = args.polling_rate
    # All these polling rate data values were reversed engineered with Wireshark
    match pollingRate:
        case 125:
            data=[0x08, 0x07, 0x00, 0x00, 0x00, 0x06, 0x08, 0x4d, 0x01, 0x54, 0x00, 0x55, 0x00, 0x00, 0x00, 0x00, 0x41]
        case 250:
            data=[0x08, 0x07, 0x00, 0x00, 0x00, 0x06, 0x04, 0x51, 0x01, 0x54, 0x00, 0x55, 0x00, 0x00, 0x00, 0x00, 0x41]
        case 500:
            data=[0x08, 0x07, 0x00, 0x00, 0x00, 0x06, 0x02, 0x53, 0x01, 0x54, 0x00, 0x55, 0x00, 0x00, 0x00, 0x00, 0x41]
        case 1000:
            data=[0x08, 0x07, 0x00, 0x00, 0x00, 0x06, 0x01, 0x54, 0x01, 0x54, 0x00, 0x55, 0x00, 0x00, 0x00, 0x00, 0x41]
        case 2000:
            data=[0x08, 0x07, 0x00, 0x00, 0x00, 0x06, 0x10, 0x45, 0x01, 0x54, 0x00, 0x55, 0x00, 0x00, 0x00, 0x00, 0x41]
        case 4000:
            data=[0x08, 0x07, 0x00, 0x00, 0x00, 0x06, 0x20, 0x35, 0x01, 0x54, 0x00, 0x55, 0x00, 0x00, 0x00, 0x00, 0x41]
        case _:
            print("Unexpected polling rate, exiting")
            exit(-1)
    result = hid_set_report(data)
    # Always returns 17 if successful, not sure about unsuccessful
    if result == 17:
        print("Polling rate set to %d" % pollingRate)
    
    # If debounce was also given as a CLI param, 
    # sleep 2 seconds, otherwise it doesn't always register
    if is_debounce_valid():
        time.sleep(2)

# This method sets the debounce to the specified value       
def setDebounce():
    
    debounce = args.debounce
    match debounce:
        # This is unknown if it actually works
        case 0:
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x00, 0x55, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
            print("Warning: It is unconfirmed whether it actually sets 0 ms debounce as VHUB's lowest value is 1ms")
        case 1:
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x01, 0x54, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case 2:
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x02, 0x53, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case 4:
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x04, 0x51, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case 8:
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x08, 0x4d, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case 15:
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x15, 0x40, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case 20:
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x14, 0x41, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case _:
            print("Unexpected debounce rate, exiting")
            exit(-1)
    
    result = hid_set_report(data)
    if result == 17:
        print("Debounce set to %d" % debounce)
        
def toggleMotionSync():
    # Data Fragment: 08070000a90a 0055 0055 064f00550055ea off
    # Data Fragment: 08070000a90a 0055 0154 064f00550055ea on
    motionSync = args.toggle_ms
    match motionSync:
        case "on":
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x00, 0x55, 0x01, 0x54, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case "off":
            data=[0x08, 0x07, 0x00, 0x00, 0xa9, 0x0a, 0x00, 0x55, 0x00, 0x55, 0x06, 0x4f, 0x00, 0x55, 0x00, 0x55, 0xea]
        case _:
            print("Unexpected MotionSync keyword, exiting")
            exit(-1)
    result = hid_set_report(data)
    if result == 17:
        print("MotionSync turned %s" % motionSync)

    
# This originally was from https://stackoverflow.com/questions/37943825/send-hid-report-with-pyusb
# but it wasn't clear on how to setup the data payload   
def hid_set_report(report):
    return dev.ctrl_transfer(
        bmRequestType=0x21,  # REQUEST_TYPE_CLASS | RECIPIENT_INTERFACE | ENDPOINT_OUT
        bRequest=9,     # SET_REPORT
        wValue=0x0208, # "Vendor" Descriptor Type + 0 Descriptor Index
        wIndex=1,     # USB interface Number
        data_or_wLength=report # The data payload
    )

if __name__ == '__main__':
    main()