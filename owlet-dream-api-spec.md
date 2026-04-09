# Owlet Dream API Specification

Reverse-engineered from Owlet Dream Android app v3.30.0 (`com.owletcare.sleep`).

## Overview

The Owlet Dream platform uses a REST API backed by multiple microservices, all hosted under `*.owletdata.com`. Authentication is handled via Firebase Auth, with ID tokens passed as Bearer tokens. Data is serialized as JSON using Moshi.

---

## Base URLs

All service URLs follow the pattern: `https://{service}{envSuffix}.owletdata.com/`

### Environments

| Environment | Suffix     | Example                                      |
|-------------|------------|----------------------------------------------|
| Production  | *(empty)*  | `https://accounts.owletdata.com/`            |
| Europe      | `.eu`      | `https://accounts.eu.owletdata.com/`         |
| Staging     | `.staging` | `https://accounts.staging.owletdata.com/`    |
| Development | `.dev`     | `https://accounts.dev.owletdata.com/`        |

### Services

| Service                    | Hostname Prefix            | Purpose                        |
|----------------------------|----------------------------|--------------------------------|
| Accounts API               | `accounts`                 | Accounts, profiles, events, services, clips, tips, insights, sleep window |
| Device Capabilities        | `devices-public`           | Device info, OTA checks        |
| Device Registration        | `app-device-registration`  | Sock/camera registration       |
| Push Notifications         | `trigger-wrapper`          | Push notification triggers     |
| User Mapper                | `user-mapper`              | Smart sock user mapping        |
| Ayla SSO                   | `ayla-sso`                 | Ayla Networks token minification |

---

## Authentication & Credentials

### Authentication Flow Overview

The app uses a multi-layered auth system:

1. **Firebase Auth** -- user signs up/in via Firebase, gets a Firebase ID token
2. **Owlet REST APIs** -- use the Firebase ID token as `Authorization: Bearer <token>`
3. **Ayla SSO** -- the Firebase token is exchanged for an Ayla `mini_token` via the Owlet SSO bridge
4. **Ayla SDK** -- uses the mini token + app credentials to authenticate with Ayla IoT services (for sock communication)

### Firebase Configuration

#### US Production (default)

| Key                    | Value                                                        |
|------------------------|--------------------------------------------------------------|
| Project ID             | `owletcare-prod`                                             |
| API Key                | `AIzaSyCsDZ8kWxQuLJAMVnmEhEkayH1TSxKXfGA`                  |
| API Key (from strings) | `AIzaSyDlfp3urNTbyhCtHOCxZBOjHQf4WuN_Aws`                  |
| Application ID         | `1:561089101102:android:7703b1c03673b7a486cebf`              |
| Database URL           | `https://owletcare-prod.firebaseio.com`                      |
| Storage Bucket         | `owletcare-prod.appspot.com`                                 |
| GCM Sender ID          | `561089101102`                                               |
| Web Client ID          | `561089101102-batg9v6t3l2jkkri1s58dfg48si9mfta.apps.googleusercontent.com` |

#### EU Production

| Key                    | Value                                                        |
|------------------------|--------------------------------------------------------------|
| Project ID             | `owletcare-prod-eu`                                          |
| API Key                | `AIzaSyDm6EhV70wudwN3iOSq3vTjtsdGjdFLuuM`                  |
| Application ID         | `1:395737756031:android:f1145b652faa5f4a`                    |
| Database URL           | `https://owletcare-prod-eu.firebaseio.com`                   |
| Storage Bucket         | `owletcare-prod-eu.appspot.com`                              |

#### Staging

| Key                    | Value                                                        |
|------------------------|--------------------------------------------------------------|
| Project ID             | `owletcare-staging`                                          |
| API Key                | `AIzaSyBL5_z7YazZJ7DqPFstG2ufY0wRoKEHMrk`                  |
| Application ID         | `1:172090348323:android:5da151abe890eaf3d1f296`              |
| Database URL           | `https://owletcare-staging.firebaseio.com`                   |
| Storage Bucket         | `owletcare-staging.appspot.com`                              |

#### Development

| Key                    | Value                                                        |
|------------------------|--------------------------------------------------------------|
| Project ID             | `owletcare-dev`                                              |
| API Key                | `AIzaSyAkicSeKouE_Yuq6gS9HxO5WiX9pwLENjw`                  |
| Application ID         | `1:704296504428:android:a85c8029434cebe0105c49`              |
| Database URL           | `https://owletcare-dev.firebaseio.com`                       |
| Storage Bucket         | `owletcare-dev.appspot.com`                                  |

### Ayla Networks Credentials

The sock communicates through the Ayla IoT platform. The app selects credentials based on the combination of Ayla environment (dev/field) and Firebase environment (dev/staging/prod).

#### US Production (Field Ayla + Prod Firebase)

| Key        | Value                                                     |
|------------|-----------------------------------------------------------|
| App ID     | `owlet-dream-app-Qg-id`                                  |
| App Secret | `owlet-dream-app-EoSrt1LxspaBFtRZs4OEMhG148Q`           |

#### EU Production (Field Ayla + EU Firebase)

| Key        | Value                                                     |
|------------|-----------------------------------------------------------|
| App ID     | `OwletCare-Android-EU-fw-id`                              |
| App Secret | `OwletCare-Android-EU-JKupMPBoj_Npce_9a95Pc8Qo0Mw`      |

#### US Staging (Field Ayla + Staging Firebase)

