"""Constants for the Owlet Dream integration."""

DOMAIN = "owlet_dream"

CONF_REGION = "region"

REGION_US = "us"
REGION_EU = "eu"

# Owlet REST API base URLs (no env suffix for production)
OWLET_ACCOUNTS_BASE = "https://accounts.owletdata.com"
OWLET_ACCOUNTS_BASE_EU = "https://accounts.eu.owletdata.com"
OWLET_DEVICES_BASE = "https://devices-public.owletdata.com"
OWLET_DEVICES_BASE_EU = "https://devices-public.eu.owletdata.com"
OWLET_AYLA_SSO_BASE = "https://ayla-sso.owletdata.com"
OWLET_AYLA_SSO_BASE_EU = "https://ayla-sso.eu.owletdata.com"

# Firebase configuration per region
FIREBASE_CONFIG = {
    REGION_US: {
        "api_key": "AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA",
        "project_id": "owletcare-prod",
        "auth_domain": "owletcare-prod.firebaseapp.com",
    },
    REGION_EU: {
        "api_key": "AIzaSyDm6EhV70wudwN3iOSq3vTjtsdGjdFLuuM",
        "project_id": "owletcare-prod-eu",
        "auth_domain": "owletcare-prod-eu.firebaseapp.com",
    },
}

# Ayla Networks credentials per region
AYLA_CONFIG = {
    REGION_US: {
        "app_id": "owlet-dream-app-Qg-id",
        "app_secret": "owlet-dream-app-EoSrt1LxspaBFtRZs4OEMhG148Q",
        "user_field_url": "https://user-field-1a2039d9.aylanetworks.com",
        "ads_field_url": "https://ads-field-1a2039d9.aylanetworks.com",
    },
    REGION_EU: {
        "app_id": "OwletCare-Android-EU-fw-id",
        "app_secret": "OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw",
        "user_field_url": "https://user-field-eu-1a2039d9.aylanetworks.com",
        "ads_field_url": "https://ads-field-eu-1a2039d9.aylanetworks.com",
    },
}

# Firebase REST Auth endpoint
FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts"
FIREBASE_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"

# Android app identity -- required for Android-restricted Firebase API keys
ANDROID_PACKAGE = "com.owletcare.sleep"
ANDROID_CERT_SHA1 = "2A3BC26DB0B8B0792DBE28E6FFDC2598F9B12B74"

# Polling interval in seconds
DEFAULT_SCAN_INTERVAL = 30

# Real-time vitals JSON keys from Ayla REAL_TIME_VITALS property
VITALS_KEY_OXYGEN = "ox"
VITALS_KEY_HEART_RATE = "hr"
VITALS_KEY_MOVEMENT = "mv"
VITALS_KEY_SOCK_CONNECTION = "sc"
VITALS_KEY_SKIN_TEMP = "st"
VITALS_KEY_BASE_STATION_ON = "bso"
VITALS_KEY_BATTERY = "bat"
VITALS_KEY_BATTERY_TIME = "btt"
VITALS_KEY_CHARGING = "chg"
VITALS_KEY_ALERT_PAUSED = "aps"
VITALS_KEY_ALERTS_MASK = "alrt"
VITALS_KEY_OTA_STATUS = "ota"
VITALS_KEY_SOCK_READINGS = "srf"
VITALS_KEY_RSSI = "rsi"
VITALS_KEY_SOFT_BRICK = "sb"
VITALS_KEY_SLEEP_STATE = "ss"
VITALS_KEY_MOVEMENT_BUCKET = "mvb"
VITALS_KEY_OXYGEN_10MIN_AVG = "oxta"
VITALS_KEY_WELLNESS_ALERT = "onm"
VITALS_KEY_HW_VERSION = "hw"
VITALS_KEY_MONITOR_START = "mst"
VITALS_KEY_BS_BATTERY = "bsb"
VITALS_KEY_RECOVERY = "mrs"
VITALS_KEY_PERFUSION_INDEX = "pi"
VITALS_KEY_HR_LOW_THRESH = "hrl"
VITALS_KEY_HR_HIGH_THRESH = "hrh"
VITALS_KEY_OX_LOW_THRESH = "oxl"
VITALS_KEY_OX_HIGH_THRESH = "oxh"
VITALS_KEY_ALARM_MASK = "aem"
VITALS_KEY_MONITOR_SESSION = "mts"

# Sleep state values
SLEEP_STATE_UNKNOWN = 0
SLEEP_STATE_AWAKE = 1
SLEEP_STATE_LIGHT = 8
SLEEP_STATE_DEEP = 15

SLEEP_STATE_NAMES = {
    SLEEP_STATE_UNKNOWN: "Unknown",
    SLEEP_STATE_AWAKE: "Awake",
    SLEEP_STATE_LIGHT: "Light Sleep",
    SLEEP_STATE_DEEP: "Deep Sleep",
}
