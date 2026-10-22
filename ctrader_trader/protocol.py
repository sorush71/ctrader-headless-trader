"""
cTrader Open API Protocol Framing and Protobuf Wire Format Handler.
Implements the binary length-prefixed TLS framing protocol used by Spotware cTrader Open API.
"""

import struct
from enum import IntEnum
from typing import Dict, Any, Tuple, Optional


class PayloadType(IntEnum):
    HEARTBEAT_EVENT = 51
    PROTO_OA_APPLICATION_AUTH_REQ = 2100
    PROTO_OA_APPLICATION_AUTH_RES = 2101
    PROTO_OA_ACCOUNT_AUTH_REQ = 2102
    PROTO_OA_ACCOUNT_AUTH_RES = 2103
    PROTO_OA_SYMBOLS_LIST_REQ = 2114
    PROTO_OA_SYMBOLS_LIST_RES = 2115
    PROTO_OA_TRADER_REQ = 2121
    PROTO_OA_TRADER_RES = 2122
    PROTO_OA_NEW_ORDER_REQ = 2104
    PROTO_OA_EXECUTION_EVENT = 2126
    PROTO_OA_CANCEL_ORDER_REQ = 2106
    PROTO_OA_CLOSE_POSITION_REQ = 2108
    PROTO_OA_ERROR_RES = 2142


class TradeSide(IntEnum):
    BUY = 1
    SELL = 2


class ProtoOrderType(IntEnum):
    MARKET = 1
    LIMIT = 2
    STOP = 3
    MARKET_RANGE = 4


def encode_varint(value: int) -> bytes:
    """Encodes an integer into standard Protocol Buffers varint bytes."""
    if value < 0:
        value += (1 << 64)
    res = bytearray()
    while value > 0x7F:
        res.append((value & 0x7F) | 0x80)
        value >>= 7
    res.append(value & 0x7F)
    return bytes(res)


def decode_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """Decodes a varint from bytes returning (value, new_offset)."""
    res = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ValueError("Buffer underflow reading varint")
        b = data[offset]
        offset += 1
        res |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return res, offset


def make_field(field_num: int, wire_type: int, data: bytes) -> bytes:
    tag = (field_num << 3) | wire_type
    return encode_varint(tag) + data


def encode_string_field(field_num: int, text: str) -> bytes:
    encoded = text.encode("utf-8")
    return make_field(field_num, 2, encode_varint(len(encoded)) + encoded)


def encode_int_field(field_num: int, val: int) -> bytes:
    return make_field(field_num, 0, encode_varint(val))


def encode_double_field(field_num: int, val: float) -> bytes:
    return make_field(field_num, 1, struct.pack("<d", val))


class ProtoSerializer:
    """Serializes high-level cTrader requests into binary Protobuf payloads."""

    @staticmethod
    def app_auth_req(client_id: str, client_secret: str) -> bytes:
        payload = encode_string_field(1, client_id) + encode_string_field(2, client_secret)
        return ProtoSerializer.wrap_message(PayloadType.PROTO_OA_APPLICATION_AUTH_REQ, payload)

    @staticmethod
    def account_auth_req(account_id: int, access_token: str) -> bytes:
        payload = encode_int_field(1, account_id) + encode_string_field(2, access_token)
        return ProtoSerializer.wrap_message(PayloadType.PROTO_OA_ACCOUNT_AUTH_REQ, payload)

    @staticmethod
    def trader_req(account_id: int) -> bytes:
        payload = encode_int_field(1, account_id)
        return ProtoSerializer.wrap_message(PayloadType.PROTO_OA_TRADER_REQ, payload)

    @staticmethod
    def new_order_req(
        account_id: int,
        symbol_id: int,
        order_type: ProtoOrderType,
        side: TradeSide,
        volume: int,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = ""
    ) -> bytes:
        p = bytearray()
        p.extend(encode_int_field(1, account_id))
        p.extend(encode_int_field(2, symbol_id))
        p.extend(encode_int_field(3, int(order_type)))
        p.extend(encode_int_field(4, int(side)))
        p.extend(encode_int_field(5, volume))
        if price is not None:
            p.extend(encode_double_field(6, price))
        if sl is not None:
            p.extend(encode_double_field(11, sl))
        if tp is not None:
            p.extend(encode_double_field(12, tp))
        if comment:
            p.extend(encode_string_field(13, comment))

        return ProtoSerializer.wrap_message(PayloadType.PROTO_OA_NEW_ORDER_REQ, bytes(p))

    @staticmethod
    def cancel_order_req(account_id: int, order_id: int) -> bytes:
        payload = encode_int_field(1, account_id) + encode_int_field(2, order_id)
        return ProtoSerializer.wrap_message(PayloadType.PROTO_OA_CANCEL_ORDER_REQ, payload)

    @staticmethod
    def close_position_req(account_id: int, position_id: int, volume: Optional[int] = None) -> bytes:
        p = bytearray()
        p.extend(encode_int_field(1, account_id))
        p.extend(encode_int_field(2, position_id))
        if volume:
            p.extend(encode_int_field(3, volume))
        return ProtoSerializer.wrap_message(PayloadType.PROTO_OA_CLOSE_POSITION_REQ, bytes(p))

    @staticmethod
    def heartbeat() -> bytes:
        return ProtoSerializer.wrap_message(PayloadType.HEARTBEAT_EVENT, b"")

    @staticmethod
    def wrap_message(payload_type: PayloadType, payload: bytes, client_msg_id: str = "") -> bytes:
        """Wraps an inner payload in top-level ProtoMessage and adds 4-byte big-endian framing length."""
        proto = bytearray()
        proto.extend(encode_int_field(1, int(payload_type)))
        if payload:
            proto.extend(make_field(2, 2, encode_varint(len(payload)) + payload))
        if client_msg_id:
            proto.extend(encode_string_field(3, client_msg_id))

        raw_bytes = bytes(proto)
        # Prefix 4-byte big endian message length
        framed = struct.pack(">I", len(raw_bytes)) + raw_bytes
        return framed


class ProtoDeserializer:
    """Parses binary messages received over the TCP/TLS socket from cTrader Open API."""

    @staticmethod
    def parse_proto_message(raw_data: bytes) -> Dict[str, Any]:
        offset = 0
        msg: Dict[str, Any] = {"payloadType": None, "payload": b"", "clientMsgId": ""}
        while offset < len(raw_data):
            tag, offset = decode_varint(raw_data, offset)
            field_num = tag >> 3
            wire_type = tag & 0x07

            if wire_type == 0:  # Varint
                val, offset = decode_varint(raw_data, offset)
                if field_num == 1:
                    msg["payloadType"] = val
            elif wire_type == 2:  # Length-delimited
                length, offset = decode_varint(raw_data, offset)
                val_bytes = raw_data[offset:offset + length]
                offset += length
                if field_num == 2:
                    msg["payload"] = val_bytes
                elif field_num == 3:
                    msg["clientMsgId"] = val_bytes.decode("utf-8", errors="ignore")
            elif wire_type == 1:  # 64-bit
                offset += 8
            elif wire_type == 5:  # 32-bit
                offset += 4
            else:
                break
        return msg
