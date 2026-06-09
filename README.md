# delaylama
proxy http requests, cache it and configure a response delay, so it can simulate a network lag.

# what you gonna need

* Java SDK 25+
* maven 3.9.4+
* docker and docker compose
* (optional) graalvm-ce

# how to use

Pay atention to `docker-entrypoint.sh` inside the example app.
It must run at `docker compose up` stage to copy cert file inside java jre app container.

Inside `docker-compose.yaml` file there is a `CACHED_DELAY_MS` variable. This environment variable controls how much time each cached http request should wait to give a response.

# how to clear all docker compose cache and do a fresh restart

```bash
docker compose down --remove-orphans -v
docker compose build --no-cache
docker compose up --build
```

# how to test

After starting successfuly this project with docker compose, you can try this:

```bash
curl -X GET http://localhost:8080/v1/cep/01430000|jq
```

it will call the java app controller `/v1/cep` in a `GET` http method and give a response. The first uncached response should be faster.
All next calls should wait 5 seconds to answer.

# test your app with just the delay-lama proxy

you can start your application in the host machine with this:

```bash
HTTP_PROXY=http://localhost:3128 \
HTTPS_PROXY=http://localhost:3128 \
./target/cep \
        -Dhttp.proxyHost=localhost \
        -Dhttp.proxyPort=3128 \
        -Dhttps.proxyHost=localhost \
        -Dhttps.proxyPort=3128 \
        -Djavax.net.ssl.trustStore=/tmp/cacerts \
        -Djavax.net.ssl.trustStorePassword=changeit 
```

and call the endpoint forcing the proxy:

```bash
curl -k -x http://localhost:3128 \
  https://brasilapi.com.br/api/cep/v1/01430000|jq
```