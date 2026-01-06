FROM debian:12.1-slim as builder

# Anki version - hardcoded to prevent Coolify from overriding with empty values
ARG ANKI_VERSION
ARG ANKI_PACKAGE

RUN apt-get update && apt-get install -y wget zstd xdg-utils

# Download and install Anki 24.06.3 (hardcoded - last version with .tar.zst files)
RUN ANKI_VER="${ANKI_VERSION:-24.06.3}" && \
    ANKI_PKG="${ANKI_PACKAGE:-anki-24.06.3-linux-qt6}" && \
    wget "https://github.com/ankitects/anki/releases/download/${ANKI_VER}/${ANKI_PKG}.tar.zst" && \
    zstd -d ${ANKI_PKG}.tar.zst && \
    tar -xvf ${ANKI_PKG}.tar && \
    cd ${ANKI_PKG} && \
    ./install.sh

FROM debian:12.1-slim

# Set the locale
RUN apt-get update && apt-get install -y locales

RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8 \
LANGUAGE=en_US:en \
LC_ALL=en_US.UTF-8

COPY --from=builder /usr/local/share/anki /usr/local/share/anki

EXPOSE 8080

CMD ["/usr/local/share/anki/anki", "--syncserver"]