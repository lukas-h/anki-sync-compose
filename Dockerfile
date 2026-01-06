FROM debian:12.1-slim as builder

RUN apt-get update && apt-get install -y wget zstd xdg-utils

# Download and install Anki 24.06.3 (hardcoded - last version with .tar.zst files)
# NOTE: Version is hardcoded because Anki 25.x no longer provides .tar.zst downloads
RUN wget "https://github.com/ankitects/anki/releases/download/24.06.3/anki-24.06.3-linux-qt6.tar.zst" && \
    zstd -d anki-24.06.3-linux-qt6.tar.zst && \
    tar -xvf anki-24.06.3-linux-qt6.tar && \
    cd anki-24.06.3-linux-qt6 && \
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