| Key        | Value                                                     |
|------------|-----------------------------------------------------------|
| App ID     | `owlet-dream-app-NA-id`                                   |
| App Secret | `owlet-dream-app-NF1Hc2-YSOVvgLFqK5zLZpQzLKU`           |

#### US Development (Dev Ayla + Dev Firebase)

| Key        | Value                                                     |
|------------|-----------------------------------------------------------|
| App ID     | `owlet-dream-app-pg-id`                                   |
| App Secret | `owlet-dream-app-SG90w4rdAZYtndTtTpCWJbVPkGA`            |

#### US Beta (Dev Ayla + Prod Firebase)

| Key        | Value                                                     |
|------------|-----------------------------------------------------------|
| App ID     | `sso-beta-Iw-id`                                          |
| App Secret | `sso-beta-oqu2V_-gOPyGpo5iasGqUw7QzgQ`                  |

#### US Staging-Dev (Dev Ayla + Staging Firebase)

| Key        | Value                                                     |
|------------|-----------------------------------------------------------|
| App ID     | `sso-staging-5A-id`                                       |
| App Secret | `sso-staging-YYP9ZgpJPzIzY-Abai7u9lMiMKY`               |

### Ayla SSO Token Exchange

To authenticate with Ayla services, the app first minifies the Firebase token:

```
POST https://ayla-sso{env}.owletdata.com/mini/
```

**Headers:**
```http
Authorization: <firebase_id_token>
```

**Response:**
```json
{
  "mini_token": "<minified_token>"
}
```

The mini token is then used to authenticate with the Ayla SDK:

```json
{
  "token": "<firebase_id_token>",
  "app_id": "<ayla_app_id>",
  "app_secret": "<ayla_app_secret>",
  "provider": "owl_id"
}
```

### Owlet REST API Authentication

All Owlet REST API calls (accounts, devices-public, app-device-registration, trigger-wrapper, user-mapper) use the Firebase ID token directly:

```http
Authorization: Bearer <firebase_id_token>
```

### Standard Request Headers

All requests include:

```http
Accept: application/json
Content-Type: application/json
Accept-Language: <locale>
User-Agent: <appVersion>/<deviceModel>, Android <version>
```

### Client-Key Header

Some endpoints (notification preferences, camera-related) also require:

```http
Client-Key: <clientKey>
```

The `clientKey` is a per-device identifier managed via the notification client registration system (see Notification Preferences API). It is NOT a static secret -- it is generated and stored per-device during push notification setup.

### HTTP Client Configuration

- Retry on connection failure: disabled (`retryOnConnectionFailure = false`)
- Call timeout: 0 (no timeout)
- JSON serialization: Moshi with custom adapters
- Retry for non-Retrofit calls: up to 7 retries, 90-second overall timeout

---

## Accounts API

**Base URL:** `https://accounts{env}.owletdata.com/`

### Create Account

```
POST v2/accounts
```

**Request Body:** `ApiCreateAccountRequest`

```json
{
  "account": { ... }
}
```

**Response:** `ApiAccount`

```json
{
  "birthdate": "2000-01-15",
  "email": "user@example.com",
  "givenName": "Jane",
  "familyName": "Doe",
  "name": "accounts/abc123",
  "phoneNumber": "+15551234567",
  "phoneNumberLegacy": "5551234567"
}
```

### Get Account

```
GET v2/accounts/{accountId}
```

| Parameter   | In   | Type   | Required |
|-------------|------|--------|----------|
| `accountId` | path | string | yes      |

**Response:** `ApiAccount`

### Update Account

```
PATCH v2/accounts/{accountId}
```

| Parameter   | In   | Type   | Required |
|-------------|------|--------|----------|
| `accountId` | path | string | yes      |

**Request Body:** `ApiAccountPatch`

All fields use an optional-value wrapper (present/absent/null semantics for PATCH):

```json
{
  "birthdate": "2000-01-15",
  "email": "user@example.com",
  "givenName": "Jane",
  "familyName": "Doe",
  "phoneNumber": "+15551234567"
}
```

**Response:** `ApiAccount`

### Delete Account

```
DELETE v2/accounts/{accountId}
```

| Parameter   | In   | Type   | Required |
|-------------|------|--------|----------|
| `accountId` | path | string | yes      |

**Response:** `204 No Content`

### Post Account Analytics

```
POST v2/accounts/{accountId}/analytics/{eventType}
```

| Parameter   | In   | Type   | Required |
|-------------|------|--------|----------|
| `accountId` | path | string | yes      |
| `eventType` | path | string | yes      |

**Request Body:** `AccountAnalyticsData`

```json
{
  "metricValue": "some_value"
}
```

**Response:** `204 No Content`

---

## Profiles API

**Base URL:** `https://accounts{env}.owletdata.com/`

### List Profiles

```
GET v2/accounts/{accountId}/profiles
```

| Parameter   | In   | Type   | Required |
|-------------|------|--------|----------|
| `accountId` | path | string | yes      |

**Response:** `ApiListProfilesResponse`

```json
{
  "profiles": [
    {
      "name": "accounts/abc123/profiles/prof456",
      "birthdate": "2024-03-15",
      "dueDate": "2024-03-10",
      "profileType": "PROFILE_TYPE_CHILD",
      "givenName": "Baby",
      "gender": "GENDER_FEMALE",
      "nicuStay": false,
      "races": ["RACE_WHITE_CAUCASIAN"],
      "relationship": "RELATIONSHIP_BIOLOGICAL",
      "weight": 3.5
    }
  ]
}
```

