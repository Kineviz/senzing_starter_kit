ARG BASE_IMAGE=ubuntu
FROM ${BASE_IMAGE} AS runner

ENV REFRESHED_AT=2024-11-01

LABEL Name="kineviz/starter-kit" \
      Maintainer="support@kineviz.com" \
      Version="0.0.1"

# Copy files from repository.

COPY ./kineviz_rootfs /

WORKDIR /app
ENTRYPOINT ["/app/import-networkx.sh"]
