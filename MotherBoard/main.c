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
#include "twi.h"
#include <avr/interrupt.h>

#include <ctype.h>
#include <stdint.h>
#include <stdio.h>

/***************************************************/

#define DEBUG 0	// show debug messages on UART? - warning! affect functionality of CTXIR1 pin(RxD)


#define pSel0 PORTC
#define Sel0 PC1

#define pSel1 PORTC
#define Sel1 PC2

#define pSel2 PORTD
#define Sel2 PD4

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

#define pAUXWHEEL PINB
#define AUXWHEEL PB4

#define pPWM1 PORTB
#define PWM1 PB1

#define pPWM2 PORTB
#define PWM2 PB2

#define pIRFREQ PORTB
#define IRFREQ PB3


//static FILE uart_str = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);

uint32_t enkL,enkP;

int8_t cmdMotL,cmdMotR;

uint8_t sideSensors[6],cliffSensors[4],bumpSensors[2],dirtSensor,motorRswitch,motorLswitch,auxWheelSig;

static FILE uart_str = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);


/***************************************************/
int main(void)
{

	//set outputs
	DDRC = (1<<Sel0) | (1<<Sel1);

	DDRB = (1<<ML1S) | (1<<CTXIR2) | (1<<PWM1) | (1<<PWM2) | (1<<IRFREQ);

	DDRD = (1<<MP1S) | (1<<ML2S) | (1<<MP2S) | (1<<CTXIR1) | (1<<Sel2);

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
	OCR2=191;//75% - 500us negative puls


	//external interrupt INT0 and INT1
	GICR=(1<<INT1)|(1<<INT0);
	MCUCR = (1<<ISC11) | (1<<ISC01);//react on falling edge


	TWI_Init();

	// ADC initialization
	ADCSRA = (1 << ADEN) | (1 << ADPS2) | (1 << ADPS0); //division factor:32

	//Initialize USART
	if(DEBUG)USARTInit();

	_delay_s(1);

	stdout = &uart_str;

	InitCRC();//calculate table for fast CRC calculation

	//if(DEBUG)printf("START!\n");

	sei();

	while(1){

		UpdateTxData();

		setBit(&pCTXIR1,CTXIR1);
		setBit(&pCTXIR2,CTXIR2);

		ReadMUX();

		auxWheelSig = getBit(pAUXWHEEL,AUXWHEEL);

		if(cmdMotL==0)
			MotorL_stop();
		else if(cmdMotL>0)
			MotorL_fwd(cmdMotL);
		else if(cmdMotL<0)
			MotorL_bck(-cmdMotL);

		if(cmdMotR==0)
			MotorR_stop();
		else if(cmdMotR>0)
			MotorR_fwd(cmdMotR);
		else if(cmdMotR<0)
			MotorR_bck(-cmdMotR);



		/*printf("side:");

		for(int i=0;i<6;i++){
			printf(" %d,",sideSensors[i]);
		}

		printf("cliff:");

		for(int i=0;i<4;i++){
			printf(" %d,",cliffSensors[i]);
		}

		printf("bump1: %d,bump2: %d",bumpSensors[0],bumpSensors[1]);

		printf("dirt: %d,motorL_SW: %d,motorP_SW: %d, auxwheel:%d",dirtSensor,motorLswitch,motorPswitch,auxWheelSig);

		printf("\n");*/

		_delay_ms(100);
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

void ReadMUX(){

	clearBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	sideSensors[3] = getModulatedValue(0);//MUX1

	setBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	sideSensors[4] = getModulatedValue(0);//MUX1

	clearBit(&pSel0,Sel0);
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	sideSensors[5] = getModulatedValue(0);//MUX1

	setBit(&pSel0,Sel0);
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	sideSensors[2] = getModulatedValue(0);//MUX1

	clearBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);

	_delay_ms(1);

	sideSensors[1] = getModulatedValue(0);//MUX1

	setBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);

	_delay_ms(1);

	sideSensors[0] = getModulatedValue(0);//MUX1

	clearBit(&pSel0,Sel0);
	setBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);

	_delay_ms(1);

	motorRswitch = getModulatedValue(0);//MUX1

	setBit(&pSel0,Sel0);
	setBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);

	_delay_ms(1);

	motorLswitch = getModulatedValue(0);//MUX1

	/////////////////////////////////////
	clearBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	cliffSensors[3] = getModulatedValue(3);//MUX2

	setBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	bumpSensors[0] = getModulatedValue(3);//MUX2

	clearBit(&pSel0,Sel0);
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	bumpSensors[1] = getModulatedValue(3);//MUX2

	setBit(&pSel0,Sel0);
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);

	_delay_ms(1);

	cliffSensors[2] = getModulatedValue(3);//MUX2

	clearBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);

	_delay_ms(1);

	dirtSensor = getModulatedValue(3);//MUX2

	setBit(&pSel0,Sel0);
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);

	_delay_ms(1);

	cliffSensors[0] = getModulatedValue(3);//MUX2

	////////////RESERVE Y6/////////////////////

	setBit(&pSel0,Sel0);
	setBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);

	_delay_ms(1);


	cliffSensors[1] = getModulatedValue(3);//MUX2


}

uint8_t getModulatedValue(uint8_t ADC_channel){
	uint16_t measuredMin,measuredMax,value;

	measuredMin=65535;
	measuredMax=0;

	for(int i=0;i<35;i++){// more than ~2ms
		value = ReadADC(ADC_channel);//takes at least 10 us

		if(value < measuredMin) measuredMin = value;
		if(value > measuredMax) measuredMax = value;
	}

	value = measuredMax-measuredMin;

	if(value>255)value=255;

	return value;

}

void MotorL_fwd(uint8_t speed){//0-100%
	OCR1A=255-(uint16_t)(speed)*255/100;//0-255

	setBit(&pML1S,ML1S);
	clearBit(&pML2S,ML2S);
}
void MotorL_bck(uint8_t speed){//0-100%
	OCR1A=255-(uint16_t)(speed)*255/100;//0-255

	setBit(&pML2S,ML2S);
	clearBit(&pML1S,ML1S);
}
void MotorR_bck(uint8_t speed){//0-100%
	OCR1B=255-(uint16_t)(speed)*255/100;//0-255

	setBit(&pMP1S,MP1S);
	clearBit(&pMP2S,MP2S);
}
void MotorR_fwd(uint8_t speed){//0-100%
	OCR1B=255-(uint16_t)(speed)*255/100;//0-255

	setBit(&pMP2S,MP2S);
	clearBit(&pMP1S,MP1S);
}

void MotorR_stop(){
	OCR1B=0;//0-255

	clearBit(&pMP2S,MP2S);
	clearBit(&pMP1S,MP1S);
}
void MotorL_stop(){
	OCR1A=0;//0-255

	clearBit(&pML2S,ML2S);
	clearBit(&pML1S,ML1S);
}

// Read the 8 most significant bits
// of the AD conversion result
uint16_t ReadADC(uint8_t adc_input) {//read voltages in 0,01V
  ADMUX = adc_input | (1 << REFS0);
// Delay needed for the stabilization of the ADC input voltage
  _delay_us(10);
// Start the AD conversion
  ADCSRA |= (1 << ADSC); // Start conversion
// Wait for the AD conversion to complete
  while (ADCSRA & (1 << ADSC))
    ;
  ADCSRA |= 0x10;
  return ADCW;
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
