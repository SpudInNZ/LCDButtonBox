#!python3

import irsdk
import time
import serial
import argparse
import math

# this is our State class, with some helpful variables
class State:
    ir_connected = False
    last_car_setup_tick = -1


class Car:

    def __int__(self, carname):
        self._carName = carname

    def getNextRaceTime(self):
        if self._carName == 'j':
            pass


class FuelCalculator:
    def __init__(self):
        self.stint = 0
        self.fuel_remaining = 0
        self.fuel_use_history = []

    def on_progress(self, lap_dist_pct, fuel_level, fuel_level_pct):
        self.fuel_use_history.append({"lap_dist_pct" : lap_dist_pct,
                                      "fuel_level" : fuel_level,
                                      "fuel_level_pct" : fuel_level_pct})

    def on_pit(self):
        pass

class ArduinoComms:
    def __init__(self, com_port, speed):
        self.ser = serial.Serial(com_port, speed)
        time.sleep(1)
        s = int(round(time.time(), 0))
        self.sendViaSerial("X" + str(s) + "!")

    def sendViaSerial(self, str):  # Function to send data to the Arduino
        self.ser.write(bytes(str.encode('ascii')))  # Send the string to the Arduino 1 byte at a time.
        time.sleep(1)


arduino_comms = None

class ButtonBoxServer:

    def __init__(self):
        self._pitSvFlags = None
        self._driverCar = None
        self._fuel_calculator = None

    def setCarInfo(self):
        driverInfo = ir['DriverInfo']
        if driverInfo:
            driverCarIdx = driverInfo['DriverCarIdx']
            if driverCarIdx:
                drivers = driverInfo['Drivers']
                if drivers:
                    for driver in drivers:
                        if driver['CarIdx'] == driverCarIdx:
                            shortName = driver['CarClassShortName']
                            if shortName is not None:
                                self._driverCar = Car()
                                self._driverCar._carName = shortName;
                                arduino_comms.sendViaSerial("#Car: " + shortName + "!")

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

        if self._driverCar is None:
            self.setCarInfo()

        # retrieve live telemetry data
        # check here for list of available variables
        # https://github.com/kutu/pyirsdk/blob/master/vars.txt
        # this is not full list, because some cars has additional
        # specific variables, like break bias, wings adjustment, etc
        # t = ir['SessionTime']
        #print('session time:', t)

        if ir['IsOnTrack'] == 1:
            if self._fuel_calculator is None:
                self._fuel_calculator = FuelCalculator()
            fuel_level = ir['FuelLevel']
            if fuel_level:
                print('fuel:', fuel_level / 3.78)
                gallons = fuel_level / 3.78
                arduino_comms.sendViaSerial("F " + str(round(gallons,2)) + "!")
            fuel_level_pct = ir['FuelLevelPct']
            lap_dist_pct = ir['LapDistPct']
            self._fuel_calculator.on_progress(lap_dist_pct, fuel_level, fuel_level_pct )

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
            arduino_comms.sendViaSerial("P " + str(pitSvFlags) + "!")

bbs = ButtonBoxServer()


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
        bbs = ButtonBoxServer()
        print('irsdk connected')

if __name__ == '__main__':

    parser = argparse.ArgumentParser('LCD ButtonBox Server')
    parser.add_argument('--port', '-p', action='store', default='com3', required=True, help='COM port arduino is on')
    parser.add_argument('--speed', '-s', action='store', default='9600', required=True, help='Speed')

    arguments = parser.parse_args()

    arduino_comms = ArduinoComms(com_port=arguments.port, speed=arguments.speed)

    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()

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
            time.sleep(0.1)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
