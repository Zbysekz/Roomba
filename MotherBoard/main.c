/*
 * main.c
 *
 *  Created on: 3. 4. 2016
 *      Author: Zbysek
 */

#include <avr/io.h>
#include <util/delay.h>
#include "main.h"
#include "uart.h"
//#include <stdlib.h>
#include <avr/interrupt.h>
//#include <avr/pgmspace.h>
#include <avr/sleep.h>

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>

/***************************************************/

#define DEBUG 1	// show debug messages on UART?


#define pSel0 PORTC
#define Sel0 PC1

#define pSel1 PORTC
#define Sel1 PC2

#define pSel2 PORTC
#define Sel2 PC6

#define pML1S PORTB
#define ML1S PB0

#define pMP1S PORTD
#define MPS1S PD6

#define pML2S PORTD
#define ML2S PD7

#define pMP2S PORTD
#define MP2S PD5

#define pCTXIR1 PORTD
#define CTXIR1 PD0

#define pCTXIR2 PORTB
#define CTXIR2 PB5

#define pAUXWHEEL PORTB
#define AUXWHEEL PB4

#define pPWM1 PORTB
#define PWM1 PB1

#define pPWM2 PORTB
#define PWM2 PCB2

#define pIRFREQ PORTB
#define IRFREQ PB3

static FILE uart_str = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);



/***************************************************/
int main(void)
{

	//nastavit výstupy
	//DDRB = (1<<PB0) | (1<<PB1) | (1<<PB2);

	//natavit výstupy
	//DDRD =1<<PD5;

	//natavit výstupy
	//DDRC =(1<<PC2) | (1<<PC3);

	// Timer/Counter 0 initialization
	// Clock source: System Clock
	// Clock value: 15,625 kHz
	TCCR0=0x05;
	TCNT0=0x00;

	// Timer(s)/Counter(s) Interrupt(s) initialization
	TIMSK=0x01;

	//external interrupt INT0 - accel
	//GICR=(1<<INT0);
	//MCUCR = (1<<ISC01);//pro accel sestupna

	// Use the Power Down sleep mode
	//set_sleep_mode(SLEEP_MODE_PWR_DOWN);

	//init interrupt
	sei();

	//Initialize USART
	USARTInit();

	_delay_s(1);

	stdout = &uart_str;

	if(DEBUG)printf("START!\n");

	while(1){//lze blokovat pomocí delay

	}

return 0;
}

// Timer 0 overflow interrupt service routine    // Clock value: 15 Hz
ISR(TIMER0_OVF_vect)
{

}
ISR(INT0_vect){

}
ISR(INT1_vect){

}

void _delay_s(int sec){
	for(int c=0;c<sec*10;c++)
		_delay_ms(100);
}

void setBit(volatile uint8_t *port, int bit){
	*port|=(1<<bit);
}
void clearBit(volatile uint8_t *port, int bit){
	*port&=0xFF-(1<<bit);
}
uint8_t getBit(volatile uint8_t port, int bit){
	if((port&(1<<bit))==0)return 0;else return 1;
}
