FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------
# Base system + common development tools
# ---------------------------------------------------------
RUN apt-get update && apt-get install -y \
    build-essential \
    make \
    git \
    cmake \
    ninja-build \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    vim \
    nano \
    gdb \
    pkg-config \
    file \
    rsync \
    sudo \
    ccache \
    # Kernel / U-Boot build dependencies
    bison \
    flex \
    libssl-dev \
    zlib1g-dev \
    libncurses-dev \
    libgmp-dev \
    libmpc-dev \
    libmpfr-dev \
    # Cross compilers
    gcc-arm-linux-gnueabihf \
    g++-arm-linux-gnueabihf \
    # U-Boot tools
    u-boot-tools \
    cpio \
    device-tree-compiler \
    # Clean up
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------
# Create non-root user
# ---------------------------------------------------------
RUN useradd -ms /bin/bash dev && \
    usermod -aG sudo dev && \
    echo "dev ALL=(ALL) NOPASSWD: ALL" >/etc/sudoers.d/dev

# ---------------------------------------------------------
# Workspace for your project
# ---------------------------------------------------------
USER dev
RUN mkdir -p /home/dev/work
WORKDIR /home/dev/work

CMD ["/bin/bash"]
