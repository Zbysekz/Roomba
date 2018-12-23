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
#define MP1S PD6

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
#define PWM2 PB2

#define pIRFREQ PORTB
#define IRFREQ PB3

static FILE uart_str = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);

uint32_t enkL,enkP;

uint8_t motDirL,motDirP;
uint16_t motSpeedL,motSpeedP;


/***************************************************/
int main(void)
{

	//set outputs
	DDRC = (1<<Sel0) | (1<<Sel1) | (1<<Sel2);

	DDRB = (1<<ML1S) | (1<<CTXIR2) | (1<<PWM1) | (1<<PWM2) | (1<<IRFREQ);

	DDRD = (1<<MP1S) | (1<<ML2S) | (1<<MP2S) | (1<<CTXIR1);

	// Timer/Counter 0 initialization
	// Clock source: System Clock
	// Clock value: 15 Hz
	TCCR0=(1<<CS02) | (1<<CS00);//div 1024
	TCNT0=0x00;
	// Timer(s)/Counter(s) Interrupt(s) initialization
	TIMSK=(1<<TOIE0);//overflow enable

	// Timer/Counter 1 initialization
	// Clock source: System Clock
	// Clock value: 244 Hz
	// Mode: Fast PWM 8 bit TOP, non-inverting

	TCCR1A = (1<<WGM10) | (1<<COM1A1)| (1<<COM1B1);
	TCCR1B = (1<<CS11) | (1<<CS10);//div 64

	TCNT1=0x00;
	OCR1A=0x19;//10%
	OCR1B=0x19;//10%

	// Timer/Counter 2 initialization
	// Clock source: System Clock
	// Clock value: 244 Hz
	// Mode: Fast PWM 8 bit TOP, non-inverting

	TCCR2 = (1<<WGM21) | (1<<WGM20) | (1<<COM21) | (1<<CS22);

	TCNT2=0x00;
	OCR2=64;//25% - 500us


	//external interrupt INT0 and INT1
	GICR=(1<<INT1)|(1<<INT0);
	MCUCR = (1<<ISC11) | (1<<ISC01);//react on falling edge

	// ADC initialization
	ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS0); //division factor:32

	//Initialize USART
	USARTInit();

	_delay_s(1);

	stdout = &uart_str;

	if(DEBUG)printf("START!\n");

	sei();

	while(1){
		printf("L:%lu P:%lu\n",enkL,enkP);
	}

return 0;
}

// Timer 0 overflow interrupt service routine    // Clock value: 15 Hz
ISR(TIMER0_OVF_vect)
{

}
ISR(INT0_vect){
	enkL++;
}
ISR(INT1_vect){
	enkP++;
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
