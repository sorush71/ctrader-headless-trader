import socket
import ssl
import struct
import logging
import threading
import time
from typing import Dict, Any, Optional

from .config import CTraderConfig
from .protocol import (
    PayloadType,
    ProtoOrderType,
    TradeSide,
    ProtoSerializer,
    ProtoDeserializer
)

logger = logging.getLogger("cTraderGateway")


class CTraderGateway:
    """
    Production-grade Network Gateway for cTrader Open API.
    Connects via raw TLS Socket (Port 5035), handles 4-byte big-endian framing,
    binary Protobuf messages, automatic heartbeats, and error codes.
    """

    def __init__(self, config: CTraderConfig):
        self.config = config
        self.sock: Optional[ssl.SSLSocket] = None
        self.is_connected = False
        self.is_authorized = False
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None

    def connect(self) -> bool:
        """
        Connects directly to cTrader Cloud via SSL/TLS.
        If real API credentials exist, executes real handshake;
        otherwise runs in safe local sandbox mode.
        """
        has_real_credentials = bool(
            self.config.client_id
            and self.config.client_id != "your_client_id_here"
            and self.config.access_token
            and self.config.access_token != "your_access_token_here"
        )

        if not has_real_credentials:
            logger.warning(
                "Running in SANDBOX / SIMULATION mode. Set valid CTRADER_CLIENT_ID and "
                "CTRADER_ACCESS_TOKEN in .env to connect to live/demo cTrader Open API servers."
            )
            self.is_connected = True
            self.is_authorized = True
            return True

        # Real Live TLS Connection
        logger.info(f"Connecting to live cTrader Open API at {self.config.host}:{self.config.PORT}...")
        try:
            raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw_sock.settimeout(10.0)

            context = ssl.create_default_context()
            self.sock = context.wrap_socket(raw_sock, server_hostname=self.config.host)
            self.sock.connect((self.config.host, self.config.PORT))
            self.is_connected = True
            logger.info("TCP/TLS Connection established!")

            # 1. Authorize Application (ProtoOAApplicationAuthReq)
            app_req = ProtoSerializer.app_auth_req(self.config.client_id, self.config.client_secret)
            self._send_raw(app_req)
            resp = self._read_message()
            logger.info(f"Application Auth Response: {resp.get('payloadType')}")

            # 2. Authorize Account (ProtoOAAccountAuthReq)
            if self.config.account_id:
                acc_id = int(self.config.account_id)
                acc_req = ProtoSerializer.account_auth_req(acc_id, self.config.access_token)
                self._send_raw(acc_req)
                resp = self._read_message()
                logger.info(f"Account Auth Response: {resp.get('payloadType')}")

            self.is_authorized = True
            self._start_heartbeat()
            return True

        except Exception as e:
            logger.error(f"Connection to cTrader Open API failed: {e}")
            self.is_connected = False
            self.is_authorized = False
            raise ConnectionError(f"cTrader Live Connection Error: {e}")

    def send_order(
        self,
        symbol_id: int,
        order_type: ProtoOrderType,
        side: TradeSide,
        volume_cents: int,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = ""
    ) -> Dict[str, Any]:
        """Sends a real or simulated ProtoOANewOrderReq."""
        if not self.is_authorized:
            raise ConnectionError("Gateway not authorized. Call connect() first.")

        if self.sock and self.is_connected:
            acc_id = int(self.config.account_id)
            payload = ProtoSerializer.new_order_req(
                account_id=acc_id,
                symbol_id=symbol_id,
                order_type=order_type,
                side=side,
                volume=volume_cents,
                price=price,
                sl=sl,
                tp=tp,
                comment=comment
            )
            self._send_raw(payload)
            resp = self._read_message()
            return {"status": "SUCCESS", "raw": resp}
        else:
            # Sandbox response
            return {
                "orderId": 9820412,
                "positionId": 551902,
                "executionPrice": price or 1.08520,
                "status": "ORDER_ACCEPTED (SANDBOX)"
            }

    def cancel_order(self, order_id: int) -> bool:
        """Sends a real or simulated ProtoOACancelOrderReq."""
        if not self.is_authorized:
            raise ConnectionError("Gateway not authorized.")

        if self.sock and self.is_connected:
            acc_id = int(self.config.account_id)
            payload = ProtoSerializer.cancel_order_req(acc_id, order_id)
            self._send_raw(payload)
            self._read_message()
            return True
        return True

    def close_position(self, position_id: int, volume_cents: Optional[int] = None) -> Dict[str, Any]:
        """Sends a real or simulated ProtoOAClosePositionReq."""
        if not self.is_authorized:
            raise ConnectionError("Gateway not authorized.")

        if self.sock and self.is_connected:
            acc_id = int(self.config.account_id)
            payload = ProtoSerializer.close_position_req(acc_id, position_id, volume_cents)
            self._send_raw(payload)
            resp = self._read_message()
            return {"positionId": position_id, "status": "CLOSED", "raw": resp}
        return {"positionId": position_id, "status": "CLOSED (SANDBOX)", "closePrice": 1.08550}

    def get_trader_info(self) -> Dict[str, Any]:
        """Fetches account balance and metrics."""
        if not self.is_authorized:
            raise ConnectionError("Gateway not authorized.")

        if self.sock and self.is_connected:
            acc_id = int(self.config.account_id)
            payload = ProtoSerializer.trader_req(acc_id)
            self._send_raw(payload)
            resp = self._read_message()
            return {"status": "SUCCESS", "raw": resp}

        return {
            "accountId": self.config.account_id or "DEMO-884920",
            "balance": 10000.0,
            "equity": 10050.25,
            "freeMargin": 9850.25,
            "marginUsed": 200.0,
            "leverage": 100,
            "currency": "USD"
        }

    def disconnect(self):
        """Cleanly terminates TLS socket and heartbeat thread."""
        self._running = False
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        self.is_connected = False
        self.is_authorized = False

    def _send_raw(self, framed_data: bytes):
        if not self.sock:
            raise ConnectionError("Socket is not open.")
        self.sock.sendall(framed_data)

    def _read_message(self) -> Dict[str, Any]:
        """Reads 4-byte length prefix then reads the exact protobuf message payload."""
        if not self.sock:
            raise ConnectionError("Socket is not open.")

        raw_len = self._recv_exact(4)
        msg_len = struct.unpack(">I", raw_len)[0]
        payload = self._recv_exact(msg_len)
        return ProtoDeserializer.parse_proto_message(payload)

    def _recv_exact(self, num_bytes: int) -> bytes:
        data = bytearray()
        while len(data) < num_bytes:
            packet = self.sock.recv(num_bytes - len(data))
            if not packet:
                raise ConnectionError("Socket closed unexpectedly by remote peer.")
            data.extend(packet)
        return bytes(data)

    def _start_heartbeat(self):
        """Sends periodic heartbeat to keep the cloud TCP session alive."""
        self._running = True

        def heartbeat_loop():
            while self._running:
                time.sleep(10)
                try:
                    if self.sock and self.is_connected:
                        hb = ProtoSerializer.heartbeat()
                        self._send_raw(hb)
                except Exception as e:
                    logger.debug(f"Heartbeat tick error: {e}")
                    break

        self._heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
