FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    git build-essential cmake pkg-config \
    librtlsdr-dev libpulse-dev rtl-sdr \
    multimon-ng \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["sh", "-c", "rtl_fm -f ${FREQ:-164.98M} -M fm -s 22050 -g ${GAIN:-40} -p ${PPM:-0} - | multimon-ng -t raw -a POCSAG512 -a POCSAG1200 -a POCSAG2400 -f alpha -"]
