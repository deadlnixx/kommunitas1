ARG sourceimage=kommunitasorg/kommunitas
ARG sourcetag=develop
FROM ${sourceimage}:${sourcetag}

# Install dependencies
COPY requirements-plot.txt /kommunitas/

RUN pip install -r requirements-plot.txt --user --no-cache-dir
