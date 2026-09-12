#ifndef UART_APP_H
#define UART_APP_H

#include "main.h"
extern UART_HandleTypeDef huart6;
extern DMA_HandleTypeDef hdma_usart6_rx;
extern DMA_HandleTypeDef hdma_usart6_tx;
void UART_rx_init(void);
void UART_App_Process(void);
void UART_App_ProcessDMA(void);

#endif