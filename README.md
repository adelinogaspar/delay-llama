![Delay-Llama Logo](docs/delay-llama-logo.png)

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

HTTP_PROXY=http://localhost:3128 HTTPS_PROXY=http://localhost:3128 curl -X GET localhost:8081/v1/cep/05541000
```

# use the proxy with an external app like debuging with intellij

```bash
 ✘ gaspar@mint-inspiron  [c] (base)  3.13.11  ~  docker exec delaylama-cache-proxy ls -la /home/mitmproxy/.mitmproxy
total 32
drwxr-xr-x 2 mitmproxy mitmproxy 4096 Jun 11 20:23 .
drwx------ 1 mitmproxy mitmproxy 4096 May 12 13:10 ..
-rw-r--r-- 1 mitmproxy mitmproxy 1172 Jun 11 20:23 mitmproxy-ca-cert.cer
-rw-r--r-- 1 mitmproxy mitmproxy 1035 Jun 11 20:23 mitmproxy-ca-cert.p12
-rw-r--r-- 1 mitmproxy mitmproxy 1172 Jun 11 20:23 mitmproxy-ca-cert.pem
-rw------- 1 mitmproxy mitmproxy 2383 Jun 11 20:23 mitmproxy-ca.p12
-rw------- 1 mitmproxy mitmproxy 2847 Jun 11 20:23 mitmproxy-ca.pem
-rw-r--r-- 1 mitmproxy mitmproxy  770 Jun 11 20:23 mitmproxy-dhparam.pem
 gaspar@mint-inspiron  [c] (base)  3.13.11  ~  docker cp \
  delaylama-cache-proxy:/home/mitmproxy/.mitmproxy/mitmproxy-ca-cert.pem \
  /tmp/
Successfully copied 1.17kB (transferred 3.07kB) to /tmp/
 gaspar@mint-inspiron  [c] (base)  3.13.11  ~  cp $JAVA_HOME/lib/security/cacerts /tmp/cacerts^C
 ✘ gaspar@mint-inspiron  [c] (base)  3.13.11  ~  keytool -importcert \
  -alias mitmproxy \
  -file /tmp/mitmproxy-ca-cert.pem \
  -keystore /tmp/cacerts \
  -storepass changeit \
  -noprompt
Certificate was added to keystore
 gaspar@mint-inspiron  [c] (base)  3.13.11  ~  keytool -list \
  -keystore /tmp/cacerts \
  -storepass changeit | grep mitmproxy
```

start the app in intellij with

```
        -Dhttp.proxyHost=localhost -Dhttp.proxyPort=3128 -Dhttps.proxyHost=localhost -Dhttps.proxyPort=3128 -Djavax.net.ssl.trustStore=/tmp/cacerts -Djavax.net.ssl.trustStorePassword=changeit -Djavax.net.debug=ssl,handshake
```


# gatling

```bash
docker exec -it gatling \
  ./bin/gatling.sh \
  -s simulations.DelayLlamaSimulationScaleCep1to100Users
```


# create this environment to fix root files

```bash
cat > .env <<EOF
UID=$(id -u)
GID=$(id -g)
EOF
```