FROM docker.io/sitespeedio/browsertime:14.8.0
USER root

RUN apt-get update && apt-get install -y \
  iputils-ping \
  dnsutils \
  nano \
  libnss3-tools

RUN [ -d ~/.pki/nssdb ] || mkdir -p ~/.pki/nssdb

RUN mkdir /opt/comsyschrome
COPY chromium/src/out/Default/chrome /opt/comsyschrome/chrome

RUN chown -R root:root /opt/comsyschrome

COPY certificates/RootCA.crt /root/ca.crt

RUN certutil -d sql:/root/.pki/nssdb -A -n 'example ca' -i /root/ca.crt -t TCP,TCP,TCP

COPY chromeDevtoolsProtocol.js /usr/src/app/lib/chrome/chromeDevtoolsProtocol.js
COPY har.js /usr/src/app/lib/chrome/har.js

ENV BROWSERTIME_DOCKER=true BT_THREADS=4

ENTRYPOINT ["/usr/bin/env"]
CMD ["bash"]