### Create Profile

```
POST v2/accounts/{accountId}/profiles
```

**Request Body:** `ApiCreateProfileRequest`

```json
{
  "profile": {
    "name": null,
    "birthdate": "2024-03-15",
    "dueDate": null,
    "profileType": "PROFILE_TYPE_CHILD",
    "givenName": "Baby",
    "gender": "GENDER_MALE",
    "nicuStay": false,
    "races": [],
    "relationship": "RELATIONSHIP_BIOLOGICAL",
    "weight": null
  },
  "requestId": "unique-request-id"
}
```

**Response:** `ApiProfile`

### Delete Profile

```
DELETE v2/accounts/{accountId}/profiles/{profileId}
```

**Response:** `204 No Content`

### Reassign Profile

```
POST v2/accounts/{accountId}/profiles/{profileId}:reassign
```

**Request Body:** `ApiReassignToProfileRequest`

```json
{
  "services": ["accounts/abc123/services/svc789"]
}
```

**Response:** `204 No Content`

### Profile Photo

**Base URL:** `https://accounts{env}.owletdata.com/`

#### Get Photo

```
GET v0/accounts/{accountId}/profiles/{profileId}/photo
```

#### Update Photo

```
PUT v0/accounts/{accountId}/profiles/{profileId}/photo
```

#### Delete Photo

```
DELETE v0/accounts/{accountId}/profiles/{profileId}/photo
```

---

## Profile Enums

### Gender

| Value            | JSON                |
|------------------|---------------------|
| Male             | `GENDER_MALE`       |
| Female           | `GENDER_FEMALE`     |
| Unknown          | `GENDER_UNKNOWN`    |

### Profile Type

| Value     | JSON                    |
|-----------|-------------------------|
| Child     | `PROFILE_TYPE_CHILD`    |
| Pregnancy | `PROFILE_TYPE_PREGNANCY`|
| Unknown   | `PROFILE_TYPE_UNKNOWN`  |

### Relationship

| Value        | JSON                          |
|--------------|-------------------------------|
| Unknown      | `RELATIONSHIP_UNKNOWN`        |
| Biological   | `RELATIONSHIP_BIOLOGICAL`     |
| Adopted      | `RELATIONSHIP_ADOPTED`        |
| GeneralCare  | `RELATIONSHIP_GENERAL_CARE`   |
| Grandchild   | `RELATIONSHIP_GRANDCHILD`     |
| OtherFamily  | `RELATIONSHIP_OTHER_FAMILY`   |

### Race

| Value                    | JSON                                      |
|--------------------------|-------------------------------------------|
| Other                    | `RACE_OTHER`                              |
| WhiteCaucasian           | `RACE_WHITE_CAUCASIAN`                    |
| HispanicLatino           | `RACE_HISPANIC_LATINO`                    |
| BlackAfricanAmerican     | `RACE_BLACK_AFRICAN_AMERICAN`             |
| Asian                    | `RACE_ASIAN`                              |
| NativeAmericanAlaska     | `RACE_AMERICAN_INDIAN_ALASKA_NATIVE`      |
| PacificIslander          | `RACE_NATIVE_HAWAIIAN_PACIFIC_ISLANDER`   |
| Unknown                  | `RACE_UNKNOWN`                            |

### Pregnancy Risk

| Value                      | JSON                                            |
|----------------------------|-------------------------------------------------|
| OTHER                      | `PREGNANCY_RISK_OTHER`                          |
| HIGH_BLOOD_PRESSURE        | `PREGNANCY_RISK_HIGH_BLOOD_PRESSURE`            |
| DIABETES                   | `PREGNANCY_RISK_DIABETES`                       |
| GESTATIONAL_DIABETES       | `PREGNANCY_RISK_GESTATIONAL_DIABETES`           |
| INFECTIONS                 | `PREGNANCY_RISK_INFECTIONS`                     |
| PREECLAMPSIA               | `PREGNANCY_RISK_PREECLAMPSIA`                   |
| PRETERM_LABOR              | `PREGNANCY_RISK_PRETERM_LABOR`                  |
| MISCARRIAGE                | `PREGNANCY_RISK_MISCARRIAGE`                    |
| STILLBIRTH                 | `PREGNANCY_RISK_STILLBIRTH`                     |
| PLACENTA_PREVIA_ABRUPTION  | `PREGNANCY_RISK_PLACENTA_PREVIA_ABRUPTION`      |
| CURRENT_DRUG_OR_ALCOHOL_USE| `PREGNANCY_RISK_CURRENT_DRUG_OR_ALCOHOL_USE`    |
| UNKNOWN                    | `PREGNANCY_RISK_UNKNOWN`                        |

### Pregnancy Status

| Value      | JSON                            |
|------------|---------------------------------|
| PREGNANT   | `PREGNANCY_STATUS_PREGNANT`     |
| LIVE_BIRTH | `PREGNANCY_STATUS_LIVE_BIRTH`   |
| STILLBIRTH | `PREGNANCY_STATUS_STILLBIRTH`   |
| MISCARRIAGE| `PREGNANCY_STATUS_MISCARRIAGE`  |
| UNKNOWN    | `PREGNANCY_STATUS_UNKNOWN`      |

---

## Services API

**Base URL:** `https://accounts{env}.owletdata.com/`

A "service" represents a device subscription/pairing (sock or camera) linked to an account.

### List Services

```
GET v2/accounts/{accountId}/services
```

