#  Proyecto BLE-WiFi ESP32

Este repositorio implementa un sistema de conexión ESP32 ↔ Servidor BLE para autenticación y provisión de credenciales Wi-Fi. Incluye una interfaz gráfica en Python que muestra los estados del flujo en tiempo real.

---

##  Estructura de archivos

```
.
├── esp32/
│   └── esp32.ino          # Código Arduino para ESP32 (cliente BLE)
├── server_ble.py          # Servidor BLE GATT con validación de token
├── interfaz.py            # Interfaz gráfica PyQt que muestra estados
├── run_server.bash        # Script para reiniciar Bluetooth y lanzar servidor
```

---

##  Descripción de cada archivo

* \`\`
  Programa para el ESP32: escanea dispositivos BLE, se conecta, envía el token de autenticación y recibe SSID y contraseña para conectarse a Wi-Fi.

* \`\`
  Servidor BLE en Python (BlueZ + D-Bus). Publica servicio GATT, valida el token recibido y permite leer SSID/PASS solo si la autenticación es correcta.

* \`\`
  Interfaz gráfica hecha con PyQt5. Lee mensajes del ESP32 (`ESTADO:`, `RESULTADO:`, `IP:`) y muestra cada estado como bloques tipo diagrama de flujo, resaltando el bloque activo.

* \`\`
  Script Bash para reiniciar `bluetooth.service` y lanzar el servidor BLE con permisos de superusuario.

---

##  Requisitos

* ESP32 con soporte BLE.
* Linux con BlueZ >= 5.50.
* Dependencias Python: `pydbus`, `PyQt5` o `PySide2`, `pyserial`.

---

##  Ejecución rápida

```bash
# 1) Reiniciar Bluetooth y lanzar servidor BLE
bash run_server.bash

# 2) Subir esp32.ino al ESP32 y abrir monitor serial

# 3) Ejecutar interfaz gráfica
python3 interfaz.py
```

---

