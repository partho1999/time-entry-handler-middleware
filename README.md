# WebSocket API Connection Management Service for Shenxing Series Panel Devices

## Architecture Diagram
![demo.png](demo.png)

Explanation:
1. The panel device first connects to the SxDeviceManager service via WebSocket (WS).
2. After the device is connected, it uses the [Get Login Random Number] and [Device Login Request] interfaces from the API documentation for device authentication. Once authenticated, SxDeviceManager retains the connection session with the device via SessionManager.
3. Third-party services can communicate with the corresponding device by calling SxDeviceManager through HTTP interfaces.

## Instructions for Third-Party Platform Calls
> Third-party platforms can call device APIs as described in the device's API documentation. In addition, the following HTTP headers must be set:

1. Add the header [sxdmSn] in the HTTP request to specify which device the API call is targeting.
2. Depending on whether SxDeviceManager requires authentication for third-party HTTP calls (configured via `access.auth.check.type` in `application.properties`):
   2.1 If no authentication is required, no additional fields are needed.
   2.2 If simple token authentication is used, add the HTTP header [sxdmToken] with the value matching `access.auth.check.token` in `application.properties`. Otherwise, the call will fail.
   2.3 [Recommended] Users can implement stricter authentication as needed by extending or modifying the `AccessAuthCheckFilter` class.

## Device Authentication
> Currently, SxDeviceManager uses a simple random number authentication for devices. It is recommended that customers override the `checkClientLogin` method in `SxDeviceServiceImpl` to implement stricter device authentication. [Recommended]

## Django REST Framework Clone

### Setup

1. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Linux/Mac
   ```
2. Install dependencies:
   ```sh
   pip install django djangorestframework
   ```
3. Run migrations:
   ```sh
   python manage.py migrate
   ```
4. Start the server:
   ```sh
   python manage.py runserver
   ```

### API Endpoints

- `GET /openapi/manager/status/` — List all online device statuses
- `GET /openapi/manager/status/<sn>/` — Get status for a specific device by serial number