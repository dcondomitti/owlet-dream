"""API client for Owlet Dream -- Firebase Auth + Owlet REST + Ayla IoT."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import aiohttp

from .const import (
    ANDROID_CERT_SHA1,
    ANDROID_PACKAGE,
    AYLA_CONFIG,
    FIREBASE_AUTH_URL,
    FIREBASE_CONFIG,
    FIREBASE_TOKEN_URL,
    OWLET_ACCOUNTS_BASE,
    OWLET_ACCOUNTS_BASE_EU,
    OWLET_AYLA_SSO_BASE,
    OWLET_AYLA_SSO_BASE_EU,
    OWLET_DEVICES_BASE,
    OWLET_DEVICES_BASE_EU,
    REGION_EU,
    REGION_US,
)

_LOGGER = logging.getLogger(__name__)


class OwletError(Exception):
    """Base exception for Owlet API errors."""


class OwletAuthError(OwletError):
    """Authentication error."""


class OwletApiError(OwletError):
    """API call error."""


class OwletApi:
    """Client for the Owlet Dream API stack."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        email: str,
        password: str,
        region: str = REGION_US,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._region = region

        # Firebase tokens
        self._firebase_id_token: str | None = None
        self._firebase_refresh_token: str | None = None
        self._firebase_token_expiry: float = 0

        # Ayla tokens
        self._ayla_access_token: str | None = None
        self._ayla_refresh_token: str | None = None
        self._ayla_token_expiry: float = 0

        # Owlet account state
        self._account_id: str | None = None

        # Region-specific URLs
        if region == REGION_EU:
            self._accounts_base = OWLET_ACCOUNTS_BASE_EU
            self._devices_base = OWLET_DEVICES_BASE_EU
            self._ayla_sso_base = OWLET_AYLA_SSO_BASE_EU
        else:
            self._accounts_base = OWLET_ACCOUNTS_BASE
            self._devices_base = OWLET_DEVICES_BASE
            self._ayla_sso_base = OWLET_AYLA_SSO_BASE

        self._ayla_config = AYLA_CONFIG[region]
        self._firebase_config = FIREBASE_CONFIG[region]

    # ── Firebase Auth ─────────────────────────────────────────────────

    def _firebase_headers(self) -> dict[str, str]:
        """Headers to satisfy Android-restricted Firebase API keys."""
        return {
            "X-Android-Package": ANDROID_PACKAGE,
            "X-Android-Cert": ANDROID_CERT_SHA1,
            "Content-Type": "application/json",
        }

    async def _firebase_sign_in(self) -> None:
        """Sign in with email/password via Firebase REST API."""
        url = f"{FIREBASE_AUTH_URL}:signInWithPassword"
        params = {"key": self._firebase_config["api_key"]}
        payload = {
            "email": self._email,
            "password": self._password,
            "returnSecureToken": True,
        }

        resp = await self._session.post(
            url, params=params, json=payload, headers=self._firebase_headers()
        )
        if resp.status != 200:
            body = await resp.text()
            _LOGGER.error("Firebase sign-in failed: %s %s", resp.status, body)
            raise OwletAuthError(f"Firebase sign-in failed ({resp.status})")

        data = await resp.json()
        self._firebase_id_token = data["idToken"]
        self._firebase_refresh_token = data["refreshToken"]
        expires_in = int(data.get("expiresIn", 3600))
        self._firebase_token_expiry = time.time() + expires_in - 60

    async def _firebase_refresh(self) -> None:
        """Refresh the Firebase ID token."""
        if not self._firebase_refresh_token:
            await self._firebase_sign_in()
            return

        url = f"{FIREBASE_TOKEN_URL}"
        params = {"key": self._firebase_config["api_key"]}
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._firebase_refresh_token,
        }

        resp = await self._session.post(
            url, params=params, json=payload, headers=self._firebase_headers()
        )
        if resp.status != 200:
            _LOGGER.warning("Firebase token refresh failed, re-authenticating")
            await self._firebase_sign_in()
            return

        data = await resp.json()
        self._firebase_id_token = data["id_token"]
        self._firebase_refresh_token = data["refresh_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._firebase_token_expiry = time.time() + expires_in - 60

    async def _ensure_firebase_token(self) -> str:
        """Return a valid Firebase ID token, refreshing if needed."""
        if self._firebase_id_token and time.time() < self._firebase_token_expiry:
            return self._firebase_id_token

        if self._firebase_refresh_token:
            await self._firebase_refresh()
        else:
            await self._firebase_sign_in()

        if not self._firebase_id_token:
            raise OwletAuthError("Failed to obtain Firebase token")
        return self._firebase_id_token

    # ── Ayla Auth ─────────────────────────────────────────────────────

    async def _ayla_sign_in(self) -> None:
        """Authenticate with Ayla via the Owlet SSO mini-token bridge."""
        firebase_token = await self._ensure_firebase_token()

        # Step 1: Get mini token from Owlet SSO
        mini_url = f"{self._ayla_sso_base}/mini/"
        headers = {"Authorization": firebase_token}
        resp = await self._session.get(mini_url, headers=headers)
        if resp.status != 200:
            body = await resp.text()
            _LOGGER.error("Ayla SSO mini token failed: %s %s", resp.status, body)
            raise OwletAuthError(f"Ayla SSO mini token failed ({resp.status})")

        mini_data = await resp.json()
        mini_token = mini_data["mini_token"]

        # Step 2: Auth with Ayla using mini token via token_sign_in
        ayla_auth_url = (
            f"{self._ayla_config['user_field_url']}/api/v1/token_sign_in"
        )
        payload = {
            "token": mini_token,
            "app_id": self._ayla_config["app_id"],
            "app_secret": self._ayla_config["app_secret"],
            "provider": "owl_id",
        }
        resp = await self._session.post(ayla_auth_url, json=payload)
        data = await resp.json()
        if resp.status != 200 or "error" in data:
            _LOGGER.error("Ayla sign-in failed: %s %s", resp.status, data)
            raise OwletAuthError(f"Ayla sign-in failed: {data.get('error', resp.status)}")

        self._ayla_access_token = data["access_token"]
        self._ayla_refresh_token = data["refresh_token"]
        expires_in = int(data.get("expires_in", 86400))
        self._ayla_token_expiry = time.time() + expires_in - 300

    async def _ensure_ayla_token(self) -> str:
        """Return a valid Ayla access token, refreshing if needed."""
        if self._ayla_access_token and time.time() < self._ayla_token_expiry:
            return self._ayla_access_token

        if self._ayla_refresh_token and time.time() < self._ayla_token_expiry:
            await self._ayla_refresh_auth()
        else:
            await self._ayla_sign_in()

        if not self._ayla_access_token:
            raise OwletAuthError("Failed to obtain Ayla access token")
        return self._ayla_access_token

    async def _ayla_refresh_auth(self) -> None:
        """Refresh Ayla access token."""
        url = f"{self._ayla_config['user_field_url']}/users/refresh_token.json"
        payload = {"user": {"refresh_token": self._ayla_refresh_token}}
        resp = await self._session.post(url, json=payload)
        if resp.status != 200:
            _LOGGER.warning("Ayla token refresh failed, re-authenticating")
            await self._ayla_sign_in()
            return

        data = await resp.json()
        # refresh_token endpoint may wrap in "user" or return flat
        if "user" in data:
            data = data["user"]
        self._ayla_access_token = data["access_token"]
        self._ayla_refresh_token = data["refresh_token"]
        expires_in = int(data.get("expires_in", 86400))
        self._ayla_token_expiry = time.time() + expires_in - 300

    # ── Owlet REST API ────────────────────────────────────────────────

    async def _owlet_headers(self) -> dict[str, str]:
        """Build headers for Owlet REST API calls."""
        token = await self._ensure_firebase_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_account(self) -> dict[str, Any]:
        """Get the authenticated user's account from Firebase, then fetch from Owlet."""
        firebase_token = await self._ensure_firebase_token()

        # Use Firebase to get the user's UID which maps to the Owlet account
        url = f"{FIREBASE_AUTH_URL}:lookup"
        params = {"key": self._firebase_config["api_key"]}
        resp = await self._session.post(
            url,
            params=params,
            json={"idToken": firebase_token},
            headers=self._firebase_headers(),
        )
        if resp.status != 200:
            raise OwletApiError("Failed to look up Firebase user")

        data = await resp.json()
        uid = data["users"][0]["localId"]
        self._account_id = uid
        return {"account_id": uid, "email": data["users"][0].get("email", "")}

    async def get_devices(self) -> list[dict[str, Any]]:
        """Get all devices on the account via Owlet REST API."""
        if not self._account_id:
            await self.get_account()

        headers = await self._owlet_headers()
        url = f"{self._accounts_base}/v2/accounts/{self._account_id}/devices"
        resp = await self._session.get(url, headers=headers)
        if resp.status != 200:
            body = await resp.text()
            _LOGGER.error("Get devices failed: %s %s", resp.status, body)
            raise OwletApiError(f"Get devices failed ({resp.status})")

        data = await resp.json()
        return data.get("devices", [])

    async def get_services(self) -> list[dict[str, Any]]:
        """Get all services (device-profile pairings) on the account."""
        if not self._account_id:
            await self.get_account()

        headers = await self._owlet_headers()
        url = f"{self._accounts_base}/v2/accounts/{self._account_id}/services"
        resp = await self._session.get(url, headers=headers)
        if resp.status != 200:
            body = await resp.text()
            _LOGGER.error("Get services failed: %s %s", resp.status, body)
            raise OwletApiError(f"Get services failed ({resp.status})")

        data = await resp.json()
        return data.get("services", [])

    async def get_profiles(self) -> list[dict[str, Any]]:
        """Get all child profiles on the account."""
        if not self._account_id:
            await self.get_account()

        headers = await self._owlet_headers()
        url = f"{self._accounts_base}/v2/accounts/{self._account_id}/profiles"
        resp = await self._session.get(url, headers=headers)
        if resp.status != 200:
            body = await resp.text()
            _LOGGER.error("Get profiles failed: %s %s", resp.status, body)
            raise OwletApiError(f"Get profiles failed ({resp.status})")

        data = await resp.json()
        return data.get("profiles", [])

    # ── Ayla Device Data ──────────────────────────────────────────────

    async def _ayla_headers(self) -> dict[str, str]:
        """Build headers for Ayla API calls."""
        token = await self._ensure_ayla_token()
        return {
            "Authorization": f"auth_token {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def get_ayla_devices(self) -> list[dict[str, Any]]:
        """Get all devices registered in Ayla."""
        headers = await self._ayla_headers()
        url = f"{self._ayla_config['ads_field_url']}/apiv1/devices.json"
        resp = await self._session.get(url, headers=headers)
        if resp.status == 401:
            raise OwletAuthError("Ayla auth expired fetching devices")
        if resp.status != 200:
            body = await resp.text()
            _LOGGER.error("Ayla get devices failed: %s %s", resp.status, body)
            raise OwletApiError(f"Ayla get devices failed ({resp.status})")

        data = await resp.json()
        return data

    async def get_device_properties(self, dsn: str) -> dict[str, Any]:
        """Get all properties for an Ayla device."""
        headers = await self._ayla_headers()
        url = f"{self._ayla_config['ads_field_url']}/apiv1/dsns/{dsn}/properties.json"
        resp = await self._session.get(url, headers=headers)
        if resp.status == 401:
            raise OwletAuthError(f"Ayla auth expired fetching properties for {dsn}")
        if resp.status != 200:
            body = await resp.text()
            _LOGGER.error(
                "Ayla get properties for %s failed: %s %s", dsn, resp.status, body
            )
            raise OwletApiError(
                f"Ayla get properties for {dsn} failed ({resp.status})"
            )

        data = await resp.json()
        # Ayla returns a list of {"property": {...}} objects
        props: dict[str, Any] = {}
        for item in data:
            prop = item.get("property", {})
            name = prop.get("name")
            value = prop.get("value")
            if name:
                props[name] = value
        return props

    async def send_heartbeat(self, dsn: str) -> None:
        """Write APP_ACTIVE=1 to keep the base station streaming vitals.

        The base station only pushes REAL_TIME_VITALS while it receives
        periodic APP_ACTIVE=1 datapoints. Without this heartbeat, the
        vitals property goes stale within ~60 seconds.
        """
        headers = await self._ayla_headers()
        url = (
            f"{self._ayla_config['ads_field_url']}"
            f"/apiv1/dsns/{dsn}/properties/APP_ACTIVE/datapoints.json"
        )
        resp = await self._session.post(
            url, headers=headers, json={"datapoint": {"value": 1}}
        )
        if resp.status == 401:
            raise OwletAuthError(f"Ayla auth expired sending heartbeat for {dsn}")
        if resp.status not in (200, 201):
            _LOGGER.warning(
                "APP_ACTIVE heartbeat failed for %s: %s", dsn, resp.status
            )

    async def get_real_time_vitals(self, dsn: str) -> dict[str, Any] | None:
        """Get real-time vitals for a device.

        Sends APP_ACTIVE heartbeat then fetches REAL_TIME_VITALS property.
        Falls back to fetching all properties if that fails.
        """
        # Send heartbeat to keep base station streaming
        await self.send_heartbeat(dsn)

        headers = await self._ayla_headers()
        url = (
            f"{self._ayla_config['ads_field_url']}"
            f"/apiv1/dsns/{dsn}/properties/REAL_TIME_VITALS.json"
        )
        resp = await self._session.get(url, headers=headers)
        if resp.status == 401:
            raise OwletAuthError(f"Ayla auth expired for {dsn}")

        if resp.status == 200:
            data = await resp.json()
            raw = data.get("property", {}).get("value")
            if raw and isinstance(raw, str):
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    _LOGGER.warning(
                        "Failed to parse REAL_TIME_VITALS for %s", dsn
                    )

        # Slow fallback: fetch all properties
        _LOGGER.debug("Falling back to full property fetch for %s", dsn)
        props = await self.get_device_properties(dsn)

        rtv_raw = props.get("REAL_TIME_VITALS")
        if rtv_raw and isinstance(rtv_raw, str):
            try:
                return json.loads(rtv_raw)
            except json.JSONDecodeError:
                pass

        vitals: dict[str, Any] = {}
        prop_map = {
            "HEART_RATE": "hr",
            "OXYGEN_LEVEL": "ox",
            "SKIN_TEMPERATURE": "st",
            "MOVEMENT": "mv",
            "BATT_LEVEL": "bat",
            "CHARGE_STATUS": "chg",
            "SOCK_CONNECTION": "sc",
            "BASE_STATION_ON": "bso",
            "SLEEP_STATE": "ss",
            "BATT_TIME_REMAINING": "btt",
            "ALRT_PAUSED_STATUS": "aps",
            "CURRENT_ALERTS_MASK": "alrt",
            "BLUETOOTH_RSSI_LEVEL": "rsi",
        }
        for ayla_name, key in prop_map.items():
            if ayla_name in props and props[ayla_name] is not None:
                vitals[key] = props[ayla_name]

        return vitals if vitals else None

    # ── Combined Discovery ────────────────────────────────────────────

    async def authenticate(self) -> bool:
        """Authenticate with all services. Returns True on success."""
        await self._firebase_sign_in()
        await self.get_account()
        await self._ayla_sign_in()
        return True

    async def discover_devices(self) -> list[dict[str, Any]]:
        """Discover all sock/cam devices and their associated profiles.

        Returns a list of dicts with device info, profile name, and DSN.
        """
        services = await self.get_services()
        profiles = await self.get_profiles()
        ayla_devices = await self.get_ayla_devices()

        # Build profile name lookup: "accounts/.../profiles/xyz" -> profile data
        profile_map: dict[str, dict[str, Any]] = {}
        for p in profiles:
            name = p.get("name", "")
            profile_map[name] = p

        # Build Ayla device lookup by DSN
        ayla_map: dict[str, dict[str, Any]] = {}
        for d in ayla_devices:
            dev = d.get("device", d)
            dsn = dev.get("dsn", "")
            if dsn:
                ayla_map[dsn] = dev

        devices: list[dict[str, Any]] = []
        for svc in services:
            svc_device = svc.get("device") or {}
            dsn = svc_device.get("dsn")
            if not dsn:
                continue

            # Find linked profile
            profile_names = svc.get("profiles", [])
            profile_data = None
            for pname in profile_names:
                if pname in profile_map:
                    profile_data = profile_map[pname]
                    break

            child_name = "Unknown"
            if profile_data:
                child_name = (
                    profile_data.get("givenName")
                    or profile_data.get("name", "").split("/")[-1]
                    or "Unknown"
                )

            ayla_dev = ayla_map.get(dsn, {})
            model = ayla_dev.get("model", svc_device.get("deviceType", "Unknown"))
            sw_version = svc_device.get("firmwareVersion")

            devices.append(
                {
                    "dsn": dsn,
                    "service_name": svc.get("name", ""),
                    "service_type": svc.get("serviceType", ""),
                    "display_name": svc.get("displayName") or child_name,
                    "child_name": child_name,
                    "device_type": svc_device.get("deviceType", ""),
                    "model": model,
                    "sw_version": sw_version,
                    "product_name": ayla_dev.get("product_name", ""),
                }
            )

        return devices
