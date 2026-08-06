import logging
from typing import Tuple, Union

import requests
from kavenegar import KavenegarAPI, APIException, HTTPException

logger = logging.getLogger(__name__)

SMS_SUCCESS_RESPONSE = 200

class KavenegarClient:
    def __init__(self, api_key: str = None):
        self.api_key = '646871784E586D7A596F4B672B594B465A58667861417A4536433455437A4E487051796D376F78423241733D'
        # self.api = KavenegarAPI(self.api_key)
        self.url = f'https://api.kavenegar.com/v1/{self.api_key}/verify/lookup.json'

    def send_sms(self, to: str, message: str) -> Tuple[bool, Union[int, str], str]:
        """
        Send SMS via Kavenegar.

        Args:
            to: Recipient phone number
            message: SMS text content

        Returns:
            Tuple of (success: bool, status: int|str, message: str)
        """
        try:
            print(self.url)
            response = requests.get(
                url=self.url,
                params={
                    'receptor': to,
                    'token': message,
                    'template': 'movra'
                },
                headers={
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
            )
            response.raise_for_status()
            res = response.json()
            result = res.get('return')

            is_success = result.get('status') == SMS_SUCCESS_RESPONSE
            if is_success:
                logger.info("SMS sent to %s (status: %s)", to, result.get('status'))
            else:
                logger.error("SMS failed for %s: %s", to, result.get('status'))

            return is_success, result.get('status'), result.get('message', '')
        except (APIException, HTTPException) as e:
            logger.exception("Kavenegar API exception: %s", e)
            return False, str(e), ''
        except requests.RequestException as e:
            logger.exception("Kavenegar request failed: %s", e)
            return False, str(e), ''