**Response:** `ApiListServicesResponse`

```json
{
  "services": [
    {
      "name": "accounts/abc123/services/svc789",
      "serviceType": "SERVICE_TYPE_SOCK",
      "device": {
        "dsn": "AC000W012345678",
        "firmwareVersion": "1.2.3",
        "deviceType": "DEVICE_TYPE_SMARTSOCK3_SLEEP"
      },
      "displayName": "Baby's Sock",
      "profiles": ["accounts/abc123/profiles/prof456"]
    }
  ]
}
```

### Create Service

```
POST v2/accounts/{accountId}/services
```

**Request Body:** `ApiCreateServiceRequest`

```json
{
  "service": {
    "serviceType": "SERVICE_TYPE_SOCK",
    "displayName": "Baby's Sock"
  },
  "requestId": "unique-request-id",
  "registrationToken": "token"
}
```

**Response:** `ApiService`

### Update Service

```
PATCH v2/accounts/{accountId}/services/{serviceId}
```

**Request Body:** `ApiServicePatch`

```json
{
  "serviceType": "SERVICE_TYPE_SOCK",
  "displayName": "New Name"
}
```

**Response:** `ApiService`

### Delete Service

```
DELETE v2/accounts/{accountId}/services/{serviceId}
```

**Response:** `204 No Content`

### Service Type Enum

| Value   | JSON                   |
|---------|------------------------|
| SOCK    | `SERVICE_TYPE_SOCK`    |
| CAMERA  | `SERVICE_TYPE_CAMERA`  |
| UNKNOWN | *(fallback)*           |

### Device Type Enum

| Value              | JSON                               |
|--------------------|--------------------------------------|
| SMARTSOCK          | `DEVICE_TYPE_SMARTSOCK`              |
| SMARTSOCK3         | `DEVICE_TYPE_SMARTSOCK3`             |
| SMARTSOCK3_MEDICAL | `DEVICE_TYPE_SMARTSOCK3_DREAMSAMD`   |
| SMARTSOCK4_MEDICAL | `DEVICE_TYPE_SMARTSOCK4`             |
| DREAMSOCK          | `DEVICE_TYPE_SMARTSOCK3_SLEEP`       |
| CAMERA             | `DEVICE_TYPE_CAMERA`                 |
| CAMERA_V2          | `DEVICE_TYPE_CAMERA2`                |
| CAMERA_V3          | `DEVICE_TYPE_CAMERA3`                |
| BABYSAT            | `DEVICE_TYPE_SMARTSOCK3_MEDICAL`     |
| UNKNOWN            | *(fallback)*                         |

---

## Events API

**Base URL:** `https://accounts{env}.owletdata.com/`

Events track things like sleep sessions, alerts, sound/motion detections, etc.

### List Events

```
GET v2/accounts/{accountId}/events
```

| Parameter   | In    | Type   | Required | Description             |
|-------------|-------|--------|----------|-------------------------|
| `accountId` | path  | string | yes      |                         |
| `filter`    | query | string | no       | Filter expression        |
| `totalSize` | query | int    | yes      | Page size                |

**Response:** `ApiListEventsResponse`

```json
{
  "events": [
    {
      "name": "accounts/abc123/events/evt001",
      "profile": "accounts/abc123/profiles/prof456",
      "eventTime": "2024-03-15",
      "startTime": "2024-03-15T20:30:00Z",
      "endTime": "2024-03-16T06:15:00Z",
      "isDiscrete": false,
      "eventType": "PROFILE_SLEEP",
      "notes": "Good night",
      "deviceType": "DEVICE_TYPE_SMARTSOCK3_SLEEP",
      "isUserModified": false,
      "profileType": "PROFILE_TYPE_CHILD",
      "service": "accounts/abc123/services/svc789",
      "serviceType": "SERVICE_TYPE_SOCK"
    }
  ]
}
```

### Create Event

```
POST v2/accounts/{accountId}/events
```

**Request Body:** `ApiCreateEventRequest`

```json
{
  "event": {
    "startTime": "2024-03-15T20:30:00Z",
    "endTime": "2024-03-16T06:15:00Z",
    "eventType": "PROFILE_SLEEP",
    "notes": "Slept well",
    "profile": "accounts/abc123/profiles/prof456"
  }
}
```

**Response:** `ApiEvent`

### Update Event

```
PATCH v2/accounts/{accountId}/events/{eventId}
```

**Request Body:** `ApiEventPatch`

All fields use optional-value wrapper:

```json
{
  "startTime": "2024-03-15T20:30:00Z",
  "endTime": "2024-03-16T06:15:00Z",
  "eventType": "PROFILE_SLEEP",
  "notes": "Updated notes",
  "profile": "accounts/abc123/profiles/prof456"
}
```

**Response:** `ApiEvent`

### Delete Event

```
DELETE v2/accounts/{accountId}/events/{eventId}
```

**Response:** `204 No Content`

### Event Type Enum

