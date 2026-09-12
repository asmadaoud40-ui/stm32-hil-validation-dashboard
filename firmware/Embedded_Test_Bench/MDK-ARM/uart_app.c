#include "uart_app.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>

#define UART_APP_BUFFER_SIZE 100


static char tx_buffer[UART_APP_BUFFER_SIZE];
static char rx_buffer[UART_APP_BUFFER_SIZE];
static char command_buffer[UART_APP_BUFFER_SIZE];  // commande construite ici

static volatile uint8_t rx_flag = 0;

static volatile uint16_t dma_pos = 0; //dernière position annoncée par la callback HAL.
static volatile uint8_t dma_event = 0;
static volatile uint8_t tx_busy = 0;

static uint16_t old_pos = 0;
static uint16_t command_index = 0;

void UART_rx_init(void)
{
	HAL_UARTEx_ReceiveToIdle_DMA(&huart6,(uint8_t *)rx_buffer,UART_APP_BUFFER_SIZE);
}

void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart,uint16_t Size) //st appelée quand HAL détecte un 
{//des événements de réception suivants :idle/Half Transfer DMA /Transfer Complete DMA
    if (huart->Instance == USART6)
    {
        if (HAL_UARTEx_GetRxEventType(huart) == HAL_UART_RXEVENT_IDLE)
        {
            dma_pos = Size;
            dma_event = 1;
        }
    }
}

void UART_App_ProcessDMA(void)
{
    uint16_t current_pos;


    if (dma_event == 0 || rx_flag == 1)//rx flag==1 si j'ai \n
        return;


    current_pos = dma_pos;

    while (old_pos != current_pos)
    {
        char byte = rx_buffer[old_pos];

        old_pos++;

        if (old_pos >= UART_APP_BUFFER_SIZE)
            old_pos = 0;

        if (byte == '\n')
        {
            command_buffer[command_index] = '\0';

            command_index = 0;
            rx_flag = 1;

            return;
        }

        if (command_index < UART_APP_BUFFER_SIZE - 1)
        {
            command_buffer[command_index] = byte;
            command_index++;
        }
    }
		    dma_event = 0;
}
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART6)
    {
        tx_busy = 0;
    }
}

void UART_App_Process(void){

	        if (rx_flag)
        {
					if (tx_busy == 1)
					return;
	
            if (strcmp(command_buffer, "red on\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_14,GPIO_PIN_SET);
                sprintf(tx_buffer, "LED RED ON");
								tx_busy = 1;
                HAL_UART_Transmit_DMA(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer));
            }

            else if (strcmp(command_buffer, "red off\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_14,GPIO_PIN_RESET);
                sprintf(tx_buffer, "LED RED OFF");
								tx_busy = 1;
                HAL_UART_Transmit_DMA(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer));
            }

            else if (strcmp(command_buffer, "green on\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_12,GPIO_PIN_SET);
                sprintf(tx_buffer, "LED GREEN ON");
								tx_busy = 1;
                HAL_UART_Transmit_DMA(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer));
            }

            else if (strcmp(command_buffer, "green off\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_12,GPIO_PIN_RESET);
                sprintf(tx_buffer, "LED GREEN OFF");
								tx_busy = 1;
                HAL_UART_Transmit_DMA(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer));
            }

            else if (strcmp(command_buffer, "all on\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_14, GPIO_PIN_SET);
                HAL_GPIO_WritePin(GPIOD,GPIO_PIN_12,GPIO_PIN_SET );
                sprintf(tx_buffer,"LED GREEN ON\nLED RED ON");
								tx_busy = 1;
                HAL_UART_Transmit_DMA(&huart6, (const uint8_t *)tx_buffer,strlen(tx_buffer));
						}

            else if (strcmp(command_buffer, "all off\r") == 0)
            {
                HAL_GPIO_WritePin(GPIOD, GPIO_PIN_14,GPIO_PIN_RESET);
                HAL_GPIO_WritePin(GPIOD, GPIO_PIN_12, GPIO_PIN_RESET);
                sprintf(tx_buffer,"LED GREEN OFF\nLED RED OFF");
								tx_busy = 1;
                HAL_UART_Transmit_DMA(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer));
            }

            else
            {
                sprintf(tx_buffer,"ERROR INVALID COMMAND");
								tx_busy = 1;
                HAL_UART_Transmit_DMA(&huart6,(const uint8_t *)tx_buffer,strlen(tx_buffer));
            }

            rx_flag = 0;

					}
}
