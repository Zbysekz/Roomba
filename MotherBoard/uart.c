/*
 * uart.c
 *
 *  Created on: 19. 4. 2016
 *      Author: Zbysek
 */
#include "uart.h"
#include <avr/io.h>
#include <avr/interrupt.h>

#define USART_BAUDRATE 9600
#define UBRR_VALUE ((F_CPU / (USART_BAUDRATE * 16UL)) - 1)

void USARTInit(void)
{
	UBRRH = (uint8_t)(UBRR_VALUE>>8);                      // shift the register right by 8 bits
	UBRRL = (uint8_t)UBRR_VALUE;                           // set baud rate
	UCSRB|= (1<<TXEN)|(1<<RXEN);    // enable receiver and transmitter
	//UCSR0C|= (1<<UCSZ00)|(1<<UCSZ01);   // 8bit data format

}
/*
 * Send character c down the UART Tx, wait until tx holding register
 * is empty.
 */
int uart_putchar(char c, FILE *stream)
{

  if (c == '\a')
    {
      fputs("*ring*\n", stderr);
      return 0;
    }

  if (c == '\n')
    uart_putchar('\r', stream);
  loop_until_bit_is_set(UCSRA, UDRE);
  UDR = c;

  return 0;
}

void USART_Transmit( uint8_t data )
{
	/* Wait for empty transmit buffer */
	while ( !( UCSRA & (1<<UDRE)) )
	;
	/* Put data into buffer, sends the data */
	UDR = data;
}
