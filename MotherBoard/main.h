
#include <inttypes.h>
void _delay_s(int sec);
void SMSreceived(void);
void setBit(volatile uint8_t *port, int bit);
void clearBit(volatile uint8_t *port, int bit);
uint8_t getBit(volatile uint8_t port, int bit);
void Blik(void);

void MotorL_fwd(uint8_t speed);
void MotorL_bck(uint8_t speed);
void MotorP_fwd(uint8_t speed);
void MotorP_bck(uint8_t speed);
void MotorP_stop();
void MotorL_stop();

uint16_t ReadADC(uint8_t adc_input);

void ReadMUX();
