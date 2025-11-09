ARG BUILD_FROM
FROM $BUILD_FROM

# Install required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bluez \
    bluez-deprecated \
    dbus \
    py3-gobject3 \
    py3-dbus \
    bash \
    jq \
    py3-requests

# Install Python dependencies
RUN pip3 install --break-system-packages pytz

# Copy application files
COPY bluetooth_cts_server.py /bluetooth_cts_server.py
COPY run.sh /etc/services.d/bluetooth-cts/run
RUN chmod +x /etc/services.d/bluetooth-cts/run