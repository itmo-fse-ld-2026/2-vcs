# =============================================================================
# Custom XeLaTeX Environment for Version Control Systems Lab Documentation
# Base: ghcr.io/mrdvd/xetex-base (Ubuntu-based)
# Purpose: Compiling reports on SVN/Git configuration and conflict resolution
# =============================================================================

FROM ghcr.io/mrdvd/xetex-base:2026

RUN \
  apt-get update && \
  apt-get install -y make fonts-cmu && \
  # fixes error "Local TeX Live (YYYY-1) is older than remote repository (YYYY)"
  curl -sSL http://mirror.ctan.org/systems/texlive/tlnet/update-tlmgr-latest.sh -o update-tlmgr-latest.sh && \
  sh update-tlmgr-latest.sh && rm update-tlmgr-latest.sh && \
  # # # # #
  tlmgr update --self && \
  tlmgr install \
    babel-english \
    babel-russian \
    hyphen-russian \
    hyperref \
    titlesec \
    etoolbox && \
  apt-get clean