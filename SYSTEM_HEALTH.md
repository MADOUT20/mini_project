# System Health

The health of the system can be monitored using the following endpoint:

## Health Check

- **Endpoint:** `/health`
- **Method:** `GET`
- **Description:** Returns the status of the API and its services.
- **Success Response:**
  - **Code:** `200 OK`
  - **Content:**
    ```json
    {
      "status": "healthy",
      "services": {
        "packet_capture": "operational",
        "threat_detection": "operational",
        "traffic_analysis": "operational"
      },
      "timestamp": "2023-10-27T10:00:00.000Z"
    }
    ```
