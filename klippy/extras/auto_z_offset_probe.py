# Auto Z Offset Probe
#
# Copyright (C) 2024 FAME3D
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
from . import probe

class AutoZOffsetProbe:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.probe_accel = config.getfloat('probe_accel', 0., minval=0.)
        self.recovery_time = config.getfloat('recovery_time', 0.4, minval=0.)
        self.probe_wrapper = probe.ProbeEndstopWrapper(config)
        # Wrappers
        self.get_mcu = self.probe_wrapper.get_mcu
        self.add_stepper = self.probe_wrapper.add_stepper
        self.get_steppers = self.probe_wrapper.get_steppers
        self.home_start = self.probe_wrapper.home_start
        self.home_wait = self.probe_wrapper.home_wait
        self.query_endstop = self.probe_wrapper.query_endstop
        self.multi_probe_begin = self.probe_wrapper.multi_probe_begin
        self.multi_probe_end = self.probe_wrapper.multi_probe_end
        # Common probe implementation helpers
        self.cmd_helper = probe.ProbeCommandHelper(
            config, self, self.probe_wrapper.query_endstop)
        self.probe_offsets = probe.ProbeOffsetsHelper(config)
        self.probe_session = probe.ProbeSessionHelper(config, self)
    def get_probe_params(self, gcmd=None):
        return self.probe_session.get_probe_params(gcmd)
    def get_offsets(self):
        return self.probe_offsets.get_offsets()
    def get_status(self, eventtime):
        return self.cmd_helper.get_status(eventtime)
    def start_probe_session(self, gcmd):
        return self.probe_session.start_probe_session(gcmd)
    def probing_move(self, pos, speed):
        phoming = self.printer.lookup_object('homing')
        return phoming.probing_move(self, pos, speed)
    def probe_prepare(self, hmove):
        toolhead = self.printer.lookup_object('toolhead')
        self.probe_wrapper.probe_prepare(hmove)
        if self.probe_accel:
            systime = self.printer.get_reactor().monotonic()
            toolhead_info = toolhead.get_status(systime)
            self.old_max_accel = toolhead_info['max_accel']
            self.gcode.run_script_from_command(
                    "M204 S%.3f" % (self.probe_accel,))
        if self.recovery_time:
            toolhead.dwell(self.recovery_time)
    def probe_finish(self, hmove):
        if self.probe_accel:
            self.gcode.run_script_from_command(
                    "M204 S%.3f" % (self.old_max_accel,))
        self.probe_wrapper.probe_finish(hmove)

def load_config(config):
    z_offset_probe = AutoZOffsetProbe(config)
    config.get_printer().add_object('z_offset_probe', z_offset_probe)
    return z_offset_probe
