FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    git build-essential pkg-config \
    librtlsdr-dev libncurses6 libncurses-dev \
    python3 \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/flightaware/dump1090.git /opt/dump1090 \
    && cd /opt/dump1090 \
    && make BLADERF=no HACKRF=no LIMESDR=no SOAPYSDR=no -j$(nproc)

RUN mkdir -p /run/dump1090-fa \
    && ln -s /run/dump1090-fa /opt/dump1090/public_html/data

# Patch the default config with Nashville location
RUN sed -i \
    -e 's/DefaultCenterLat = 45.0/DefaultCenterLat = 36.1811/' \
    -e 's/DefaultCenterLon = 9.0/DefaultCenterLon = -86.7335/' \
    -e 's/DefaultZoomLvl   = 7/DefaultZoomLvl   = 9/' \
    -e 's/SiteShow    = false/SiteShow    = true/' \
    -e 's/SiteLat     = 45.0/SiteLat     = 36.1811/' \
    -e 's/SiteLon     = 9.0/SiteLon     = -86.7335/' \
    -e 's/SiteName    = "My Radar Site"/SiteName    = "East Nashville"/' \
    -e 's/PageName = "PiAware SkyAware"/PageName = "Nashville ADS-B"/' \
    /opt/dump1090/public_html/config.js

WORKDIR /opt/dump1090

EXPOSE 8080

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
