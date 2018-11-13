#!python3

"""

Possibly the worst Python code ever writen. Certainly the worst from me.
Hacked this together without knowing Python. Somehow it works.

"""

import irsdk
import time
import serial
import win32com.client as wc
import argparse
import math
import logging
import datetime
from typing import Dict, List

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

speak = wc.Dispatch("Sapi.SpVoice")

OIL_TEMP_WARNING_TEMP = 141.5  # Minimum temp before warning
OIL_TEMP_CRITICAL_TEMP = 142.75  # Always alert if this level, ignore OIL_TEMP_WARNING_FREQUENCY_SECONDS
OIL_TEMP_WARNING_DIFF = 0.3  # Next warning if temp rises by this much
OIL_TEMP_WARNING_FREQUENCY_SECONDS = 12  # Max frequency of warnings

assert OIL_TEMP_CRITICAL_TEMP > OIL_TEMP_WARNING_TEMP

REPORT_SOF_IN_PRACTICE = False

IN_VR = False

ALL_TYRES = (irsdk.PitSvFlags.lf_tire_change +
             irsdk.PitSvFlags.rf_tire_change +
             irsdk.PitSvFlags.rr_tire_change +
             irsdk.PitSvFlags.rf_tire_change)

FRONT_TYRES = irsdk.PitSvFlags.rf_tire_change + irsdk.PitSvFlags.lf_tire_change
REAR_TYRES = irsdk.PitSvFlags.rf_tire_change + irsdk.PitSvFlags.rr_tire_change


class Speaker:

    @staticmethod
    def say(words: str):
        speak.Speak(words)


class State:
    """
    This is our State class, with some helpful variables
    """

    def __init__(self):
        self.ir_connected = False
        self.last_car_setup_tick = -1
        self.last_driver_info_tick = -1
        self.track_temp = 0
        self.car_type = ''


