FROM ubuntu:18.04

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# ===== SYSTEM DEPENDENCIES =====
# Menambahkan fontconfig agar wkhtmltopdf 0.12.5 terinstall lancar
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    fontconfig \
 && curl -sL https://deb.nodesource.com/setup_14.x | bash - \
 && apt-get update && apt-get install -y \
    python2.7 \
    python-pip \
    python-dev \
    build-essential \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    libjpeg-dev \
    libpq-dev \
    zlib1g-dev \
    libffi-dev \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    xfonts-base \
    xfonts-75dpi \
    xfonts-utils \
    nodejs \
 && rm -rf /var/lib/apt/lists/*

# ===== FIX pip (Python 2) =====
RUN python -m pip install --upgrade "pip<21" "setuptools<45" "wheel<0.35"

# ===== LESS =====
RUN npm install -g less less-plugin-clean-css

# ===== WORKDIR =====
WORKDIR /opt/odoo

# ===== COPY SOURCE =====
COPY odoo /opt/odoo/odoo
COPY emm /opt/odoo/emm
COPY Setup /opt/odoo/Setup
COPY requirements.txt /opt/odoo/

# ===== PYTHON DEPENDENCIES (ODOO 7) =====
RUN pip install --no-cache-dir \
    psycopg2==2.7.4 \
    Babel==2.9.1 \
    decorator==4.4.2 \
    docutils==0.18.1 \
    feedparser==5.2.1 \
    Jinja2==2.10.3 \
    lxml==4.6.5 \
    MarkupSafe==1.1.1 \
    passlib==1.7.4 \
    Pillow==6.2.2 \
    psutil==5.9.8 \
    python-dateutil==2.8.2 \
    python-openid==2.2.5 \
    pytz==2023.3.post1 \
    PyYAML==5.3.1 \
    reportlab==3.5.59 \
    simplejson==3.19.2 \
    unittest2==1.1.0 \
    mock==3.0.5 \
    Mako==1.1.6 \
    Werkzeug==0.16.1

# ===== wkhtmltopdf =====
# Menggunakan 0.12.5 (Versi resmi terakhir untuk Ubuntu 18.04/Bionic)
# Jika nanti PDF Header/Footer terpotong, baru kita coba trik downgrade ke 0.12.1.
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.bionic_amd64.deb \
 && dpkg -i wkhtmltox_0.12.5-1.bionic_amd64.deb \
 && apt-get -f install -y \
 && rm wkhtmltox_0.12.5-1.bionic_amd64.deb

# ===== aeroolib =====
RUN cd /tmp \
 && git clone https://github.com/aeroo/aeroolib.git \
 && cd aeroolib \
 && git checkout py2.x \
 && python setup.py install \
 && rm -rf /tmp/aeroolib

# ===== PyChart =====
RUN cd /tmp \
 && wget https://fossies.org/linux/privat/old/PyChart-1.39.tar.gz \
 && tar -xzf PyChart-1.39.tar.gz \
 && cd PyChart-1.39 \
 && python setup.py install \
 && rm -rf /tmp/PyChart-1.39*

EXPOSE 9000 8071

CMD ["python", "/opt/odoo/odoo/openerp-server", \
     "--config=/opt/odoo/Setup/odoo_prod.conf", \
     "--addons-path=/opt/odoo/odoo/addons,/opt/odoo/emm", \
     "--load=web"]