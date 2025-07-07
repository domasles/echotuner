# Server Endpoints

These endpoints provide server status and mode information.

## GET /server/mode

Get current server mode.

**Response:**
```json
{
    "demo_mode": false,
    "mode": "normal",
}
```

**Response Fields:**
- `mode`: Current server mode ("debug" or "production")
- `debug_enabled`: Whether debug mode is active
- `version`: API version
- `features`: Object describing enabled features

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
    "detail": "string",
    "error": "string"
}
```
