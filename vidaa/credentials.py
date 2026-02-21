"""Dynamic credential generation for Vidaa TV MQTT connection.

Reverse engineered from libmqttcrypt.so in the Vidaa mobile app.

The CORRECT algorithm (discovered via logcat capture):
- pattern: Constant "38D65DC30F45109A369A86FCE866A85B" from getInfo()/getSalt()
- race: pattern$uuid -> MD5 -> first 6 chars uppercase
- client_id: uuid$brand$race_md5_operation_001
- username: brand$XOR(timestamp) or brand$timestamp (legacy)
- value: brand + remainder + VALUE_SUFFIX (depends on protocol)
- password: MD5(timestamp$value_md5[:6])

Where:
- timestamp is Unix timestamp in SECONDS
- remainder = sum_of_digits(timestamp) % 10
- XOR constant = 0x5698_1477_2b03_a968

Authentication methods by transport protocol:
- LEGACY (< 3000): no XOR username, VALUE_SUFFIX_LEGACY
- MIDDLE (3000-3285): XOR username, VALUE_SUFFIX_LEGACY
- MODERN (>= 3290): XOR username, VALUE_SUFFIX_MODERN
"""

import hashlib
import time
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from .config import (
    PATTERN,
    VALUE_SUFFIX_MODERN,
    VALUE_SUFFIX_LEGACY,
    TIME_XOR_CONSTANT,
    DEFAULT_MQTT_USERNAME,
    DEFAULT_MQTT_PASSWORD,
)

if TYPE_CHECKING:
    from .protocol import AuthMethod


@dataclass
class MQTTCredentials:
    """MQTT connection credentials."""
    client_id: str
    username: str
    password: str


# Backwards compatibility alias
VALUE_SUFFIX = VALUE_SUFFIX_MODERN


def _md5(s: str) -> str:
    """Calculate MD5 hash of string and return UPPERCASE hex digest."""
    return hashlib.md5(s.encode('utf-8')).hexdigest().upper()


def _sum_digits(n: int) -> int:
    """Sum all digits of a number."""
    return sum(int(d) for d in str(abs(n)))


def generate_credentials(
    mac_address: str,
    brand: str = "his",
    operation: str = "vidaacommon",
    timestamp: Optional[int] = None,
    auth_method: Optional["AuthMethod"] = None,
) -> MQTTCredentials:
    """Generate MQTT credentials for Vidaa TV connection.

    Args:
        mac_address: Device MAC address or UUID (format: "AA:BB:CC:DD:EE:FF")
        brand: Brand identifier (default: "his" for Hisense)
        operation: Operation mode ("vidaacommon" or "vidaavoice")
        timestamp: Unix timestamp in SECONDS (default: current time)
        auth_method: Authentication method (LEGACY, MIDDLE, or MODERN).
                     Default: MODERN for backwards compatibility.

    Returns:
        MQTTCredentials with client_id, username, and password
    """
    # Import here to avoid circular dependency
    from .protocol import AuthMethod

    if auth_method is None:
        auth_method = AuthMethod.MODERN

    if timestamp is None:
        timestamp = int(time.time())

    # UUID should keep original case - the race hash is case-sensitive!
    uuid = mac_address
    if ":" not in uuid and "-" not in uuid and len(uuid) == 12:
        # Convert flat MAC to colon format
        uuid = ":".join(uuid[i:i+2] for i in range(0, 12, 2))

    # Step 1: Calculate race = pattern$uuid, then MD5
    race = f"{PATTERN}${uuid}"
    race_md5 = _md5(race)[:6]  # First 6 chars, uppercase

    # Step 2: Build client_id: uuid$brand$race_md5_operation_001
    client_id = f"{uuid}${brand}${race_md5}_{operation}_001"

    # Step 3: Build username
    # LEGACY: brand$timestamp (no XOR)
    # MIDDLE/MODERN: brand$XOR(timestamp)
    if auth_method == AuthMethod.LEGACY:
        username = f"{brand}${timestamp}"
    else:
        xor_time = timestamp ^ TIME_XOR_CONSTANT
        username = f"{brand}${xor_time}"

    # Step 4: Build value for password hash
    # MODERN: uses VALUE_SUFFIX_MODERN
    # LEGACY/MIDDLE: uses VALUE_SUFFIX_LEGACY
    if auth_method == AuthMethod.MODERN:
        value_suffix = VALUE_SUFFIX_MODERN
    else:
        value_suffix = VALUE_SUFFIX_LEGACY

    remainder = _sum_digits(timestamp) % 10
    value = f"{brand}{remainder}{value_suffix}"
    value_md5 = _md5(value)[:6]  # First 6 chars

    # Step 5: Password = MD5(timestamp$value_md5)
    password = _md5(f"{timestamp}${value_md5}")

    return MQTTCredentials(
        client_id=client_id,
        username=username,
        password=password
    )


def generate_credentials_static(mac_address: str) -> MQTTCredentials:
    """Generate static credentials for older Hisense TVs.

    Some older TV models accept static credentials without the dynamic algorithm.
    Try this as a fallback if dynamic credentials don't work.
    """
    uuid = mac_address.replace(":", "").replace("-", "").upper()

    return MQTTCredentials(
        client_id=f"{uuid}$vidaa_common",
        username=DEFAULT_MQTT_USERNAME,
        password=DEFAULT_MQTT_PASSWORD
    )
