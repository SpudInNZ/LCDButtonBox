#!python3

import irsdk
import time


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


class PiRacing:

    def __init__(self):
        self._last_lap_dist_pct = 0.0
        self._last_lap = 0

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

        weekend_info = ir['WeekendInfo']
        if weekend_info:
            pass

        lap = ir['Lap']
        lap_dist_pct = ir['LapDistPct']

        if not (lap == self._last_lap and self._last_lap_dist_pct == lap_dist_pct):
            if self._last_lap_dist_pct <= lap_dist_pct:
                dt = lap_dist_pct - self._last_lap_dist_pct
            else:
                dt = (1.0-self._last_lap_dist_pct) + lap_dist_pct

            rounded = round(dt, 5)
            if rounded > 0:
                print("Distance" + str(rounded))
                self._last_lap = lap
                self._last_lap_dist_pct = lap_dist_pct

        # note about session info data
        # you should always check if data is available
        # before do something like ir['WeekendInfo']['TeamRacing']
        # so do like this:
        # if ir['WeekendInfo']:
        #   print(ir['WeekendInfo']['TeamRacing'])

        # and just as an example
        # you can send commands to iracing
        # like switch cameras, rewind in replay mode, send chat and pit commands, etc
        # check pyirsdk.py library to see what commands are available
        # https://github.com/kutu/pyirsdk/blob/master/irsdk.py#L332
        # when you run this script, camera will be switched to P1
        # and very first camera in list of cameras in iracing
        # while script is running, change camera by yourself in iracing
        # and how it changed back every 1 sec
        # ir.cam_switch_pos(0, 1)

if __name__ == '__main__':
    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()

    pir = PiRacing()

    try:
        # infinite loop
        while True:
            # check if we are connected to iracing
            check_iracing()
            # if we are, then process data
            if state.ir_connected:
                pir.loop()
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing update data with 60 fps
            time.sleep(1)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
