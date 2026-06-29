#!/bin/bash

set -e

# ============================================================
# EARTHQUAKE WARNING SYSTEM
# INSTALLATION SCRIPT
# ============================================================

PROJECT_ROOT="/opt/earthquake-warning-system"

VENV_PATH="${PROJECT_ROOT}/venv"

LOG_DIRECTORY="/var/log/earthquake"

SERVICE_DIRECTORY="/etc/systemd/system"

SSN_SERVICE="ssn.service"

CRS_SERVICE="crs.service"

echo "=================================================="
echo "Earthquake Warning System Installation"
echo "=================================================="

# ============================================================
# ROOT CHECK
# ============================================================

if [ "$EUID" -ne 0 ]
then
    echo "Run as root"
    exit 1
fi

# ============================================================
# SYSTEM UPDATE
# ============================================================

echo "[1/10] Updating system"

apt-get update

apt-get install -y \
python3 \
python3-pip \
python3-venv \
python3-dev \
build-essential \
git \
curl \
wget \
mosquitto-clients

# ============================================================
# PROJECT DIRECTORY
# ============================================================

echo "[2/10] Creating directories"

mkdir -p "${PROJECT_ROOT}"

mkdir -p "${LOG_DIRECTORY}"

chmod 755 "${LOG_DIRECTORY}"

# ============================================================
# PYTHON VENV
# ============================================================

echo "[3/10] Creating virtual environment"

if [ ! -d "${VENV_PATH}" ]
then
    python3 -m venv "${VENV_PATH}"
fi

source "${VENV_PATH}/bin/activate"

# ============================================================
# REQUIREMENTS
# ============================================================

echo "[4/10] Installing requirements"

pip install --upgrade pip

if [ -f "${PROJECT_ROOT}/requirements.txt" ]
then

    pip install \
        -r "${PROJECT_ROOT}/requirements.txt"

else

    echo "requirements.txt missing"

    exit 1

fi

# ============================================================
# LOG FILES
# ============================================================

echo "[5/10] Creating log files"

touch "${LOG_DIRECTORY}/ssn_stdout.log"
touch "${LOG_DIRECTORY}/ssn_stderr.log"

touch "${LOG_DIRECTORY}/crs_stdout.log"
touch "${LOG_DIRECTORY}/crs_stderr.log"

chmod 644 "${LOG_DIRECTORY}"/*.log

# ============================================================
# SERVICES
# ============================================================

echo "[6/10] Installing services"

if [ -f "./deployment/${SSN_SERVICE}" ]
then

    cp \
        "./deployment/${SSN_SERVICE}" \
        "${SERVICE_DIRECTORY}/${SSN_SERVICE}"

fi

if [ -f "./deployment/${CRS_SERVICE}" ]
then

    cp \
        "./deployment/${CRS_SERVICE}" \
        "${SERVICE_DIRECTORY}/${CRS_SERVICE}"

fi

# ============================================================
# SYSTEMD RELOAD
# ============================================================

echo "[7/10] Reloading systemd"

systemctl daemon-reload

# ============================================================
# ENABLE SERVICES
# ============================================================

echo "[8/10] Enabling services"

if systemctl list-unit-files | grep -q "${SSN_SERVICE}"
then
    systemctl enable "${SSN_SERVICE}"
fi

if systemctl list-unit-files | grep -q "${CRS_SERVICE}"
then
    systemctl enable "${CRS_SERVICE}"
fi

# ============================================================
# PERMISSIONS
# ============================================================

echo "[9/10] Setting permissions"

chmod -R 755 "${PROJECT_ROOT}"

# ============================================================
# STATUS
# ============================================================

echo "[10/10] Installation completed"

echo ""
echo "=========================================="
echo "Installed Successfully"
echo "=========================================="
echo ""
echo "Start SSN:"
echo "sudo systemctl start ssn.service"
echo ""
echo "Start CRS:"
echo "sudo systemctl start crs.service"
echo ""
echo "Check Status:"
echo "sudo systemctl status ssn.service"
echo "sudo systemctl status crs.service"
echo ""
echo "View Logs:"
echo "journalctl -u ssn.service -f"
echo "journalctl -u crs.service -f"
echo ""
echo "=========================================="