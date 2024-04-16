from . import probe

class ManualZTilt:

    def __init__(self, config):
        self.printer = config.get_printer()
        self.probe_helper = probe.ProbePointsHelper(config,self.probe_finalize)
        if len(self.probe_helper.probe_points) != 2:
            raise config.error(
                "Need exactly 2 probe points for skew correction!")
        self.height_tolerance = config.getfloat("height_tolerance", 0.1, 0.)
        self.thread_constant = config.getfloat("thread_constant")
        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command(
            'MANUAL_Z_TILT', self.cmd_MANUAL_Z_TILT,
            desc=self.cmd_MANUAL_Z_TILT_help)
    cmd_MANUAL_Z_TILT_help = "CoreXZ Skew Correction Script"

    def cmd_MANUAL_Z_TILT(self, gcmd):
        self.probe_helper.start_probe(gcmd)

    def probe_finalize(self, offsets, results):
        if len(results) != 2:
            self.gcode.respond_info("COREXZ CALIBRATE received \
                                    more results than expected!")
            return
        pos_left = results.pop(0) if results[0][0] < results[1][0] \
            else results.pop(1)
        pos_right = results[0]
        z_pos_left = pos_left[2]
        z_pos_right = pos_right[2]
        z_variance = (z_pos_left - z_pos_right) #find the difference
        height_difference= abs(z_variance)
        self.gcode.respond_info("Height difference = %.4fmm." \
                                % height_difference)

        #calculate the rotation required and round to nearest 0.25
        calculated_turn = round(abs(z_variance*self.thread_constant)*4)/4
        if abs(z_variance) < self.height_tolerance:
            self.gcode.respond_info("Congratulations, Your X Axis is Calibrated!")

        elif calculated_turn < .25:
            if z_variance < (-1 * self.height_tolerance):
                self.gcode.respond_info("Turn Left Tension Bolt CW by 1/8th rotation and\n Right Tension Bolt CCW 1/8th rotation")

            elif z_variance > self.height_tolerance:
                self.gcode.respond_info("Turn Left Tension Bolt CCW by 1/8th rotation and\n Right Tension Bolt CW 1/8th rotation")
        else:
            if z_variance < (-1 * self.height_tolerance):
                self.gcode.respond_info("Turn Left Tension Bolt CW by %.2f rotations and\n Right Tension Bolt CCW %.2f rotations" %(calculated_turn, calculated_turn))

            elif z_variance > self.height_tolerance:
                self.gcode.respond_info("Turn Left Tension Bolt CCW by %.2f rotations and\n Right Tension Bolt CW %.2f rotations" %(calculated_turn, calculated_turn))

def load_config(config):
    return ManualZTilt(config)
