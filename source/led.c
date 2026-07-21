/******************************************************************************
* File Name: led.c
*
* Description: This file contains source code that controls LED.
*
* Related Document: README.md
*
*******************************************************************************
 * (c) 2019-2025, Infineon Technologies AG, or an affiliate of Infineon
 * Technologies AG. All rights reserved.
 * This software, associated documentation and materials ("Software") is
 * owned by Infineon Technologies AG or one of its affiliates ("Infineon")
 * and is protected by and subject to worldwide patent protection, worldwide
 * copyright laws, and international treaty provisions. Therefore, you may use
 * this Software only as provided in the license agreement accompanying the
 * software package from which you obtained this Software. If no license
 * agreement applies, then any use, reproduction, modification, translation, or
 * compilation of this Software is prohibited without the express written
 * permission of Infineon.
 *
 * Disclaimer: UNLESS OTHERWISE EXPRESSLY AGREED WITH INFINEON, THIS SOFTWARE
 * IS PROVIDED AS-IS, WITH NO WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING, BUT NOT LIMITED TO, ALL WARRANTIES OF NON-INFRINGEMENT OF
 * THIRD-PARTY RIGHTS AND IMPLIED WARRANTIES SUCH AS WARRANTIES OF FITNESS FOR A
 * SPECIFIC USE/PURPOSE OR MERCHANTABILITY.
 * Infineon reserves the right to make changes to the Software without notice.
 * You are responsible for properly designing, programming, and testing the
 * functionality and safety of your intended application of the Software, as
 * well as complying with any legal requirements related to its use. Infineon
 * does not guarantee that the Software will be free from intrusion, data theft
 * or loss, or other breaches ("Security Breaches"), and Infineon shall have
 * no liability arising out of any Security Breaches. Unless otherwise
 * explicitly approved by Infineon, the Software may not be used in any
 * application where a failure of the Product or any consequences of the use
 * thereof can reasonably be expected to result in personal injury.
*******************************************************************************/

/*******************************************************************************
* Header files includes
*******************************************************************************/
#include "cybsp.h"
#include "cyhal.h"
#include "led.h"


/*******************************************************************************
* Global constants
*******************************************************************************/
#define PWM_LED_FREQ_HZ    (1000000lu)  /* in Hz */
#define GET_DUTY_CYCLE(x)    (100 - x)


/*******************************************************************************
* Global constants
*******************************************************************************/
led_state_t led_state_cur = LED_OFF;
cyhal_pwm_t pwm_led;


/*******************************************************************************
* Function Name: update_led_state
********************************************************************************
* Summary:
*  This function updates the LED state, based on the touch input.
*
* Parameter:
*  ledData: the pointer to the LED data structure
*
*******************************************************************************/
void update_led_state(led_data_t *ledData)
{
    if ((led_state_cur == LED_OFF) && (ledData->state == LED_ON))
    {
        cyhal_pwm_start(&pwm_led);
        led_state_cur = LED_ON;
        ledData->brightness = LED_MAX_BRIGHTNESS;
    }
    else if ((led_state_cur == LED_ON) && (ledData->state == LED_OFF))
    {
        cyhal_pwm_stop(&pwm_led);
        led_state_cur = LED_OFF;
        ledData->brightness = 0;
    }
    else
    {
    }

    if ((LED_ON == led_state_cur) || ((LED_OFF == led_state_cur) && (ledData->brightness > 0)))
    {
        cyhal_pwm_start(&pwm_led);
        uint32_t brightness = (ledData->brightness < LED_MIN_BRIGHTNESS) ? LED_MIN_BRIGHTNESS : ledData->brightness;

        /* Drive the LED with brightness */
        cyhal_pwm_set_duty_cycle(&pwm_led, GET_DUTY_CYCLE(brightness),
                                 PWM_LED_FREQ_HZ);
        led_state_cur = LED_ON;
    }
}


/*******************************************************************************
* Function Name: initialize_led
********************************************************************************
* Summary:
*  Initializes a PWM resource for driving an LED.
*
*******************************************************************************/
cy_rslt_t initialize_led(void)
{
    cy_rslt_t rslt;

    rslt = cyhal_pwm_init(&pwm_led, CYBSP_USER_LED, NULL);

    if (CY_RSLT_SUCCESS == rslt)
    {
        rslt = cyhal_pwm_set_duty_cycle(&pwm_led,
                                        GET_DUTY_CYCLE(LED_MAX_BRIGHTNESS),
                                        PWM_LED_FREQ_HZ);
        if (CY_RSLT_SUCCESS == rslt)
        {
            rslt = cyhal_pwm_start(&pwm_led);
        }
        
    }

    if (CY_RSLT_SUCCESS == rslt)
    {
        led_state_cur = LED_ON;
    }

    return rslt;
}


/* [] END OF FILE */
