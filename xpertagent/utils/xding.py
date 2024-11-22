#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DingTalk Bot Integration Module

This module provides integration with DingTalk's messaging system through their Stream API.
It handles both group and individual conversations, supporting text message interactions
with a DingTalk bot.

Key Features:
- Automatic token management
- Message sending to both group and individual chats
- Webhook-based message handling
- Asynchronous message processing
"""

import sys
import os
import json
import requests
import dingtalk_stream

from dingtalk_stream import CallbackHandler
from concurrent.futures import ThreadPoolExecutor
from xpertagent.utils.xlogger import logger
from xpertagent.config.settings import settings
from xpertagent.services.xservice import XService

class DingTalkBotHandler(CallbackHandler):
    """
    DingTalk Bot Message Handler

    This class handles incoming messages from DingTalk and provides methods for sending
    responses back to users in both group and individual chats.

    Attributes:
        app_key (str): DingTalk application key from settings
        app_secret (str): DingTalk application secret from settings
        webhook_token (str): DingTalk webhook token for custom bot
    """

    def __init__(self):
        super().__init__()
        self.xservice = XService()
        self.app_key = settings.XDINGTALK_APP_KEY
        self.app_secret = settings.XDINGTALK_APP_SECRET
        self.webhook_token = settings.XDINGTALK_WEBHOOK_TOKEN
        
        if not self.webhook_token:
            logger.warning("XDINGTALK_WEBHOOK_TOKEN not set")
    
    async def get_access_token(self) -> str:
        """
        Retrieve access token from DingTalk API.

        Returns:
            str: The access token for DingTalk API authentication

        Raises:
            ValueError: If APP_KEY or APP_SECRET is missing
            Exception: If token retrieval fails
        """
        if not all([self.app_key, self.app_secret]):
            raise ValueError("Missing APP_KEY or APP_SECRET")
            
        url = "https://oapi.dingtalk.com/gettoken"
        params = {
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
            if result.get("errcode") == 0:
                self.access_token = result.get("access_token")
                logger.info(f"Successfully obtained access_token: `{self.access_token}`")
                return self.access_token
            else:
                raise Exception(f"Failed to get access_token: {result}")
        except Exception as e:
            logger.error(f"Failed to get access_token: {e}")
            raise
    
    async def send_message(self, conversation_id: str, content: str) -> bool:
        """
        Send a message to a DingTalk conversation.

        Args:
            conversation_id (str): The ID of the conversation
            content (str): The message content to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            if not self.webhook_token:
                logger.error("Missing XDINGTALK_WEBHOOK_TOKEN")
                return False
                
            url = f"https://oapi.dingtalk.com/robot/send"
            params = {
                "access_token": self.webhook_token
            }
            
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "at": {
                    "isAtAll": False
                }
            }
            
            logger.info(f"Message parameters: {data}")
            response = requests.post(url, params=params, json=data)
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"Message sent successfully: {content}")
                return True
            else:
                logger.error(f"Failed to send message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            return False
    
    async def send_group_message(self, conversation_id: str, content: str) -> bool:
        """
        Send a message to a DingTalk group chat.

        Args:
            conversation_id (str): The ID of the group conversation
            content (str): The message content to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            if not self.webhook_token:
                logger.error("Missing XDINGTALK_WEBHOOK_TOKEN")
                return False
                
            url = f"https://oapi.dingtalk.com/robot/send"
            params = {
                "access_token": self.webhook_token
            }
            
            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                },
                "at": {
                    "isAtAll": False
                }
            }
            
            logger.info(f"Group message parameters: {data}")
            response = requests.post(url, params=params, json=data)
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"Group message sent successfully: {content}")
                return True
            else:
                logger.error(f"Failed to send group message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending group message: {e}", exc_info=True)
            return False

    async def send_single_message(self, user_id: str, content: str, session_webhook: str = None) -> bool:
        """
        Send a message to an individual user.

        Args:
            user_id (str): The ID of the recipient user
            content (str): The message content to send
            session_webhook (str, optional): The webhook URL for the session

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            if not session_webhook:
                logger.error("Missing session webhook URL")
                return False

            data = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            logger.info(f"Individual message parameters: {data}")
            response = requests.post(session_webhook, json=data)
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"Individual message sent successfully: {content}")
                return True
            else:
                logger.error(f"Failed to send individual message: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending individual message: {e}", exc_info=True)
            return False

    async def process(self, callback: dingtalk_stream.CallbackMessage) -> tuple:
        """
        Process incoming DingTalk message callbacks.

        Args:
            callback (CallbackMessage): The callback message from DingTalk

        Returns:
            tuple: (status_code, headers) where status_code is HTTP status code
        """
        try:
            logger.info(f"Received raw message data: {callback.data}")
            
            data = callback.data
            if not data:
                logger.warning("Received empty message")
                return 200, {}
                
            conversation_id = data.get('conversationId')
            logger.info(f"Conversation ID: {conversation_id}")
            
            conversation_type = data.get('conversationType')
            sender_id = data.get('senderId')
            sender_nick = data.get('senderNick', 'Unknown User')
            logger.info(f"Conversation type: {conversation_type}, Sender ID: {sender_id}, Sender nickname: {sender_nick}")
            
            if not conversation_id:
                logger.warning("No conversation ID in message")
                return 200, {}
                
            msg_type = data.get('msgtype', '')
            if msg_type == 'text':
                text_content = data.get('text', {}).get('content', '').strip()
                logger.info(f"Received text message from {sender_nick}: {text_content}")
                
                ### ==================================================================
                ### 临时测试：用 XOCR！！！
                if text_content.startswith("http://") or text_content.startswith("https://"):
                    http_response = await self.xservice.make_http_request(
                        "/xocr/process",
                        json={
                            "img_url": text_content
                        }
                    )
                    response = http_response["result"]
                else:
                    response = f"Message received from {sender_nick}: `{text_content}`. \n\nIf you want to use the XOCR service, please send an image URL."
                ### ==================================================================
                
                if conversation_type == '1':  # Individual chat
                    session_webhook = data.get('sessionWebhook')
                    success = await self.send_single_message(sender_id, response, session_webhook)
                else:  # Group chat
                    success = await self.send_group_message(conversation_id, response)
                    
                if success:
                    logger.info("Reply sent successfully")
                else:
                    logger.error("Failed to send reply")
                    
            else:
                logger.warning(f"Unhandled message type: {msg_type}")
            
            return 200, {}
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return 500, {}

def start_bot(app_key: str, app_secret: str):
    """
    Start the DingTalk bot with the provided credentials.

    Args:
        app_key (str): DingTalk application key
        app_secret (str): DingTalk application secret
    """
    try:
        credential = dingtalk_stream.Credential(app_key, app_secret)
        client = dingtalk_stream.DingTalkStreamClient(credential, logger)
        
        handler = DingTalkBotHandler()
        client.register_callback_handler(dingtalk_stream.ChatbotMessage.TOPIC, handler)
        
        logger.info("Starting DingTalk bot...")
        client.start_forever()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)

def run():
    """
    Main entry point for running the DingTalk bot.
    Validates required settings and starts the bot in a separate thread.
    """
    if not all([settings.XDINGTALK_APP_KEY, settings.XDINGTALK_APP_SECRET]):
        logger.error("Please configure XDINGTALK_APP_KEY and XDINGTALK_APP_SECRET in .env file")
        return
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(start_bot, settings.XDINGTALK_APP_KEY, settings.XDINGTALK_APP_SECRET)

if __name__ == "__main__":
    run()