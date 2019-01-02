/*
 * twi.c
 *
 *  Created on: Jan 2, 2019
 *      Author: zz
 */

#include <compat/twi.h>
#include <avr/interrupt.h>
#include "twi.h"

#define TWI_SLAVE_ADDR       0x4E
#define BUFFSIZE 50

uint8_t rxBuffer[BUFFSIZE];
uint8_t txBuffer[BUFFSIZE];


volatile uint8_t i2c_state;
volatile uint8_t twi_status;

volatile uint8_t regaddr; // Store the Requested Register Address
volatile uint8_t regdata; // Store the Register Address Data

///////CRC//////////////

/*
 * The width of the CRC calculation and result.
 * Modify the typedef for a 16 or 32-bit CRC standard.
 */

#define WIDTH  (8 * sizeof(crc))
#define TOPBIT (1 << (WIDTH - 1))

#define POLYNOMIAL 0xD8  /* 11011 followed by 0's */
//////////////////////////

static crc crcTable[256];

void InitCRC(void)
{
    crc  remainder;
    //Compute the remainder of each possible dividend.
    for (int dividend = 0; dividend < 256; ++dividend)
    {
        /*
         * Start with the dividend followed by zeros.
         */
        remainder = dividend << (WIDTH - 8);
        /*
         * Perform modulo-2 division, a bit at a time.
         */
        for (uint8_t bit = 8; bit > 0; --bit)
        {
            // Try to divide the current data bit.
            if (remainder & TOPBIT)
            {
                remainder = (remainder << 1) ^ POLYNOMIAL;
            }
            else
            {
                remainder = (remainder << 1);
            }
        }
        // Store the result into the table.
        crcTable[dividend] = remainder;
    }

}   /* crcInit() */

crc CalculateCRC(uint8_t const message[], int nBytes)
{
    uint8_t data;
    crc remainder = 0;
    //Divide the message by the polynomial, a byte at a time.
    for (int byte = 0; byte < nBytes; ++byte)
    {
        data = message[byte] ^ (remainder >> (WIDTH - 8));
        remainder = crcTable[data] ^ (remainder << 8);
    }
    //The final remainder is the CRC.
    return (remainder);
}   /* crcFast() */

void TWI_Init(){
	// Initial I2C Slave
	TWAR = TWI_SLAVE_ADDR & 0xFE;    // Set I2C Address, Ignore I2C General Address 0x00
	TWDR = 0x00;            // Default Initial Value

	// Start Slave Listening: Clear TWINT Flag, Enable ACK, Enable TWI, TWI Interrupt Enable
	TWCR = (1<<TWINT) | (1<<TWEA) | (1<<TWEN) | (1<<TWIE);

	// Initial Variable Used
	regaddr=0;
	regdata=0;
}


void TWI_SlaveAction(uint8_t rw_status)
{
	if(regaddr==0){// this is just for communication check
		if (rw_status == 0)
			regdata = 66;
	}else if(regaddr == 200){//master is sending CRC to us or wants CRC of our data
		if (rw_status == 0){
			regdata = CalculateCRC(txBuffer,5);
			UpdateTxData();//update next data
		}else
			ValidateData(regdata);
	}else if(regaddr>0 && regaddr<BUFFSIZE+1){
		if(rw_status == 0){ //read
			regdata = txBuffer[regaddr-1];
		}else{//write
			rxBuffer[regaddr-1] = regdata;
		}
    }
}

ISR(TWI_vect)
{
    // Disable Global Interrupt
    cli();

    // Get TWI Status Register, mask the prescaler bits (TWPS1,TWPS0)
    twi_status=TWSR & 0xF8;

    switch(twi_status) {
        case TW_SR_SLA_ACK: // 0x60: SLA+W received, ACK returned
            i2c_state=0;    // Start I2C State for Register Address required
            break;

        case TW_SR_DATA_ACK:    // 0x80: data received, ACK returned
            if (i2c_state == 0) {
                regaddr = TWDR; // Save data to the register address
                i2c_state = 1;
            } else {
                regdata = TWDR; // Save to the register data
                i2c_state = 2;
            }
            break;

        case TW_SR_STOP:    // 0xA0: stop or repeated start condition received while selected
            if (i2c_state == 2) {
            	TWI_SlaveAction(1);    // Call Write I2C Action (rw_status = 1)
                i2c_state = 0;      // Reset I2C State
            }
            break;

        case TW_ST_SLA_ACK: // 0xA8: SLA+R received, ACK returned
        case TW_ST_DATA_ACK:    // 0xB8: data transmitted, ACK received
            if (i2c_state == 1) {
            	TWI_SlaveAction(0);    // Call Read I2C Action (rw_status = 0)
                TWDR = regdata;     // Store data in TWDR register
                i2c_state = 0;      // Reset I2C State
            }
            break;

        case TW_ST_DATA_NACK:   // 0xC0: data transmitted, NACK received
        case TW_ST_LAST_DATA:   // 0xC8: last data byte transmitted, ACK received
        case TW_BUS_ERROR:  // 0x00: illegal start or stop condition
        default:
            i2c_state = 0;  // Back to the Begining State
    }
    // Clear TWINT Flag
    TWCR |= (1<<TWINT);
    // Enable Global Interrupt
    sei();
}

void ValidateData(uint8_t crc){
	//validate if received data are ok
	if(CalculateCRC(rxBuffer,5) == crc){
		//we can now copy rxBuffer data to specific vars
		;
	}
}

void UpdateTxData(){//called at the beginning and every time after CRC value is read by master

	txBuffer[0]=10;
	txBuffer[1]=11;
	txBuffer[2]=12;
	txBuffer[3]=13;
	txBuffer[4]=14;

	//sideSensors[6],cliffSensors[4],bumpSensors[2],dirtSensor,motorPswitch,motorLswitch,auxWheelSig;

}


