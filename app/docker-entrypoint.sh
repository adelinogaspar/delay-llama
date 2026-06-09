#!/bin/sh

set -e

echo "Waiting for mitmproxy cert..."

while [ ! -f /mitm-certs/mitmproxy-ca-cert.pem ]
do
  sleep 1
done

echo "Copying default cacerts..."

cp /opt/java/openjdk/lib/security/cacerts /tmp/cacerts

echo "Importing mitmproxy CA..."

keytool \
  -importcert \
  -trustcacerts \
  -alias mitmproxy \
  -file /mitm-certs/mitmproxy-ca-cert.pem \
  -keystore /tmp/cacerts \
  -storepass changeit \
  -noprompt

echo "Starting Spring Boot..."

exec java $JAVA_TOOL_OPTIONS -jar /app/app.jar