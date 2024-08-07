# ts20.py --
# 11 Mar 2024 - @todbot / Tod Kurt
#
# Some aspect of this library copies functions from:
#   https://github.com/adafruit/Adafruit_CircuitPython_CAP1188
# Configuration information from:
#   https://github.com/yni2yni/TS20

from micropython import const
from adafruit_bus_device import i2c_device

_TS20_DEFAULT_ADDRESS = const(0x6A)

_TS20_SEN_PWM1 = const(0x00)  # ch2,ch1
_TS20_SEN_PWM2 = const(0x01)  # ch4,ch3
_TS20_SEN_PWM3 = const(0x02)  # ch6,ch5
_TS20_SEN_PWM4 = const(0x03)  # -,ch7
_TS20_SEN_PWM5 = const(0x04)  # ch9,ch8
_TS20_SEN_PWM6 = const(0x05)  # ch11,ch10
_TS20_SEN_PWM7 = const(0x06)  # ch13,ch12
_TS20_SEN_PWM8 = const(0x07)  # ch15,ch14
_TS20_SEN_PWM9 = const(0x08)  # ch17,ch16
_TS20_SEN_PWM10 = const(0x09)  # ch19,ch18
_TS20_SEN_PWM11 = const(0x0A)  # ch20

_TS20_GTRL1 = const(0x0B)
_TS20_GTRL2 = const(0x0C)
_TS20_CAL_CTRL = const(0x0D)

_TS20_PORT_CTRL1 = const(0x0E)
_TS20_PORT_CTRL2 = const(0x0F)
_TS20_PORT_CTRL3 = const(0x10)
_TS20_PORT_CTRL4 = const(0x11)
_TS20_PORT_CTRL5 = const(0x12)
_TS20_PORT_CTRL6 = const(0x13)

_TS20_CAL_HOLD1 = const(0x14)
_TS20_CAL_HOLD2 = const(0x15)
_TS20_CAL_HOLD3 = const(0x16)
_TS20_ERR_CTRL = const(0x17)

_TS20_OUTPUT1 = const(0x20)
_TS20_OUTPUT2 = const(0x21)
_TS20_OUTPUT3 = const(0x22)

_TS20_REF_WR_H = const(0x23)
_TS20_REF_WR_L = const(0x24)
_TS20_REF_WR_CH1 = const(0x25)
_TS20_REF_WR_CH2 = const(0x26)
_TS20_REF_WR_CH3 = const(0x27)

_TS20_SEN_RD_CTRL = const(0x28)
_TS20_SEN_RD = const(0x29)

_TS20_RD_CH1 = const(0x30)
_TS20_RD_CH2 = const(0x31)
_TS20_RD_CH3 = const(0x32)
_TS20_SEN_H = const(0x33)
_TS20_SEN_L = const(0x34)
_TS20_REF_H = const(0x35)
_TS20_REF_L = const(0x36)
_TS20_RD_CH4 = const(0x37)
_TS20_RD_CH5 = const(0x38)
_TS20_RD_CH6 = const(0x39)

#PADSENS = const(0b0101)  # 0x55 default
PADSENS = const(0b1111)  # 0xff
#PADSENS = const(0b0000)  # 0x00
PADSENS2 = const((PADSENS << 4) | PADSENS)

