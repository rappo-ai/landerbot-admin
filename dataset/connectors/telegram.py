import base64
from copy import deepcopy
from csv import excel
from dotenv import load_dotenv
import json
import logging
from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from telebot import TeleBot
from telebot.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from typing import Dict, Text, Any, List, Optional, Callable, Awaitable

from rasa.core.channels.channel import InputChannel, UserMessage, OutputChannel
from rasa.shared.constants import INTENT_MESSAGE_PREFIX
from rasa.shared.core.constants import USER_INTENT_RESTART

logger = logging.getLogger(__name__)

load_dotenv()

from actions.utils.admin_config import get_admin_group_id
from actions.utils.livechat import get_livechat, update_livechat
from actions.utils.message_metadata import update_message_metadata


def get_query_param(params, key):
    return next(iter(params[key]), "")


def get_bot_link(bot_username):
    return "https://t.me/" + bot_username


class TelegramOutput(TeleBot, OutputChannel):
    """Output channel for Telegram."""

    # skipcq: PYL-W0236
    @classmethod
    def name(cls) -> Text:
        return "telegram"

    def __init__(self, access_token: Optional[Text]) -> None:
        super().__init__(access_token)

    async def send_text_message(
        self,
        recipient_id: Text,
        text: Text,
        reply_markup=ReplyKeyboardRemove(),
        **kwargs: Any,
    ) -> None:
        for message_part in text.strip().split("\n\n"):
            self.send_message(recipient_id, message_part, reply_markup=reply_markup)

    async def send_image_url(
        self,
        recipient_id: Text,
        image: Text,
        reply_markup=ReplyKeyboardRemove(),
        **kwargs: Any,
    ) -> None:
        self.send_photo(recipient_id, image, reply_markup=reply_markup)

    async def send_text_with_buttons(
        self,
        recipient_id: Text,
        text: Text,
        buttons: List[Dict[Text, Any]],
        button_type: Optional[Text] = "inline",
        **kwargs: Any,
    ) -> None:
        """Sends a message with keyboard.

        For more information: https://core.telegram.org/bots#keyboards

        :button_type inline: horizontal inline keyboard

        :button_type vertical: vertical inline keyboard

        :button_type reply: reply keyboard
        """
        if button_type == "inline":
            reply_markup = InlineKeyboardMarkup()
            button_list = [
                InlineKeyboardButton(s["title"], callback_data=s["payload"])
                for s in buttons
            ]
            reply_markup.row(*button_list)

        elif button_type == "vertical":
            reply_markup = InlineKeyboardMarkup()
            [
                reply_markup.row(
                    InlineKeyboardButton(s["title"], callback_data=s["payload"])
                )
                for s in buttons
            ]

        elif button_type == "reply":
            reply_markup = ReplyKeyboardMarkup(
                resize_keyboard=False, one_time_keyboard=True
            )
            # drop button_type from button_list
            button_list = [b for b in buttons if b.get("title")]
            for idx, button in enumerate(buttons):
                if isinstance(button, list):
                    reply_markup.add(KeyboardButton(s["title"]) for s in button)
                else:
                    reply_markup.add(KeyboardButton(button["title"]))
        else:
            logger.error(
                "Trying to send text with buttons for unknown "
                "button type {}".format(button_type)
            )
            return

        self.send_message(recipient_id, text, reply_markup=reply_markup)

    async def send_custom_json(
        self, recipient_id: Text, json_message_arg: Dict[Text, Any], **kwargs: Any
    ) -> None:
        try:
            json_message = deepcopy(json_message_arg)

            message_metadata = json_message.pop("message_metadata", {})
            reply_markup_json: Dict = json_message.pop("reply_markup", None)
            reply_markup = (
                ReplyKeyboardRemove()
                if json_message.pop("remove_reply_markup", True)
                else None
            )
            if reply_markup_json:
                keyboard_type = reply_markup_json.get("type", "reply")
                if keyboard_type == "reply":
                    reply_markup = ReplyKeyboardMarkup(
                        resize_keyboard=reply_markup_json.get("resize_keyboard", False),
                        one_time_keyboard=reply_markup_json.get(
                            "one_time_keyboard", True
                        ),
                        row_width=reply_markup_json.get("row_width", 4),
                    )
                    [
                        reply_markup.add(*row)
                        for row in reply_markup_json.get("keyboard", [])
                    ]
                elif keyboard_type == "inline":
                    reply_markup = InlineKeyboardMarkup(
                        row_width=reply_markup_json.get("row_width", 4)
                    )
                    [
                        reply_markup.add(
                            *[
                                InlineKeyboardButton(
                                    col.get("title"),
                                    callback_data=col.get("payload"),
                                    url=col.get("url"),
                                )
                                for col in row
                            ]
                        )
                        for row in reply_markup_json.get("keyboard", [])
                    ]

            send_functions = {
                ("from_chat_id", "message_id"): "copy_message",
                (
                    "text",
                    "chat_id",
                    "message_id",
                ): "edit_message_text",
                ("text",): "send_message",
                ("photo",): "send_photo",
                ("audio",): "send_audio",
                ("document",): "send_document",
                ("sticker",): "send_sticker",
                ("video",): "send_video",
                ("video_note",): "send_video_note",
                ("animation",): "send_animation",
                ("voice",): "send_voice",
                ("media",): "send_media_group",
                ("latitude", "longitude", "title", "address"): "send_venue",
                ("latitude", "longitude"): "send_location",
                ("phone_number", "first_name"): "send_contact",
                ("game_short_name",): "send_game",
                ("action",): "send_chat_action",
                (
                    "title",
                    "decription",
                    "payload",
                    "provider_token",
                    "start_parameter",
                    "currency",
                    "prices",
                ): "send_invoice",
            }

            for params in send_functions.keys():
                if all(json_message.get(p) is not None for p in params):
                    document = json_message.pop("document", None)
                    if document:
                        document_file_type = json_message.pop(
                            "document_file_type", None
                        )
                        document_file_name = json_message.pop(
                            "document_file_name", "document"
                        )
                        if document_file_type == "application/zip":
                            document_bytes = base64.standard_b64decode(document)
                        else:
                            document_bytes = document.encode("utf-8")
                        json_message["document"] = (
                            document_file_name,
                            document_bytes,
                            document_file_type,
                        )
                    args = [json_message.pop(p) for p in params]
                    if (
                        send_functions[params]
                        not in [
                            "send_media_group",
                            "send_game",
                            "send_chat_action",
                            "send_invoice",
                        ]
                        and reply_markup
                    ):
                        json_message["reply_markup"] = reply_markup
                    api_call = getattr(self, send_functions[params])
                    if send_functions[params] == "edit_message_text":
                        response = api_call(*args, **json_message)
                    else:
                        recipient_id = json_message.pop("chat_id", recipient_id)
                        response = api_call(recipient_id, *args, **json_message)
                    if message_metadata:
                        update_message_metadata(response.message_id, message_metadata)

        except Exception as e:
            logger.error(e)


