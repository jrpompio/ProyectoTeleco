
echo "==> Deteniendo bluetooth.service"
sudo systemctl restart bluetooth

echo "==> Ejecutando servidor BLE GATT"
sudo python3 server_ble.py