| Value                            | JSON                              |
|----------------------------------|-----------------------------------|
| Sock Unspecified                 | `SERVICE_SOCK_UNSPECIFIED`        |
| High Heart Rate Alert            | `PROFILE_HIGH_HR_ALRT`           |
| Low Battery Alert                | `SERVICE_SOCK_LOW_BATT_ALRT`     |
| Low Heart Rate Alert             | `PROFILE_LOW_HR_ALRT`            |
| Low Integrity Read               | `SERVICE_SOCK_LOW_INTEG_READ`    |
| Low Oxygen Alert                 | `PROFILE_LOW_OX_ALRT`           |
| Sock Disconnect Alert            | `SERVICE_SOCK_SOCK_DISCON_ALRT`  |
| Sock Off                         | `SERVICE_SOCK_SOCK_OFF`          |
| Camera Unspecified               | `SERVICE_CAMERA_UNSPECIFIED`     |
| Camera Sound Detection           | `SERVICE_CAMERA_SOUND`           |
| Camera Motion Detection          | `SERVICE_CAMERA_MOTION`          |
| Sleep Session                    | `PROFILE_SLEEP`                  |
| Unknown                          | `EVENT_TYPE_UNKNOWN`             |

---

## Insights API

**Base URL:** `https://accounts{env}.owletdata.com/`

### Get Insights (Summary)

```
GET v2/accounts/{accountId}/profiles/{profileId}/insights
```

| Parameter              | In    | Type    | Required | Default | Description                |
|------------------------|-------|---------|----------|---------|----------------------------|
| `accountId`            | path  | string  | yes      |         |                            |
| `profileId`            | path  | string  | yes      |         |                            |
| `timeZone`             | query | string  | yes      |         | IANA timezone              |
| `morningReportEndDate` | query | string  | yes      |         | ISO date                   |
| `temperatureUnit`      | query | string  | yes      |         | `c` or `f`                |
| `healthSummary`        | query | boolean | no       | `false` | Include health insights    |
| `morningReports`       | query | boolean | no       | `true`  | Include morning reports    |
| `cameraSummary`        | query | boolean | no       | `false` | Include camera environment |
| `morningReportDates`   | query | boolean | no       | `false` |                            |

### Get Insights (Full)

```
GET v2/accounts/{accountId}/profiles/{profileId}/insights
```

| Parameter                | In    | Type    | Required | Default | Description                |
|--------------------------|-------|---------|----------|---------|----------------------------|
| `accountId`              | path  | string  | yes      |         |                            |
| `profileId`              | path  | string  | yes      |         |                            |
| `timeZone`               | query | string  | yes      |         | IANA timezone              |
| `morningReportStartDate` | query | string  | yes      |         | ISO date                   |
| `morningReportEndDate`   | query | string  | yes      |         | ISO date                   |
| `temperatureUnit`        | query | string  | yes      |         | `c` or `f`                |
| `healthSummary`          | query | boolean | no       | `true`  | Include health insights    |
| `morningReports`         | query | boolean | no       | `true`  | Include morning reports    |
| `cameraSummary`          | query | boolean | no       | `true`  | Include camera environment |
| `morningReportDates`     | query | boolean | no       | `false` |                            |
| `sleepSummary`           | query | boolean | no       | `true`  | Include 7-night sleep summary |

**Response:** `ApiInsights`

```json
{
  "healthSummary": { ... },
  "morningReports": [ ... ],
  "cameraSummary": { ... },
  "sleepSummary": { ... }
}
```

### ApiInsights Response Schema