class ArduinoComms:
    def __init__(self, com_port, speed):
        self.ser = serial.Serial(com_port, speed)
        time.sleep(1)
        s = (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds()
        self.send_via_serial("X" + str(s) + "!")

    def send_via_serial(self, msg: str):  # Function to send data to the Arduino
        # log.debug('Sending ' + msg)
        self.ser.write(bytes(msg.encode('ascii')))  # Send the string to the Arduino 1 byte at a time.
        time.sleep(0.1)


class ButtonBoxServer:
    def __init__(self):

        self._started_at = datetime.datetime.now()
        self._pit_sv_flags = -1
        self._tc = 0.0
        self._bb = 0.0
        self._oiltemp = 0
        self._fuel = 0
        self._sof = 0

        self._last_temp_warning_at = datetime.datetime.now()
        self._last_warning_temp = 0.0

        self._sof_reported = False
        self._drivers: Dict[str, int] = {}  # Driver name and irating

        self._pit_stop_visits = -1
        self._trk_loc: irsdk.TrkLoc = None

        self._my_car_idx = ir['PlayerCarIdx']

        self._event_type = None

        self._critical_engine_temp_alert_sent = False
        self._session_id = None
        self._sub_session_id = None

    def reset(self):

        self._started_at = datetime.datetime.now()
        self._pit_sv_flags = -1
        self._tc = 0
        self._bb = 0
        self._oiltemp = 0
        self._fuel = 0
        self._sof = 0

        self._last_temp_warning_at = datetime.datetime.now()
        self._last_warning_temp = 0.0

        self._sof_reported = False
        self._drivers: Dict[str, int] = {}  # Driver name and irating

        self._pit_stop_visits = -1
        self._trk_loc: irsdk.TrkLoc = None

        self._my_car_idx = ir['PlayerCarIdx']

        self._critical_engine_temp_alert_sent = False
        self._event_type = None
        self._session_id = None
        self._sub_session_id = None

    # our main loop, where we retrieve data
    # and do something useful with it

    def is_practice(self):
        return self._event_type == 'practice'

    def loop(self):

        try:

            ir.freeze_var_buffer_latest()

            # retrieve live telemetry data
            # check here for list of available variables
            # https://github.com/kutu/pyirsdk/blob/master/vars.txt
            # this is not full list, because some cars has additional
            # specific variables, like brake bias, wings adjustment, etc
            # t = ir['SessionTime']
            # print('session time:', t)

            to_send: List[str] = list()

            weekend_info = ir['WeekendInfo']
            if weekend_info:
                if weekend_info['SessionID'] != self._session_id or weekend_info[
                    'SubSessionID'] != self._sub_session_id:
                    self.reset()
                    self._session_id = weekend_info['SessionID']
                    self._sub_session_id = weekend_info['SubSessionID']

                if not self._event_type:
                    self._event_type = weekend_info['EventType']

            is_on_track = ir['IsOnTrack'] == 1

            if not is_on_track:
                self._pit_stop_visits = -1
                self._trk_loc = None
            else:
                trk_loc = ir['CarIdxTrackSurface'][self._my_car_idx]
                if trk_loc and trk_loc != self._trk_loc:
                    if trk_loc == irsdk.TrkLoc.in_pit_stall and self._trk_loc:
                        self._pit_stop_visits += 1
                    self._trk_loc = trk_loc

                fuel_level = ir['FuelLevel']
                gallons = fuel_level / 3.78
                if self._fuel != round(gallons, 2):
                    self._fuel = round(gallons, 2)
                    to_send.append("F " + str(round(gallons, 2)))

                oiltemp = round(ir['OilTemp'], 1)

                if oiltemp > OIL_TEMP_CRITICAL_TEMP and not self._critical_engine_temp_alert_sent:
                    Speaker.say(f"Critical engine temp {oiltemp}")
                elif oiltemp < OIL_TEMP_CRITICAL_TEMP:
                    self._critical_engine_temp_alert_sent = False

                if oiltemp > OIL_TEMP_WARNING_TEMP:
                    if (
                            datetime.datetime.now() - self._last_temp_warning_at).seconds >= OIL_TEMP_WARNING_FREQUENCY_SECONDS:

                        if oiltemp > self._last_warning_temp + OIL_TEMP_WARNING_DIFF:
                            Speaker.say(f"Engine temp is {oiltemp}")
                            self._last_temp_warning_at = datetime.datetime.now()
                            self._last_warning_temp = oiltemp

                        elif oiltemp < self._last_warning_temp - OIL_TEMP_WARNING_DIFF:
                            Speaker.say(f"Engine temp falling")
                            self._last_temp_warning_at = datetime.datetime.now()

                elif self._last_warning_temp:
                    Speaker.say(f"Safe engine temp {oiltemp}")
                    self._last_warning_temp = 0.0

                if self._oiltemp != oiltemp:
                    self._oiltemp = oiltemp
                    to_send.append(f"O {oiltemp}")

            driver_info = ir['DriverInfo']
            if driver_info:
                driver_info_tick = ir.get_session_info_update_by_key('DriverInfo')
                if driver_info_tick != state.last_driver_info_tick:

                    track_temp = round(ir['TrackTempCrew'], 1)
                    if track_temp > 0 and state.track_temp != track_temp:
                        state.track_temp = track_temp
                        to_send.append('t ' + str(math.floor(track_temp)))
                        Speaker.say(f"Track temp is {track_temp} degrees")

                    state.last_driver_info_tick = driver_info_tick
                    irating_sum = 0
                    drivers = driver_info['Drivers']
                    ln = 1600 / math.log(2)

                    current_drivers: Dict[str, int] = {}
                    for driver in drivers:
                        if 'CarNumber' in driver:
                            car_number = int(driver['CarNumber'] or 0)
                            if car_number > 0 and driver['IsSpectator'] != 1:
                                current_drivers[driver['UserName']] = driver['IRating']
                                irating_sum += math.exp(- driver['IRating'] / ln)
                            elif driver['IsSpectator'] == 1:
                                log.info(f"{driver['UserName']} is spectating")

                    driver_count = len(current_drivers)
                    sof = int(math.floor(ln * math.log(driver_count / irating_sum)))
                    if sof != self._sof:
                        self._sof = sof
                        log.info("Drivers:{}  Total SoF:{}".format(driver_count, sof))
                        if not self._sof_reported and (
                                not self.is_practice() or (self.is_practice() and REPORT_SOF_IN_PRACTICE)):
                            Speaker.say(f"SOF is {sof}")
                            to_send.append(f"I {sof}")
                            self._sof_reported = True

                    new_drivers: Dict[str, int] = {name: irating for name, irating in current_drivers.items() if
                                                   name not in self._drivers}

                    for name, irating in new_drivers.items():
                        log.debug(f"Driver {name} - {irating}")
                        if len(self._drivers) and self.is_practice():
                            Speaker.say(f"{name} joined, rating {irating}")

                    self._drivers = current_drivers

            # retrieve CarSetup from session data
            # we also check if CarSetup data has been updated
            # with ir.get_session_info_update_by_key
            # but first you need to request data, before check if its updated
            car_setup = ir['CarSetup']
            if car_setup:
                car_setup_tick = ir.get_session_info_update_by_key('CarSetup')
                if car_setup_tick != state.last_car_setup_tick:
                    state.last_car_setup_tick = car_setup_tick
                    # now you can go to garage, and do some changes with your setup
                    # and that this line will be printed, only when you change something
                    # and not every 1 sec

            bb = ir['dcBrakeBias']
            if bb:
                bb = round(bb, 1)
                if not math.isclose(bb, self._bb):
                    if not math.isclose(self._bb, 0.0):
                        Speaker.say(f"B B {bb}")
                    self._bb = bb
                    to_send.append("B " + str(bb))

            tc = ir['dcTractionControl']
            if tc and self._tc != int(tc):
                tc = int(tc)
                if self._tc > 0:
                    # TC is changing
                    Speaker.say(f"Traction {tc}")
                self._tc = tc
                to_send.append("T " + str(tc))
                to_send.append("r 1")

            pit_sv_flags = ir['PitSvFlags']
            if pit_sv_flags != self._pit_sv_flags:

                #  Only speak if the pitflags have actually changed and car is on track
                if IN_VR and self._pit_sv_flags != -1 and is_on_track and self._trk_loc != irsdk.TrkLoc.in_pit_stall:

                    new_options = self._pit_sv_flags ^ pit_sv_flags

                    if new_options & ALL_TYRES:  # Something about tyres
                        if pit_sv_flags & ALL_TYRES == 0:
                            Speaker.say("Not changing tyres")
                        elif pit_sv_flags & ALL_TYRES == ALL_TYRES:
                            Speaker.say("Changing all tyres")
                        elif pit_sv_flags & ALL_TYRES == FRONT_TYRES:
                            Speaker.say("Changing only front tyres")
                        elif pit_sv_flags & ALL_TYRES == REAR_TYRES:
                            Speaker.say("Changing only rear tyres")
                        else:
                            if pit_sv_flags & irsdk.PitSvFlags.lf_tire_change:
                                Speaker.say("Changing left front")
                            if pit_sv_flags & irsdk.PitSvFlags.rf_tire_change:
                                Speaker.say("Changing right front")
                            if pit_sv_flags & irsdk.PitSvFlags.lr_tire_change:
                                Speaker.say("Changing left rear")
                            if pit_sv_flags & irsdk.PitSvFlags.rr_tire_change:
                                Speaker.say("Changing right rear")

                    if new_options & irsdk.PitSvFlags.fuel_fill:
                        if pit_sv_flags & irsdk.PitSvFlags.fuel_fill:
                            Speaker.say("Will refuel")
                        else:
                            Speaker.say("Will not refuel")
                    if new_options & irsdk.PitSvFlags.fast_repair and ir['PitRepairLeft'] > 0:
                        if pit_sv_flags & irsdk.PitSvFlags.fast_repair:
                            Speaker.say("Will repair")
                        else:
                            Speaker.say("Will not repair")

                self._pit_sv_flags = pit_sv_flags
                to_send.append("P " + str(pit_sv_flags))

            if to_send:
                msg = "!".join([_ for _ in to_send]) + "!"
                arduino_comms.send_via_serial(msg=msg)
        finally:
            ir.unfreeze_var_buffer_latest()


# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset all your in State variables
        state.last_car_setup_tick = -1
        # we are shut down ir library (clear all internal variables)
        ir.shutdown()
        log.info('irsdk disconnected')
    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        global bbs 
        state.ir_connected = True
        bbs = ButtonBoxServer()
        log.info('irsdk connected')


if __name__ == '__main__':

    parser = argparse.ArgumentParser('LCD ButtonBox Server')
    parser.add_argument('--port', '-p', action='store', default='com3', required=True, help='COM port arduino is on')
    parser.add_argument('--speed', '-s', action='store', default='15200', required=True, help='Speed')

    arguments = parser.parse_args()
    arduino_comms = ArduinoComms(com_port=arguments.port, speed=arguments.speed)

    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()
    log.info(f"Waiting for connection")

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
            time.sleep(1 / 60)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
