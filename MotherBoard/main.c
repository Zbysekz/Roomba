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

//#define DEBUG	// show debug messages on UART?


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

long out1,out2,integ_err1,integ_err2;
long Kp=4000,Kd=100,Ki=400,Ko=1,
		err,last_err1,last_err2;

volatile uint32_t enkL,enkR,distanceL,distanceR;
volatile int speedL,speedR,//actual speed
speedReqL,speedReqR,//requested speed
speedReq2L,speedReq2R;//ramped requested speed

volatile uint8_t speedRamp=1;//how is the ramp steep
volatile uint16_t distanceReq=0,distanceReq_last=0;//required distance to travel

uint8_t sideSensors[6],cliffSensors[4],bumpSensorL,bumpSensorR,dirtSensor,motorRswitch,motorLswitch,auxWheelSig;
uint8_t stopWhenBump=1;

#ifdef DEBUG
static FILE uart_str = FDEV_SETUP_STREAM(uart_putchar, NULL, _FDEV_SETUP_WRITE);
#endif

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

	#ifdef DEBUG
	USARTInit();
	stdout = &uart_str;
	#endif

	_delay_s(1);

	InitCRC();//calculate table for fast CRC calculation

	#ifdef DEBUG
	printf("START!\n");
	#endif

	sei();

	while(1){

		UpdateTxData();

		ReadMUX();

		//now stop IRFREQ (OC2)reset IRFREQ and set CTXIR1
		TCCR2 = 0;
		clearBit(&pIRFREQ,IRFREQ);
		setBit(&pCTXIR1,CTXIR1);
		clearBit(&pCTXIR2,CTXIR2);
		_delay_ms(1);//10
		auxWheelSig = getBit(pAUXWHEEL,AUXWHEEL);

		TCCR2 = (1<<WGM21) | (1<<WGM20) | (1<<COM21) | (1<<CS22);
		_delay_ms(1);
		//////////////////////

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

		////////////////////////////////
		//printf("ramp: %d,reqL: %d",speedRamp,speedReqL);

		////////////DISTANCE MEASUREMENT///////////
		if((distanceReq_last==0 && distanceReq!=0)){//if request to measure distance has arrived, reset distance measurement
			distanceL=0;distanceR=0;
		}

		if(distanceReq>0 && distanceReq<=(distanceL+distanceR)/2){//stop when we have traveled required distance
			speedReqR=0;speedReqL=0;//stop by ramp
			distanceReq=0;//reset requirement
		}

		distanceReq_last=distanceReq;

		////////////RAMPING////////////////////////
		if(speedReq2L>speedReqL){
			speedReq2L-=speedRamp;
			if(speedReq2L<speedReqL)speedReq2L=speedReqL;//prevent overstepping
		}else if(speedReq2L<speedReqL){
			speedReq2L+=speedRamp;
			if(speedReq2L>speedReqL)speedReq2L=speedReqL;//prevent overstepping
		}

		if(speedReq2R>speedReqR){
			speedReq2R-=speedRamp;
			if(speedReq2R<speedReqR)speedReq2R=speedReqR;//prevent overstepping
		}else if(speedReq2R<speedReqR){
			speedReq2R+=speedRamp;
			if(speedReq2R>speedReqR)speedReq2R=speedReqR;//prevent overstepping
		}


		////////////STOP WHEN BUMP FUNCTION////////
		if(stopWhenBump){
			if(bumpSensorL==0 || bumpSensorR==0){
				//if we stuck to obstacle in front and we are moving forward, stop
				if(speedReqR>0||speedReqL>0||speedReq2R>0||speedReq2L>0){
					speedReqR=0;
					speedReqL=0;
					speedReq2R=0;
					speedReq2L=0;
				}
			}
		}


		//PID REGULATION
		//////LEFT MOTOR//////
		if(out1>0)
			err=(speedReq2L/10)-speedL;//actual speed positive
		else
			err=(speedReq2L/10)+speedL;//actual speed negative

		out1 =(Kp*err - Kd*(last_err1-err) + Ki*integ_err1)/Ko;
		last_err1=err;

		if(out1>=100000)out1=100000;
		else if(out1<=-100000)out1=-100000;
		else integ_err1+=err;

		if(speedReq2L==0){out1=0;integ_err1=0;}

		if(out1==0)MotorL_stop();else
		if(out1<0)MotorL_bck(-out1/1000);else
		if(out1>0)MotorL_fwd(out1/1000);

		//////RIGHT MOTOR//////
		if(out2>0)
			err=(speedReq2R/10)-speedR;//actual speed positive
		else
			err=(speedReq2R/10)+speedR;//actual speed negative

		out2 =(Kp*err - Kd*(last_err2-err) + Ki*integ_err2)/Ko;
		last_err2=err;

		if(out2>=100000)out2=100000;
		else if(out2<=-100000)out2=-100000;
		else integ_err2+=err;

		if(speedReq2R==0){out2=0;integ_err2=0;}

		if(out2==0)MotorR_stop();else
		if(out2<0)MotorR_bck(-out2/1000);else
		if(out2>0)MotorR_fwd(out2/1000);

		////////////////////////

		if(integ_err1>20000)integ_err1=20000;
		else if(integ_err1<-20000)integ_err1=-20000;
		if(integ_err2>20000)integ_err2=20000;
		else if(integ_err2<-20000)integ_err2=-20000;




		//_delay_ms(20);
	}

