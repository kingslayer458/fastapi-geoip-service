# GeoIP Lookup Microservice using FastAPI

A lightweight FastAPI microservice for resolving IP addresses into GeoIP and ASN data using MaxMind GeoLite2 databases.

## What It Does

- Looks up GeoIP data for a single IP address
- Returns ASN information for an IP address
- Performs bulk GeoIP lookups for a list of IPs
- Parses traceroute output, extracts IPs, and returns GeoIP results
- Serves a health check and a root service description

### Endpoints

- `GET /geoip/{ip}` - full GeoIP lookup
- `GET /geoip/asn/{ip}` - ASN lookup
- `POST /geoip/bulk` - bulk GeoIP lookup from a JSON array of IPs
- `POST /geoip/traceroute` - traceroute text lookup using `text/plain`

## Local Setup

 Install dependencies:

```bash
pip install -r requirements.txt
```

## MaxMind Update Configuration

The `geoipupdate` service uses `maxmind.env`.

Example values:

```env
GEOIPUPDATE_ACCOUNT_ID=your_account_id
GEOIPUPDATE_LICENSE_KEY=your_license_key
GEOIPUPDATE_EDITION_IDS=GeoLite2-Country GeoLite2-City GeoLite2-ASN
GEOIPUPDATE_FREQUENCY=9
```

Copy `maxmind.env.example` to `maxmind.env` and fill in your credentials.

3. Make sure the GeoLite2 databases exist in `geoip_database/`:

- `GeoLite2-City.mmdb`
- `GeoLite2-Country.mmdb`
- `GeoLite2-ASN.mmdb`

If you need to download them first, run this command and it will populate the `geoip_database/` directory with the latest GeoLite2 databases:

```bash
docker compose run --rm geoipupdate-init
```

Note: the GeoLite databases are downloaded from `https://updates.maxmind.com`.

4. Start the app from the `app` directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Docker Setup

You can run the API and the MaxMind updater using Docker Compose.

```bash
docker compose up --build
```

The compose file mounts `geoip_database/` into the containers so the database files are available to the API.


## Example Requests

### Single IP lookup

```bash
curl http://localhost:8000/geoip/8.8.8.8
```

### ASN lookup

```bash
curl http://localhost:8000/geoip/asn/8.8.8.8
```

### Bulk lookup

Send a raw JSON array of IPs:

```bash
curl -X POST http://localhost:8000/geoip/bulk \
  -H "Content-Type: application/json" \
  -d '["8.8.8.8","1.1.1.1","9.9.9.9"]'
```

### Traceroute lookup

Send traceroute output as plain text:

```bash
curl -X POST http://localhost:8000/geoip/traceroute \
  -H "Content-Type: text/plain" \
  --data-binary @traceroute.txt
```

Example traceroute content:

```text
traceroute to example.com
1  192.168.1.1
2  8.8.8.8
3  1.1.1.1
```

firewall outbound rules for maxmind update service:

mm-prod-geoip-databases.a2649acb697e2c09b632799562c076f2.r2.cloudflarestorage.com
status.maxmind.com
updates.maxmind.com