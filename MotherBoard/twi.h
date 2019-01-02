/*
 * twi.h
 *
 *  Created on: Jan 2, 2019
 *      Author: zz
 */

#ifndef TWI_H_
#define TWI_H_

typedef uint8_t crc;

void TWI_Init();
void TWI_slave_action(uint8_t rw_status);

void ValidateData(uint8_t crc);
void UpdateTxData();

void InitCRC(void);
crc CalculateCRC(uint8_t const message[], int nBytes);

#endif /* TWI_H_ */