class TelegramInput(InputChannel):
    """Telegram input channel"""

    @classmethod
    def name(cls) -> Text:
        return "telegram"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        if not credentials:
            cls.raise_missing_credentials_exception()

        return cls(
            credentials.get("access_token"),
            credentials.get("verify"),
            credentials.get("webhook_url"),
            credentials.get("drop_pending_updates", "true").lower()
            in ["true", "1", "t"],
        )

    def __init__(
        self,
        access_token: Optional[Text],
        verify: Optional[Text],
        webhook_url: Optional[Text],
        drop_pending_updates: Optional[bool] = True,
        debug_mode: bool = True,
    ) -> None:
        self.access_token = access_token
        self.verify = verify
        self.webhook_url = webhook_url
        self.drop_pending_updates = drop_pending_updates
        self.debug_mode = debug_mode

    @staticmethod
    def _get_message_type(message: Message) -> Text:
        try:
            if not message:
                return None
            MESSAGE_TYPES = [
                "text",
                "animation",
                "audio",
                "document",
                "photo",
                "sticker",
                "video",
                "video_note",
                "voice",
                "contact",
                "dice",
                "game",
                "poll",
                "venue",
                "location",
            ]
            for type in MESSAGE_TYPES:
                if getattr(message, type):
                    return type
        except:
            pass
        return None

    @staticmethod
    def _get_chat_type(message: Message) -> Text:
        return message and message.chat and message.chat.type

    @staticmethod
    def _is_edited_message(message: Update) -> bool:
        return message and (message.edited_message is not None)

    @staticmethod
    def _is_button(message: Update) -> bool:
        return message and (message.callback_query is not None)

    def blueprint(
        self, on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> Blueprint:
        telegram_webhook = Blueprint("telegram_webhook", __name__)
        out_channel = self.get_output_channel()

        @telegram_webhook.route("/", methods=["GET"])
        async def health(_: Request) -> HTTPResponse:
            return response.json({"status": "ok"})

        @telegram_webhook.route("/webhook", methods=["GET", "POST"])
        async def message(request: Request) -> Any:
            if request.method == "POST":
                try:
                    disable_nlu_bypass = True
                    request_dict = request.json
                    logger.info("INCOMING UPDATE: " + json.dumps(request_dict))
                    update = Update.de_json(request_dict)
                    if not out_channel.get_me().username == self.verify:
                        logger.debug("Invalid access token, check it matches Telegram")
                        return response.json({"status": "error"})

                    if self._is_button(update):
                        out_channel.answer_callback_query(update.callback_query.id)
                        msg = update.callback_query.message
                        text = update.callback_query.data
                        disable_nlu_bypass = False
                    elif self._is_edited_message(update):
                        # skip edited messages for now
                        # msg = update.edited_message
                        # text = update.edited_message.text
                        return response.json({"status": "ok"})
                    else:
                        msg = update.message
                        message_type = self._get_message_type(msg)
                        chat_type = self._get_chat_type(msg)
                        # skip channels
                        if chat_type not in ["private", "group", "supergroup"]:
                            return response.json({"status": "ok"})
                        # ignore non-command and non-reply messages in a group
                        if chat_type in ["group", "supergroup"] and not (
                            getattr(msg, "text", "").startswith("/")
                            or getattr(msg, "reply_to_message", "")
                        ):
                            return response.json({"status": "ok"})
                        if message_type == "text":
                            text = msg.text
                            if text and text.startswith("/"):
                                text = text.replace(f"@{self.verify}", "")
                        elif message_type:
                            text = json.dumps(request_dict)
                        else:
                            return response.json({"status": "ok"})
                        if getattr(msg, "reply_to_message"):
                            text = "/livechat_reply"
                    sender_id = msg.chat.id
                    metadata = self.get_metadata(request) or {}
                    if text == (INTENT_MESSAGE_PREFIX + USER_INTENT_RESTART):
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                        await on_new_message(
                            UserMessage(
                                "/start",
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                            )
                        )
                    else:
                        await on_new_message(
                            UserMessage(
                                text,
                                out_channel,
                                sender_id,
                                input_channel=self.name(),
                                metadata=metadata,
                                disable_nlu_bypass=disable_nlu_bypass,
                            )
                        )
                except Exception as e:
                    logger.error(f"Exception when trying to handle message.{e}")
                    logger.debug(e, exc_info=True)

                return response.json({"status": "ok"})

        @telegram_webhook.route("/livechat/message", methods=["POST"])
        async def livechat_message(request: Request) -> Any:
            if request.method == "POST":
                try:
                    request_dict = request.json
                    sender_id = get_admin_group_id()
                    disable_nlu_bypass = True
                    await on_new_message(
                        UserMessage(
                            "/livechat_message",
                            out_channel,
                            sender_id,
                            input_channel=self.name(),
                            metadata=request_dict,
                            disable_nlu_bypass=disable_nlu_bypass,
                        )
                    )
                except Exception as e:
                    logger.error(f"Exception in chat_webhook.{e}")
                    logger.debug(e, exc_info=True)

                return response.json({"status": "ok"})

        @telegram_webhook.route("/livechat/enabled", methods=["GET", "POST"])
        async def livechat_enabled(request: Request) -> Any:
            if request.method == "GET":
                livechat = {}
                try:
                    user_id = get_query_param(request.args, "user_id")
                    livechat = get_livechat(user_id=user_id) or {}
                except Exception as e:
                    logger.error(e)

                return response.json({"enabled": livechat.get("enabled", False)})
            elif request.method == "POST":
                enabled = False
                try:
                    user_id = request.json.get("user_id")
                    enabled = request.json.get("enabled")
                    update_livechat(
                        user_id=user_id,
                        enabled=enabled,
                    )
                except Exception as e:
                    logger.error(e)

                return response.json({"status": "ok"})

        @telegram_webhook.route("/livechat/event", methods=["POST"])
        async def livechat_event(request: Request) -> Any:
            if request.method == "POST":
                try:
                    user_id = request.json.get("user_id")
                    event = request.json.get("event")
                    update_livechat(
                        user_id=user_id,
                        event=event,
                    )
                except Exception as e:
                    logger.error(e)

                return response.json({"status": "ok"})

        @telegram_webhook.route("/livechat/online", methods=["POST"])
        async def livechat_online(request: Request) -> Any:
            if request.method == "POST":
                online = False
                try:
                    user_id = request.json.get("user_id")
                    online = request.json.get("online")
                    update_livechat(
                        user_id=user_id,
                        online=online,
                    )
                except Exception as e:
                    logger.error(e)

                return response.json({"status": "ok"})

        @telegram_webhook.route("/livechat/visible", methods=["POST"])
        async def livechat_visible(request: Request) -> Any:
            if request.method == "POST":
                visible = False
                try:
                    user_id = request.json.get("user_id")
                    visible = request.json.get("visible")
                    update_livechat(
                        user_id=user_id,
                        visible=visible,
                    )
                except Exception as e:
                    logger.error(e)

                return response.json({"status": "ok"})

        return telegram_webhook

    def get_output_channel(self) -> TelegramOutput:
        """Loads the telegram channel."""
        channel = TelegramOutput(self.access_token)
        channel.set_webhook(
            url=self.webhook_url, drop_pending_updates=self.drop_pending_updates
        )
        commands = [
            BotCommand("chats", "List chats"),
        ]
        channel.set_my_commands(commands)

        return channel

    def get_metadata(self, request: Request) -> Dict[Text, Any]:
        return request.json
