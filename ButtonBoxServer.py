#!python3

import irsdk
import time
import serial

# this is our State class, with some helpful variables
class State:
    ir_connected = False
    last_car_setup_tick = -1


# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset all your in State variables
        state.last_car_setup_tick = -1
        # we are shut down ir library (clear all internal variables)
        ir.shutdown()
        print('irsdk disconnected')
    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        state.ir_connected = True
        print('irsdk connected')



class ButtonBoxServer:

    # our main loop, where we retrieve data
    # and do something useful with it

    def loop(self):

        # on each tick we freeze buffer with live telemetry
        # it is optional, useful if you use vars like CarIdxXXX
        # in this way you will have consistent data from this vars inside one tick
        # because sometimes while you retrieve one CarIdxXXX variable
        # another one in next line of code can be changed
        # to the next iracing internal tick_count
        ir.freeze_var_buffer_latest()

        # retrieve live telemetry data
        # check here for list of available variables
        # https://github.com/kutu/pyirsdk/blob/master/vars.txt
        # this is not full list, because some cars has additional
        # specific variables, like break bias, wings adjustment, etc
        # t = ir['SessionTime']
        #print('session time:', t)

        # retrieve CarSetup from session data
        # we also check if CarSetup data has been updated
        # with ir.get_session_info_update_by_key
        # but first you need to request data, before check if its updated
        car_setup = ir['CarSetup']
        if car_setup:
            car_setup_tick = ir.get_session_info_update_by_key('CarSetup')
            if car_setup_tick != state.last_car_setup_tick:
                state.last_car_setup_tick = car_setup_tick
                print('car setup update count:', car_setup['UpdateCount'])
                # now you can go to garage, and do some changes with your setup
                # and that this line will be printed, only when you change something
                # and not every 1 sec

        pitSvFlags = ir['PitSvFlags']
        if pitSvFlags != self._pitSvFlags:
            self._pitSvFlags = pitSvFlags
            self.sendViaSerial("P " + str(pitSvFlags) + "!")

    def sendViaSerial(self, str):  # Function to send data to the Arduino
        self._ser.write(bytes(str.encode('ascii')))  # Send the string to the Arduino 1 byte at a time.

    def __init__(self):
        self._pitSvFlags = None
        self._ser = serial.Serial('com3', 9600)
        time.sleep(1)
        self.sendViaSerial("#BB Server v1.0!")
        time.sleep(1)


if __name__ == '__main__':
    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()

    bbs = ButtonBoxServer()
    try:
        # infinite loop
        while True:
            # check if we are connected to iracing
            check_iracing()
            # if we are, then process data
            if state.ir_connected:
                bbs.loop()
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing update data with 60 fps
            time.sleep(1)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