```json
{
  "healthSummary": {
    "todaysSummary": "Your baby slept well...",
    "sockWearingScore": 85,
    "ageInWeeks": 24,
    "pulseRateInsights": {
      "funInsight": "...",
      "comparativeInsight": "...",
      "trendInsight": "...",
      "weeklyAvg": 120
    },
    "oxygenInsights": {
      "funInsight": "...",
      "comparativeInsight": "...",
      "trendInsight": "...",
      "weeklyAvg": 98
    },
    "comfortTemperatureInsights": {
      "trendInsight": "...",
      "weeklyReport": "..."
    },
    "movementInsights": {
      "trendInsight": "...",
      "weeklyReport": "..."
    },
    "sevenDay": [
      {
        "summaryDate": "2024-03-15",
        "dayLabelAbbreviated": "Fri",
        "usedSock": true,
        "pulseRate": {
          "insight": "...",
          "distribution": [{"range": "60-80", "value": 0.45}],
          "min": 60,
          "max": 160,
          "avg": 120,
          "trending": "LOW"
        },
        "oxygen": { "..." : "..." },
        "temperature": {
          "deviation": 0.5,
          "trending": "AVERAGE",
          "gauge": 75
        },
        "movement": { "..." : "..." }
      }
    ]
  },
  "morningReports": [
    {
      "reportDateStart": "2024-03-15",
      "reportDateEnd": "2024-03-16",
      "defaultWindow": false,
      "defaultWindowStart": "19:00",
      "nightWindowStart": "20:30",
      "nightWindowEnd": "06:15",
      "sleepGrade": "DREAMY",
      "totalSleepMinutes": 540,
      "wakings": 2,
      "sleepStateDurationsMinutes": {
        "0": 30,
        "1": 60,
        "8": 270,
        "15": 180
      },
      "longestSleepSegmentMinutes": 240,
      "funInsight": "...",
      "sleepInsight": "...",
      "sleepInsightTitle": "...",
      "sleepGraph": {
        "sleepStates": [
          {"sleepState": 15, "startTime": "2024-03-15T20:30:00-07:00"},
          {"sleepState": 8, "startTime": "2024-03-15T21:00:00-07:00"}
        ],
        "sleepEndTime": "2024-03-16T06:15:00-07:00"
      },
      "sleepPositionInsight": "...",
      "combinedSleepPositionDurationMinutes": {
        "TUMMY": 60,
        "BACK": 400,
        "SIDE": 80
      },
      "combinedSleepPositionGraph": {
        "TUMMY": {
          "durationMinutes": 60,
          "percentageOfSleep": 11,
          "pulseRateAvg": 118,
          "oxygenAvg": 98
        },
        "BACK": { "..." : "..." },
        "SIDE": { "..." : "..." }
      },
      "developmentTip": "..."
    }
  ],
  "cameraSummary": {
    "environmentInsight": "...",
    "temperatureUnit": "f",
    "roomTemperatureInsights": {
      "historyInsight": "...",
      "hourlyHistory": [
        {"dateTime": "2024-03-15T20:00:00-07:00", "value": 72.5}
      ],
      "trendInsight": "...",
      "weeklyMin": 68.0,
      "weeklyMinCondition": "COOL",
      "weeklyMax": 74.0,
      "weeklyMaxCondition": "IN_RANGE",
      "weeklyAvg": 71.5,
      "weeklyAvgCondition": "IN_RANGE",
      "historyAvg": 71.0,
      "historyAvgCondition": "IN_RANGE"
    },
    "roomHumidityInsights": { "..." : "..." },
    "roomNoiseInsights": { "..." : "..." },
    "sevenDay": [
      {
        "summaryDate": "2024-03-15",
        "dayLabelAbbreviated": "Fri",
        "roomTemperature": {
          "min": 68.0,
          "max": 74.0,
          "avg": 71.5,
          "condition": "IN_RANGE"
        },
        "roomHumidity": { "..." : "..." },
        "roomNoise": { "..." : "..." }
      }
    ]
  },
  "sleepSummary": {
    "nightWindowStart": "20:30",
    "nightWindowEnd": "06:15",
    "nightDurationInsights": {
      "trendInsight": "...",
      "weeklyAvg": 540
    },
    "nightRoutineInsights": {
      "coreSleepOnsetTimeAvg": "20:45",
      "coreSleepWakeUpTimeAvg": "06:10",
      "trendInsight": "..."
    },
    "nightStretchInsights": {
      "stretchDurationAvg": 240,
      "trendInsight": "..."
    },
    "nightWakingsInsights": {
      "wakingsAvg": 2,
      "trendInsight": "..."
    },
    "nightSleepCycleInsights": {
      "awakePercentageAvg": 5,
      "awakeCumulativeMinutesAvg": 30,
      "lightPercentageAvg": 50,
      "lightCumulativeMinutesAvg": 270,
      "deepPercentageAvg": 33,
      "deepCumulativeMinutesAvg": 180,
      "trendInsight": "..."
    },
    "sevenNight": [
      {
        "summaryDate": "2024-03-15",
        "dayLabelAbbreviated": "Fri",
        "nightDuration": {
          "durationMinutes": 540,
          "previousNightTrend": "UP",
          "weeklyTrend": "STABLE"
        },
        "nightRoutine": {
          "coreSleepOnsetTime": "2024-03-15T20:45:00-07:00",
          "coreSleepWakeUpTime": "2024-03-16T06:10:00-07:00"
        },
        "nightStretch": {
          "stretchStart": "2024-03-15T20:45:00-07:00",
          "stretchEnd": "2024-03-16T02:45:00-07:00",
          "stretchDuration": 360,
          "previousNightTrend": "UP",
          "weeklyTrend": "STABLE"
        },
        "nightWakings": {
          "count": 2,
          "wakeTimes": ["2024-03-16T01:30:00-07:00", "2024-03-16T04:00:00-07:00"],
          "previousNightTrend": "SAME",
          "weeklyTrend": "DOWN"
        },
        "nightSleepCycle": {
          "awakePercentage": 5,
          "awakeCumulativeMinutes": 27,
          "lightPercentage": 50,
          "lightCumulativeMinutes": 270,
          "deepPercentage": 33,
          "deepCumulativeMinutes": 178,
          "previousNightTrend": "STABLE",
          "weeklyTrend": "STABLE"
        }
      }
    ]
  }
}
```

### Sleep State Values

Used in `sleepStateDurationsMinutes` keys and `SleepStateSegment.sleepState`:

| Value | Meaning |
|-------|---------|
| `0`   | Unknown |
| `1`   | Awake   |
| `8`   | Light   |
| `15`  | Deep    |

### Sleep Grade Enum

| Value              | Description                |
|--------------------|----------------------------|
| `DREAMY`           | Excellent sleep            |
| `RESTFUL`          | Good sleep                 |
| `OKAY`             | Average sleep              |
| `RESTLESS`         | Poor sleep                 |
| `IN_PROGRESS`      | Sleep session ongoing      |
| `NOT_ENOUGH_DATA`  | Insufficient data          |
| `NO_BIRTHDATE`     | No birthdate configured    |

### Environment Condition Enum

| Value       | Context                          |
|-------------|----------------------------------|
| `COOL`      | Temperature below range          |
| `WARM`      | Temperature above range          |
| `HUMID`     | Humidity above range             |
| `DRY`       | Humidity below range             |
| `IN_RANGE`  | Within acceptable range          |
| `WHISPER`   | Very quiet                       |
| `QUIET`     | Quiet                            |
| `LOUD`      | Loud                             |
| `NOISY`     | Very loud                        |

### Trending Enum

| Value     |
|-----------|
| `LOW`     |
| `HIGH`    |
| `AVERAGE` |

### Temperature Unit Enum

| Value | JSON |
|-------|------|
| Celsius    | `c` |
| Fahrenheit | `f` |

---

## Sleep Window API

**Base URL:** `https://accounts{env}.owletdata.com/`

