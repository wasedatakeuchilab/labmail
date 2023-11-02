FROM python:3.12 as builder
WORKDIR /work
COPY . /work
RUN pip install --no-cache-dir .

FROM python:3.12-slim as runner
LABEL org.opencontainers.image.title="Labmail"
LABEL org.opencontainers.image.description="Sends a message with your signature via Gmail"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="Shuhei Nitta(@huisint)"
RUN useradd takeuchilab
COPY --from=builder /usr/local/bin/labmail /usr/local/bin/
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
ENV LABMAIL_GOOGLE_OAUTH_FLOW_BIND "0.0.0.0"
ENV PYTHONUNBUFFERED "1"
ENTRYPOINT ["labmail"]
CMD ["--help"]
