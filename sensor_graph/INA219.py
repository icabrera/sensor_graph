from ctypes import *
import ctypes
import math



DECIMALS = 2
STR_FLOAT_MODIFIER = "%3." + str(DECIMALS) + "f"

INA219_REG_CONFIG = 0x00
INA219_REG_SHUNTVOLTAGE = 0x01
INA219_REG_BUSVOLTAGE = 0x02
INA219_REG_POWER = 0x03
INA219_REG_CURRENT = 0x04
INA219_REG_CALIBRATION = 0x05

class INA219:


                           						
    def __init__(self, address, r_shunt):
        self.last_bv = 0
        self.last_c = 0
        self.last_p = 0
        self.MAX_VOLTS = 32
        self.MAX_AMPS = 0.4
        self.bus_voltage_text = None
        self.gain_text = None
        self.badcres_text = None
        self.sadcres_text = None
        self.mode_text = None
            
        self.r_shunt = r_shunt
        self.i2c_address = address
        self.ch341 = cdll.LoadLibrary("CH341DLLA64.DLL")
        
        self.bus_voltage_ranges = { "BUS_VOLTAGE_RANGE_16V":0x0000, 
                                    "BUS_VOLTAGE_RANGE_32V":0x2000 }    
 
        self.bus_voltage_values = { "BUS_VOLTAGE_RANGE_16V":           16,     
                                    "BUS_VOLTAGE_RANGE_32V":           32 }
                           
        self.gain_ranges   = { "GAIN_1_40MV":                          0x0000,  
                               "GAIN_2_80MV":                          0x0800,   
                               "GAIN_4_160MV":                         0x1000, 
                               "GAIN_8_320MV":                         0x1800 }
                               
        self.gain_values   = { "GAIN_1_40MV":                          1,  
                               "GAIN_2_80MV":                          2,   
                               "GAIN_4_160MV":                         4, 
                               "GAIN_8_320MV":                         8 }
                                                          
        self.badcres_ranges = {"BUS_VOLTAGE_ADC_RES_9BIT":             0x0000, 
                               "BUS_VOLTAGE_ADC_RES_10BIT":            0x0080, 
                               "BUS_VOLTAGE_ADC_RES_11BIT":            0x0100, 
                               "BUS_VOLTAGE_ADC_RES_12BIT":            0x0180, 
                               "BUS_VOLTAGE_ADC_RES_12BIT_2S_1060US":  0x0480, 
                               "BUS_VOLTAGE_ADC_RES_12BIT_4S_2130US":  0x0500, 
                               "BUS_VOLTAGE_ADC_RES_12BIT_8S_4260US":  0x0580, 
                               "BUS_VOLTAGE_ADC_RES_12BIT_16S_8510US": 0x0600, 
                               "BUS_VOLTAGE_ADC_RES_12BIT_32S_17MS":   0x0680, 
                               "BUS_VOLTAGE_ADC_RES_12BIT_64S_34MS":   0x0700, 
                               "BUS_VOLTAGE_ADC_RES_12BIT_128S_69MS":  0x0780 }
                               
        self.sadcres_ranges = { "SHUNT_ADC_RES_9BIT_1S_84US":          0x0000, 
                               "SHUNT_ADC_RES_10BIT_1S_148US":         0x0008, 
                               "SHUNT_ADC_RES_11BIT_1S_276US":         0x0010, 
                               "SHUNT_ADC_RES_12BIT_1S_532US":         0x0018, 
                               "SHUNT_ADC_RES_12BIT_2S_1060US":        0x0048, 
                               "SHUNT_ADC_RES_12BIT_4S_2130US":        0x0050, 
                               "SHUNT_ADC_RES_12BIT_8S_4260US":        0x0058, 
                               "SHUNT_ADC_RES_12BIT_16S_8510US":       0x0060,
                               "SHUNT_ADC_RES_12BIT_32S_17MS":         0x0068, 
                               "SHUNT_ADC_RES_12BIT_64S_34MS":         0x0070, 
                               "SHUNT_ADC_RES_12BIT_128S_69MS":        0x0078 }
                               
        self.mode_ranges   = { "POWER_DOWN":                           0x00, 
                               "SVOLT_TRIGGERED":                      0x01, 
                               "BVOLT_TRIGGERED":                      0x02, 
                               "SANDBVOLT_TRIGGERED":                  0x03, 
                               "ADC_OFF":                              0x04, 
                               "SHUNT_VOLTAGE_CONTINUOUS":             0x05, 
                               "BUS_VOLTAGE_CONTINUOUS":               0x06, 
                               "SHUNT_AND_BUS_VOLTAGE_CONTINUOUS":     0x07 }
                           
    
    def convert_bytes2int(self, input):
        value_list = bytes(input)
        value_int = value_list[1] + value_list[0]*256
        return value_int
    
    def config_options(self, bus_voltage, gain, badcres, sadcres, mode):
        self.bus_voltage_text = bus_voltage
        self.gain_text = gain
        self.badcres_text = badcres
        self.sadcres_text = sadcres
        self.mode_text = mode
        
        self.MAX_VOLTS = int( self.bus_voltage_values[self.bus_voltage_text] )
        self.gain = int( self.gain_values[self.gain_text] )        
        
        self.vshunt_max = 0.04 * self.gain
        self.max_current_possible = self.vshunt_max / self.r_shunt
        self.MAX_AMPS = self.max_current_possible
        self.min_lsb = self.MAX_AMPS / 32768
        self.max_lsb = self.MAX_AMPS / 4096
        self.curr_lsb = self.calculate_current_lsb( self.min_lsb, self.max_lsb )
        self.calib = math.trunc(0.04096/(self.curr_lsb * self.r_shunt))
        
        self.power_multiplier = 20 * self.curr_lsb
        
        if self.bus_voltage_text != None and self.gain_text != None and self.badcres_text != None and self.sadcres_text != None and self.mode_text != None:
            self.config = self.bus_voltage_ranges[self.bus_voltage_text] | self.gain_ranges[self.gain_text] | self.badcres_ranges[self.badcres_text] | self.sadcres_ranges[self.sadcres_text] | self.mode_ranges[self.mode_text]

    
    def open(self, index):
        return self.ch341.CH341OpenDevice(index)
        
        
    def reset(self, index):
        return self.ch341.CH341ResetDevice(index)
    
    
    def stop(self, index):
        return self.ch341.CH341CloseDevice(index)
    
    
    def setStream(self, index, index2):
        return self.ch341.CH341SetStream(index, index2)

    
    def calibration(self):
        data_calib = [c_uint8(self.i2c_address), c_uint8(INA219_REG_CALIBRATION), c_uint8(self.calib>>8), c_uint8(self.calib)]
        IntArray4 = ctypes.c_uint8 * len(data_calib)
        parameter_array = IntArray4(*data_calib)
        self.ch341.CH341StreamI2C(0, len(data_calib), parameter_array, 0, None)

        
    def configuration(self):
        data_config = [c_uint8(self.i2c_address), c_uint8(INA219_REG_CONFIG), c_uint8(self.config>>8), c_uint8(self.config)]
        IntArray4 = ctypes.c_uint8 * len(data_config)
        parameter_array = IntArray4(*data_config)
        self.ch341.CH341StreamI2C(0, len(data_config), parameter_array, 0, None)
        
        
    def get_bus_voltage(self):
        data_voltage = [c_uint8(self.i2c_address), c_uint8(INA219_REG_BUSVOLTAGE)]
        output = [c_uint8(0), c_uint8(0)]
        Uint8Array = ctypes.c_uint8 * len(data_voltage)
        parameter_array = Uint8Array(*data_voltage)
        voltage_output = ctypes.c_uint8 * 2
        output = voltage_output(*output)
        self.ch341.CH341StreamI2C(0, len(data_voltage), parameter_array, len(output), output)
        voltage_value = self.convert_bytes2int(output)
        voltage_value = ( voltage_value >> 3 ) * 4
        voltage_value = voltage_value * 0.001
        if voltage_value > self.MAX_VOLTS:
            voltage_value = self.last_bv
        else:
            self.last_bv = voltage_value
        return voltage_value
        

    def get_current(self):
        data_current = [c_uint8(self.i2c_address), c_uint8(INA219_REG_CURRENT)]
        output = [c_uint8(0), c_uint8(0)]
        Uint8Array = ctypes.c_uint8 * len(data_current)
        parameter_array = Uint8Array(*data_current)
        current_output = ctypes.c_uint8 * 2
        output = current_output(*output)
        self.ch341.CH341StreamI2C(0, len(data_current), parameter_array, len(output), output)
        current_value = self.convert_bytes2int(output) * self.curr_lsb
        if current_value > self.MAX_AMPS:
            current_value = self.last_c
        else:
            self.last_c = current_value            
        return current_value

        
    def get_power(self):
        data_power = [c_uint8(self.i2c_address), c_uint8(INA219_REG_POWER)]
        output = [c_uint8(0), c_uint8(0)]
        Uint8Array = ctypes.c_uint8 * len(data_power)
        parameter_array = Uint8Array(*data_power)
        power_output = ctypes.c_uint8 * 2
        output = power_output(*output)
        self.ch341.CH341StreamI2C(0, len(data_power), parameter_array, len(output), output)
        return self.convert_bytes2int(output) * self.power_multiplier


    def format(self, value, unit):
        return str(STR_FLOAT_MODIFIER % value) + " " + unit
        

    def get_max_volts(self):
        return self.MAX_VOLTS
        
        
    def get_max_amps(self):
        return self.MAX_AMPS    
    

    def calculate_current_lsb(self, A, B):
        epsilon = min(1e-7, (B - A) / 100)
        eps_inv = 1/epsilon
        number = A + epsilon
        while number < B:
            candidate = int(number*eps_inv)
            if candidate % 10 == 0 and candidate % 5 == 0 and candidate % 25 == 0 and candidate % 100 == 0 and candidate % 3 != 0 and candidate % 7 != 0 and candidate % 200 != 0:
                return candidate/eps_inv
            number += epsilon
        return None 
