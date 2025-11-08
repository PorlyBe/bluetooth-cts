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
    jq

# Install Python dependencies for Home Assistant API timezone support
RUN apk add --no-cache py3-requests
RUN pip3 install --break-system-packages pytz

# Copy application files
COPY run.sh /
COPY bluetooth_cts_server.py /

# Make run script executable
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
