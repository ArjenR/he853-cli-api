FROM debian:latest as he853build

RUN set -ex; \
    apt update ; \
    apt install -y g++  make pkg-config libudev-dev libusb-1.0-0-dev libhidapi-dev git ;\
    git clone https://github.com/ArjenR/he853-cli.git ;\
    cd he853-cli ; \
    make he853-static

FROM python:slim
COPY --from=he853build /he853-cli/he853-static /usr/local/sbin/
RUN mkdir /workspace
COPY source/main.py source/requirements.txt /workspace/
RUN pip install -r /workspace/requirements.txt
ENTRYPOINT [ "uvicorn", "--host", "0.0.0.0", "--app-dir", "/workspace", "main:app" ]

