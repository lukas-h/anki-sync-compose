# Anki Sync Server for Coolify

Self-hosted Anki sync server configured for deployment on Coolify.

## Environment Variables

Configure these in the Coolify environment variables tab:

### Required Variables

- `SYNC_USER1` - First sync user credentials in format `username:password` (required)

### Optional Variables

- `SYNC_USER2` - Additional user credentials in format `username:password`
- `SYNC_USER3` - Additional user credentials in format `username:password`
- `SYNC_USER4` - Additional user credentials in format `username:password`
- `SYNC_USER5` - Additional user credentials in format `username:password`
- `SYNC_BASE` - Base path for sync data (default: `/syncserver`)
- `DATA_PATH` - Host path for data storage (default: `./syncserver`)
- `ANKI_VERSION` - Anki version to install (default: `25.09.2`)
- `ANKI_PACKAGE` - Anki package name (default: `anki-25.09.2-linux-qt6`)

## Coolify Deployment

1. Create a new service in Coolify
2. Select "Docker Compose" as the build pack
3. Point to this repository
4. Set the required `SYNC_USER1` environment variable in format `user:password`
5. Add any additional optional environment variables as needed
6. Deploy

Note: Port configuration is handled automatically by Coolify.

## Local Development

### Build image

``` bash
SYNC_USER1=user:pass docker compose build
```

### Run container

``` bash
SYNC_USER1=user:pass docker compose up -d
```

## See also

[Anki Sync Server Documentation](https://docs.ankiweb.net/sync-server.html)
