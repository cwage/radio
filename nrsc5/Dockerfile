FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    git build-essential cmake autoconf libtool \
    libao-dev libfftw3-dev librtlsdr-dev \
    libpulse0 pulseaudio-utils \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/theori-io/nrsc5.git /opt/nrsc5 \
    && cd /opt/nrsc5 \
    && mkdir build && cd build \
    && cmake .. \
    && make -j$(nproc) \
    && make install \
    && ldconfig

ENTRYPOINT ["nrsc5"]
