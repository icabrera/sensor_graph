#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
#include <CH341DLL_EN.h>
#include <stdint.h>
#include "unistd.h"

int i2c_scanner(void);

int main()
{
    i2c_scanner();
    return 0;
}

int i2c_scanner(void)
{
    int address, address_i2c;
    int nDevices = 0;
    byte obyte;

    printf("CH341 I2C Scanner\n");
    HANDLE result = CH341OpenDevice(0);
    if (!FAILED(result))
    {
        printf("Scanning...\n");
        for(address = 1; address < 256; address++ )
        {
            address_i2c = address >> 1;
            //printf("Add = %02X\t", address_i2c);
            CH341ReadI2C (0, address_i2c, 0, &obyte);
            //printf("obyte = %02X\n", obyte);
            if (obyte != 0xFF && address % 2 == 0)
            {
                printf("I2C device found at address 0x%02X 0x%02X\n", address, address_i2c);
                nDevices++;
            }
        }
    }
    CH341CloseDevice(0);
    return nDevices;
}