return 0;
}

// Timer 0 overflow interrupt service routine    // Clock value: 15 Hz
ISR(TIMER0_OVF_vect)
{
		speedL=enkL;
		speedR=enkR;

		distanceL+=enkL;
		distanceR+=enkR;

		enkL=0;enkR=0;

}
ISR(INT0_vect){
	enkL++;
}
ISR(INT1_vect){
	enkR++;
}

void ReadMUX(){

/////////////////////////////FIRST PACK OF IRs (for preventing beam interference)
	clearBit(&pCTXIR1,CTXIR1);
	setBit(&pCTXIR2,CTXIR2);

	clearBit(&pSel0,Sel0);//4
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);
	_delay_ms(1);

	sideSensors[1] = getModulatedValue(0);//MUX1

	setBit(&pSel0,Sel0);//1
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	sideSensors[4] = getModulatedValue(0);//MUX1

	setBit(&pSel0,Sel0);//3
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	sideSensors[2] = getModulatedValue(0);//MUX1

	/////////////////////////////////////

	clearBit(&pSel0,Sel0);//0
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	cliffSensors[3] = getModulatedValue(3);//MUX2

	setBit(&pSel0,Sel0);//1
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	bumpSensorR = getModulatedValue(3)>200?1:0;//MUX2

	clearBit(&pSel0,Sel0);//2
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	bumpSensorL = getModulatedValue(3)>200?1:0;//MUX2

	setBit(&pSel0,Sel0);//3
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	cliffSensors[2] = getModulatedValue(3);//MUX2

	clearBit(&pSel0,Sel0);//4
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);
	_delay_ms(1);

	dirtSensor = getModulatedValue(3);//MUX2

	setBit(&pSel0,Sel0);//5
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);
	_delay_ms(1);

	cliffSensors[0] = getModulatedValue(3);//MUX2

	////////////RESERVE Y6/////////////////////

	setBit(&pSel0,Sel0);//7
	setBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);
	_delay_ms(1);


	cliffSensors[1] = getModulatedValue(3);//MUX2

/////////////////////////////SECOND PACK OF IRs (for preventing beam interference)
	setBit(&pCTXIR1,CTXIR1);
	clearBit(&pCTXIR2,CTXIR2);

	clearBit(&pSel0,Sel0);//0
	clearBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	sideSensors[3] = getModulatedValue(0);//MUX1

	setBit(&pSel0,Sel0);//5
	clearBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);
	_delay_ms(1);

	sideSensors[0] = getModulatedValue(0);//MUX1

	clearBit(&pSel0,Sel0);//2
	setBit(&pSel1,Sel1);
	clearBit(&pSel2,Sel2);
	_delay_ms(1);

	sideSensors[5] = getModulatedValue(0);//MUX1


	//NOT DEPENDENT ON CTXIR

	clearBit(&pSel0,Sel0);//6
	setBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);
	_delay_ms(1);

	motorRswitch = ReadADC(0)>200?0:1;//MUX1

	setBit(&pSel0,Sel0);//7
	setBit(&pSel1,Sel1);
	setBit(&pSel2,Sel2);
	_delay_ms(1);

	motorLswitch = ReadADC(0)>200?0:1;//MUX1


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
