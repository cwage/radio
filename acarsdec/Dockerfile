FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    git build-essential cmake pkg-config \
    librtlsdr-dev libusb-1.0-0-dev \
    libcjson-dev libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/f00b4r0/acarsdec.git /opt/acarsdec \
    && cd /opt/acarsdec \
    && mkdir build && cd build \
    && cmake .. \
    && make -j$(nproc) \
    && make install \
    && ldconfig

ENTRYPOINT ["acarsdec"]
