
#include <inttypes.h>
void _delay_s(int sec);
void SMSreceived(void);
void setBit(volatile uint8_t *port, int bit);
void clearBit(volatile uint8_t *port, int bit);
uint8_t getBit(volatile uint8_t port, int bit);
void Blik(void);

void MotorL_fwd(uint8_t speed);
void MotorL_bck(uint8_t speed);
void MotorR_fwd(uint8_t speed);
void MotorR_bck(uint8_t speed);
void MotorR_stop();
void MotorL_stop();

uint16_t ReadADC(uint8_t adc_input);

void ReadMUX();

uint8_t getModulatedValue(uint8_t ADC_channel);

extern volatile int speedL,speedR,speedReqL,speedReqR;
extern volatile uint8_t speedRamp;
extern volatile uint8_t standstill;
extern volatile uint16_t distanceReq;

extern uint8_t sideSensors[6],cliffSensors[4],bumpSensorL,bumpSensorR,dirtSensor,motorRswitch,motorLswitch,auxWheelSig;
extern uint8_t stopWhenBump;
