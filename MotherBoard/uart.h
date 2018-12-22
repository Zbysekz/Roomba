/*
 * uart.h
 *
 *  Created on: 19. 4. 2016
 *      Author: Zbysek
 */

#ifndef UART_H_
#define UART_H_

#include <stdio.h>

void USARTInit(void);
int uart_putchar(char c, FILE *stream);
void USART_Transmit( uint8_t data );

#endif /* UART_H_ */
