# Server Endpoints

These endpoints provide server status and mode information.

## GET /server/mode

Get current server mode.

**Response:**
```json
{
    "demo_mode": false,
    "mode": "normal"
}
```

**Response Fields:**
- `demo_mode`: Whether demo mode is enabled
- `mode`: Current server mode ("demo" or "normal")

## Notes

- The server mode determines which endpoints are available
- Debug mode enables additional endpoints for testing and debugging
- Production mode restricts access to potentially sensitive endpoints
- This endpoint is always available regardless of server mode

## Error Responses

- `500 Internal Server Error`: Server configuration error

**Error Format:**
```json
{
    "detail": "string"
}
```
