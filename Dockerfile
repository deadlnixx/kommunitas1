FROM python:3.9.6-slim-buster as base

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PATH=/home/ftuser/.local/bin:$PATH
ENV FT_APP_ENV="docker"

# Prepare environment
RUN mkdir /kommunitas \
  && apt-get update \
  && apt-get -y install sudo libatlas3-base curl sqlite3 libhdf5-serial-dev  \
  && apt-get clean \
  && useradd -u 1000 -G sudo -U -m ftuser \
  && chown ftuser:ftuser /kommunitas \
  # Allow sudoers
  && echo "ftuser ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

WORKDIR /kommunitas

# Install dependencies
FROM base as python-deps
RUN  apt-get update \
  && apt-get -y install build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc \
  && apt-get clean \
  && pip install --upgrade pip

# Install TA-lib
COPY build_helpers/* /tmp/
RUN cd /tmp && /tmp/install_ta-lib.sh && rm -r /tmp/*ta-lib*
ENV LD_LIBRARY_PATH /usr/local/lib

# Install dependencies
COPY --chown=ftuser:ftuser requirements.txt requirements-hyperopt.txt /kommunitas/
USER ftuser
RUN  pip install --user --no-cache-dir numpy \
  && pip install --user --no-cache-dir -r requirements-hyperopt.txt

# Copy dependencies to runtime-image
FROM base as runtime-image
COPY --from=python-deps /usr/local/lib /usr/local/lib
ENV LD_LIBRARY_PATH /usr/local/lib

COPY --from=python-deps --chown=ftuser:ftuser /home/ftuser/.local /home/ftuser/.local

USER ftuser
# Install and execute
COPY --chown=ftuser:ftuser . /kommunitas/

RUN pip install -e . --user --no-cache-dir --no-build-isolation \
  && mkdir /kommunitas/user_data/ \
  && kommunitas install-ui

ENTRYPOINT ["kommunitas"]
# Default to trade mode
CMD [ "trade" ]
