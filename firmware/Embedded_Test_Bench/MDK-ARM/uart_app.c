#include "uart_app.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>

#define UART_APP_BUFFER_SIZE 100

static char tx_buffer[UART_APP_BUFFER_SIZE];
static char rx_buffer[UART_APP_BUFFER_SIZE];
static uint8_t rx_byte;

static volatile uint8_t index = 0;
static volatile uint8_t rx_flag = 0;

void UART_rx_init(void)
{
    HAL_UART_Receive_IT(&huart6, &rx_byte, 1);

}

void UART_App_Process(void){
	        if (rx_flag)
        {
            if (strcmp(rx_buffer, "red on\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_14,GPIO_PIN_SET);
                sprintf(tx_buffer, "LED RED ON");
                HAL_UART_Transmit(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer),100);
            }

            else if (strcmp(rx_buffer, "red off\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_14,GPIO_PIN_RESET);
                sprintf(tx_buffer, "LED RED OFF");
                HAL_UART_Transmit(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer),100);
            }

            else if (strcmp(rx_buffer, "green on\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_12,GPIO_PIN_SET);
                sprintf(tx_buffer, "LED GREEN ON");
                HAL_UART_Transmit(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer),100);
            }

            else if (strcmp(rx_buffer, "green off\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_12,GPIO_PIN_RESET);
                sprintf(tx_buffer, "LED GREEN OFF");
                HAL_UART_Transmit(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer),100);
            }

            else if (strcmp(rx_buffer, "all on\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_14, GPIO_PIN_SET);
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_12,GPIO_PIN_SET );
                sprintf(tx_buffer,"LED GREEN ON\nLED RED ON");
                HAL_UART_Transmit(&huart6, (const uint8_t *)tx_buffer,strlen(tx_buffer),100);
						}

            else if (strcmp(rx_buffer, "all off\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14,GPIO_PIN_RESET);
                HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12, GPIO_PIN_RESET);
                sprintf(tx_buffer,"LED GREEN OFF\nLED RED OFF");
                HAL_UART_Transmit(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer),100);
            }

            else
            {
                sprintf(tx_buffer,"ERROR INVALID COMMAND");
                HAL_UART_Transmit(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer),100);
            }

            rx_flag = 0;
            index = 0;
            HAL_UART_Receive_IT(&huart6,&rx_byte,1);
					}
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART6)
    {
        if (rx_byte == '\n')
        {
            rx_buffer[index] = '\0';

            rx_flag = 1;
        }

        else
        {

            rx_buffer[index] =(char)rx_byte;
            index++;
            HAL_UART_Receive_IT(&huart6,&rx_byte,1);
        }
    }
}