### Get Sleep Window

```
GET v2/accounts/{accountId}/profiles/{profileId}/sleep-window
```

**Response:** `ApiSleepWindow`

```json
{
  "name": "accounts/abc123/profiles/prof456/sleep-window",
  "startTime": "19:00",
  "endTime": "07:00"
}
```

---

## Video Clips API

**Base URL:** `https://accounts{env}.owletdata.com/`

### List Clips

```
GET v2/accounts/{accountId}/profiles/{profileId}/clips
```

| Parameter   | In    | Type       | Required | Description          |
|-------------|-------|------------|----------|----------------------|
| `accountId` | path  | string     | yes      |                      |
| `profileId` | path  | string     | yes      |                      |
| `startDate` | query | LocalDate  | yes      | ISO date (YYYY-MM-DD)|
| `endDate`   | query | LocalDate  | yes      | ISO date (YYYY-MM-DD)|
| `timeZone`  | query | string     | yes      | IANA timezone        |

**Response:** `ApiVideoClipsListResponse`

```json
{
  "clips": [
    {
      "name": "accounts/abc123/clips/clip001",
      "startTime": "2024-03-15T20:30:00Z",
      "endTime": "2024-03-15T20:31:00Z",
      "expireTime": "2024-04-14T20:31:00Z",
      "kinesisVideoStream": "stream-name",
      "profile": "accounts/abc123/profiles/prof456",
      "service": "accounts/abc123/services/svc789",
      "isPremium": false,
      "event": {
        "name": "accounts/abc123/events/evt001",
        "createTime": "2024-03-15T20:30:00Z",
        "deviceType": "DEVICE_TYPE_CAMERA2",
        "startTime": "2024-03-15T20:30:00Z",
        "eventType": "SERVICE_CAMERA_MOTION",
        "profile": "accounts/abc123/profiles/prof456",
        "profileType": "PROFILE_TYPE_CHILD",
        "service": "accounts/abc123/services/svc789",
        "serviceType": "SERVICE_TYPE_CAMERA"
      }
    }
  ]
}
```

### Batch Delete Clips

```
POST v2/accounts/{accountId}/clips:batchDelete
```

**Request Body:** `ApiDeleteVideoClipsRequest`

```json
{
  "clips": [
    "accounts/abc123/clips/clip001",
    "accounts/abc123/clips/clip002"
  ]
}
```

**Response:** `204 No Content`

---

## Tips API

**Base URL:** `https://accounts{env}.owletdata.com/`

### Get Tips

```
GET v2/tips
```

| Parameter   | In    | Type | Required | Description              |
|-------------|-------|------|----------|--------------------------|
| `ageDays`   | query | int  | yes      | Baby's age in days       |
| `totalSize` | query | int  | yes      | Number of tips to return |

**Response:** `ApiListTipsResponse`

```json
{
  "tips": [
    {
      "name": "tips/tip001",
      "body": "At this age, your baby...",
      "tipCategory": "TIP_CATEGORY_SLEEP"
    }
  ]
}
```

### Tip Category Enum

`TIP_CATEGORY_BIRTHDAY`, `TIP_CATEGORY_BOTTLE`, `TIP_CATEGORY_DIAPER`, `TIP_CATEGORY_DOCTOR`, `TIP_CATEGORY_FOOT`, `TIP_CATEGORY_HAND`, `TIP_CATEGORY_HAPPY`, `TIP_CATEGORY_HEAD`, `TIP_CATEGORY_HEARING`, `TIP_CATEGORY_LEARNING_BLOCKS`, `TIP_CATEGORY_MAD`, `TIP_CATEGORY_MIND`, `TIP_CATEGORY_MUSIC`, `TIP_CATEGORY_OWLET`, `TIP_CATEGORY_SAD`, `TIP_CATEGORY_SIGHT`, `TIP_CATEGORY_SLEEP`, `TIP_CATEGORY_SPOON`, `TIP_CATEGORY_TEETH`, `TIP_CATEGORY_VOICE`, `TIP_CATEGORY_UNKNOWN`

---

## Device Capabilities API

**Base URL:** `https://devices-public{env}.owletdata.com/`

### List Devices

```
GET v2/accounts/{accountId}/devices
```

**Response:** `ApiDeviceCapabilitiesListResponse`

```json
{
  "devices": [
    {
      "deviceType": "DEVICE_TYPE_SMARTSOCK3_SLEEP",
      "name": "AC000W012345678",
      "healthNotificationsCapable": true,
      "conversion": {
        "status": "CONVERTED"
      },
      "owletConnect": {
        "status": "ENABLED",
        "targetedSiteId": "site123",
        "targetedPatientId": "patient456",
        "profileId": "prof789"
      }
    }
  ]
}
```

### Get Device Information

```
GET /v2/dsns/{dsn}/information
```

| Parameter | In   | Type   | Required |
|-----------|------|--------|----------|
| `dsn`     | path | string | yes      |

**Response:** `ApiDeviceCapabilities`

### Check OTA Update

```
POST /v2/dsns/{dsn}:otaCheck
```

| Parameter | In   | Type   | Required |
|-----------|------|--------|----------|
| `dsn`     | path | string | yes      |

**Request Body:** `ApiCheckDeviceOtaRequest` (empty object `{}`)

**Response:** `204 No Content`

### Update Device Information

```
PATCH /v2/dsns/{dsn}/information
```

| Parameter | In   | Type   | Required |
|-----------|------|--------|----------|
| `dsn`     | path | string | yes      |

