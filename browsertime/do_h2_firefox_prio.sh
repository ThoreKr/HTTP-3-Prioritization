FIREFOXPATH="/tmp/firefox$(date +%s%N)"
BROWSERTIMEPATH="/browsertime"

podman exec $2-browsertime find $BROWSERTIMEPATH -mindepth 1 -delete
podman exec $2-browsertime mkdir $FIREFOXPATH

podman exec $2-browsertime node /usr/src/app/bin/browsertime.js \
    --resultDir $BROWSERTIMEPATH \
    --xvfb true \
    -b firefox \
    --firefox.acceptInsecureCerts true \
    --firefox.disableBrowsertimeExtension true \
    --video false \
    --visualMetrics false \
    -n 1 \
    --useSameDir true\
    "$1" > /tmp/browsertime-$2/docker.log

podman exec $2-browsertime rm -rf $FIREFOXPATH