# fmt: off
# default config for 20 touch sensors with low-impedance, low-sensitivity
_config_info_default = [
    # register name, register data
    # RB_SEL=Noram, Sleep Mode=Disable, S/W Reset=Enable,
    # IMP_SEL=High Imp. S/M_Mode=Multi, VPM=0
    (_TS20_GTRL2, 0x1A), # put chip into reset, so we can change parameters?
    # set all ports to capsense (as opposed to LED driver or tact switch)
    (_TS20_PORT_CTRL1, 0x00),  # Port Control
    (_TS20_PORT_CTRL2, 0x00),
    (_TS20_PORT_CTRL3, 0x00),
    (_TS20_PORT_CTRL4, 0x00),
    (_TS20_PORT_CTRL5, 0x00),
    (_TS20_PORT_CTRL6, 0x00),
    # Sensitivty
    # if SSC bit =1(Normal Step) , (Data Value x 0.2%)+0.15%
    # if SSC bit =0(Fine Stemp) , (Data Value x 0.1%)+0.05%
    (_TS20_SEN_PWM1, PADSENS2),  # Sensitivty control,(threshold level), ch2,1
    (_TS20_SEN_PWM2, PADSENS2),  # Sensitivty control,(threshold level), ch4,3
    (_TS20_SEN_PWM3, PADSENS2),  # Sensitivty control,(threshold level), ch6,5
    (_TS20_SEN_PWM4, PADSENS2),  # Sensitivty control,(threshold level), ch-,7
    (_TS20_SEN_PWM5, PADSENS2),  # Sensitivty control,(threshold level), ch9,8
    (_TS20_SEN_PWM6, PADSENS2),  # Sensitivty control,(threshold level), ch11,10
    (_TS20_SEN_PWM7, PADSENS2),  # Sensitivty control,(threshold level), ch13,12
    (_TS20_SEN_PWM8, PADSENS2),  # Sensitivty control,(threshold level), ch15,14
    (_TS20_SEN_PWM9, PADSENS2),  # Sensitivty control,(threshold level), ch17,16
    (_TS20_SEN_PWM10, PADSENS2),  # Sensitivty control,(threshold level), ch19,18
    (_TS20_SEN_PWM11, PADSENS2),  # Sensitivty control,(threshold level), ch20
    # General Ctrl1, SSC= Normal Step, MS=Auto Mode, FTC=5sec,
    #                Respons Time Control(RTC)= 011b + 1 = 4 times
    #(_TS20_GTRL1, 0x4B),  # 0x4B is from Arduino sketch, 0x4a is reset default (0b010_01_010
    #(_TS20_GTRL1, 0x4a), # reset default
    #(_TS20_GTRL1, 0x48), # gives a snappier response!
    (_TS20_GTRL1, 0x6a), # MS=1 "fast mode", SSC=1 normal steps
    
    (_TS20_CAL_HOLD1, 0x00),  # Calibration On, ch 1-7
    (_TS20_CAL_HOLD2, 0x00),  # Calibration On, ch 8-14
    (_TS20_CAL_HOLD2, 0x00),  # Calibration On, ch 9-20
    #(_TS20_ERR_CTRL, 0x0D),
    (_TS20_ERR_CTRL, 0x0F),
    #(_TS20_CAL_CTRL, 0xFA),
    (_TS20_CAL_CTRL, 0xAF),
    # General Ctrl2, RB_SEL=Noram, Sleep Mode=Disable, S/W Reset=Disable,
    #                IMP_SEL=High Imp. S/M_Mode=Multi, VPM=0
    #(_TS20_GTRL2, 0x12),     # Software Reset Disable (Clear)
    # General Ctrl2, RB_SEL=Noram, Sleep Mode=Disable, S/W Reset=Disable,
    #                IMP_SEL=Low Imp. S/M_Mode=Multi, VPM=0
    (_TS20_GTRL2, 0x02),     # Software Reset Disable (Clear)
]
# fmt: on


class TS20:
    """Driver for the TS20 connected over I2C."""

    def __init__(
        self, i2c, address=_TS20_DEFAULT_ADDRESS, config_info=_config_info_default
    ):
        self._i2c = i2c_device.I2CDevice(i2c, address)
        self._buf = bytearray(2)
        self.write_config(config_info)

    def _write_register(self, reg_addr, reg_val):
        """Write 8 bit value to registter at address."""
        self._buf[0] = reg_addr
        self._buf[1] = reg_val
        with self._i2c as i2c:
            i2c.write(self._buf)

    def _read_block(self, start, length) -> bytearray:
        """Return byte array of values from start address to length."""
        result = bytearray(length)
        with self._i2c as i2c:
            i2c.write(bytes((start,)))
            i2c.readinto(result)
        return result

    def _write_block(self, start, data):
        """Write out data beginning at start address."""
        with self._i2c as i2c:
            i2c.write(bytes((start,)) + data)

    def write_config(self, config_info) -> None:
        """Write configuration set to TS20
        config_info is array of tuples (reg_addr, reg_val)
        """
        for reg_addr, reg_val in config_info:
            self._write_register(reg_addr, reg_val)

    def read_touches(self):
        """Read back touches
        Return list of booleans, one per pad.
        """
        raw_touch = self._read_block(_TS20_OUTPUT1, 3)
        # convert 3 bytes of raw touch data to single int bitfield
        t = raw_touch[0] | (raw_touch[1] << 7) | (raw_touch[2] << 15)
        # turn bitfield into list
        touches = [t >> i & 1 for i in range(21)]  # bit21 is "isnoisy"
        return touches

    # def set_response_speed(self,

    def set_pad_sensitivities(self, values):
        """Set sensitivies for all pads
        'values' is a 20-element list of pad sensitivies, each element
        from 0-15 (most sensitive to least)
        """
        sens_vals = bytearray(11)
        sens_vals[0] = values[1] << 4 | values[0]  # ch2,1
        sens_vals[1] = values[3] << 4 | values[2]  # ch4,3
        sens_vals[2] = values[5] << 4 | values[4]  # ch6,5
        sens_vals[3] = 0b1111 << 4 | values[6]  # ch-,7
        sens_vals[4] = values[8] << 4 | values[7]  # ch9,8
        sens_vals[5] = values[10] << 4 | values[9]  # ch11,10
        sens_vals[6] = values[12] << 4 | values[11]  # ch13,12
        sens_vals[7] = values[14] << 4 | values[13]  # ch15,14
        sens_vals[8] = values[16] << 4 | values[15]  # ch15,14
        sens_vals[9] = values[18] << 4 | values[17]  # ch15,14
        sens_vals[10] = values[19] << 4 | values[19]  # ch-,20
        return self._write_block(_TS20_SEN_PWM1, sens_vals)