**Request Body:** `Connect`

```json
{
  "owletConnect": {
    "status": "ENABLED",
    "targetedSiteId": "site123",
    "targetedPatientId": "patient456",
    "profileId": "prof789"
  }
}
```

**Response:** `Connect`

### Device Conversion Status Enum

| Value               |
|---------------------|
| `UNKNOWN`           |
| `PENDING`           |
| `PROCESSING`        |
| `CONVERTED`         |
| `RETRIABLE_ERROR`   |
| `NON_RETRIABLE_ERROR`|

### Owlet Connect Status Enum

| Value      |
|------------|
| `ENABLED`  |
| `DISABLED` |

---

## Device Registration API

**Base URL:** `https://app-device-registration{env}.owletdata.com/`

### Register Device

```
POST sock/{dsn}
```

| Parameter | In   | Type   | Required |
|-----------|------|--------|----------|
| `dsn`     | path | string | yes      |

**Request Body:** `ApiDeviceRegistrationRequest`

```json
{
  "env": "field"
}
```

The `env` field maps to Ayla environment: `dev`, `field`, or `eu`.

**Response:** `ApiDeviceRegistrationResponse`

```json
{
  "device": {
    "dsn": "AC000W012345678",
    "deviceType": "DEVICE_TYPE_SMARTSOCK3_SLEEP"
  }
}
```

### Remove Device

```
DELETE {deviceType}/{dsn}
```

Called via the raw HTTP client (not Retrofit). Removes a device registration.

---

## Push Notifications API

**Base URL:** `https://trigger-wrapper{env}.owletdata.com/`

### Add Sock Push Notification

```
POST notifications/{dsn}/triggers/
```

**Headers:**
```http
Authorization: <firebase_token>
```

**Request Body:**

```json
{
  "push_token": "<fcm_token>",
  "device_nickname": "<device_name>",
  "suid": "<service_user_id>",
  "account_key": "<account_key>",
  "env": "<ayla_env>",
  "push_type": "gcm",
  "nick_name": "<device_name>",
  "token_type": "firebase"
}
```

### Remove Push Notification (Logout)

```
POST notifications/{dsn}/trigger_apps/
```

**Headers:**
```http
Authorization: <firebase_token>
```

Removes push notification registration on logout.

---

## Notification Preferences API

**Base URL:** `https://accounts{env}.owletdata.com/`

### Set Client ID

```
PATCH v1/clients/{clientID}
```

Registers or updates the notification client.

### Get Notification Preferences

```
GET v1/accounts/{accountId}/services/{serviceId}/clients/{clientId}
```

### Set Notification Preferences

```
PATCH v1/accounts/{accountId}/services/{serviceId}/clients/{clientId}
```

---

## User Mapper API

**Base URL:** `https://user-mapper{env}.owletdata.com/`

### Map Device to User

```
POST suid/{serviceUserKey}
```

**Request Body:**

```json
{
  "dsn": "AC000W012345678"
}
```

Used during smart sock migration to associate an Ayla device (by DSN) with the Owlet user account.

---

## Ayla SSO API

**Base URL:** `https://ayla-sso{env}.owletdata.com/`

### Minify Token

```
POST mini/
```

Used to exchange/minify a Firebase token for use with Ayla Networks services. The minified token is then used to authenticate with the Ayla SDK.

---

## Ayla Networks Integration

The Owlet Dream Sock communicates through Ayla Networks IoT platform. The app uses the Ayla SDK to interact with the sock device directly.

### Ayla Service URLs

URLs follow pattern: `https://{service}-{env}-1a2039d9.aylanetworks.com/`

| Service     | Prefix         | Purpose                |
|-------------|----------------|------------------------|
| User        | `user`         | User management        |
| Log         | `log`          | Logging                |
| Metrics     | `metric`       | Metrics collection     |
| Device (ADS)| `ads`          | Ayla Device Service    |
| Datastream  | `mstream`      | Real-time data stream  |
| MDSS        | `mdss`         | Mobile DSS             |
| Rules       | `rulesservice`  | Device rules/alerts   |

### Ayla Environments

| Region  | Environment | URL Infix     |
|---------|-------------|---------------|
| USA     | Production  | `field`       |
| USA     | Development | `dev`         |
| Europe  | Production  | `field-eu`    |

**Example:** `https://user-field-1a2039d9.aylanetworks.com/` (USA Production)

---

## Firebase Realtime Database

The app connects to `https://owletcare-prod.firebaseio.com` for real-time device state and account data. This is used alongside the REST APIs to receive live updates about device status.

---

## AWS Kinesis Video Streams

Video clips from the Owlet Cam are stored and streamed via AWS Kinesis Video Streams. The `kinesisVideoStream` field in clip responses identifies the stream name. The app uses the AWS Kinesis Video SDK to play back clips.

---

## Network Security

- Cleartext traffic is permitted only for `192.168.0.1` (direct Base Station/camera local connection)
- All other traffic uses HTTPS
- Debug builds allow system and user certificate authorities

---

## Error Handling

The HTTP client handles these status codes with retry/special behavior:

| Status Code | Handling                           |
|-------------|-------------------------------------|
| 401         | Re-authenticate (refresh token)    |
| 408         | Timeout - retry with backoff       |
| 422         | Validation error                   |
| 429         | Rate limited - retry with backoff  |
| 5xx         | Server error - retry with backoff  |

Retry configuration: up to 7 retries, 90-second overall timeout.
