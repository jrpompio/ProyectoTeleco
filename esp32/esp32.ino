#include <WiFi.h>
#include "BLEDevice.h"

#define SERVICE_UUID   "12345678-1234-1234-1234-1234567890ab"
#define CHAR_AUTH_UUID "abcd1234-5678-90ab-cdef-1234567890ab"
#define CHAR_SSID_UUID "abcd1234-5678-90ab-cdef-1234567890ac"
#define CHAR_PASS_UUID "abcd1234-5678-90ab-cdef-1234567890ad"

const char* expectedDeviceName = "ServidorWiFi-BLE";
const char* token = "hacking";

static BLEClient* pClient = nullptr;
static BLERemoteCharacteristic *pAuth = nullptr;
static BLERemoteCharacteristic *pSsid = nullptr;
static BLERemoteCharacteristic *pPass = nullptr;

enum Estado {
  INICIO, INICIAR_WIFI_BLE, ESCANEAR_BLE, ESPERAR_CONEXION_BLE, AUTENTICAR,
  LEER_CREDENCIALES, DESCONECTAR_BLE, CONECTAR_WIFI, CAPTURAR_IP, FIN
};

Estado estadoActual = INICIO;

bool   bleConectado = false;
String ssid, password;
BLEAdvertisedDevice dispositivoObjetivo;

bool connectToServer(BLEAddress addr)
{
  pClient = BLEDevice::createClient();
  if (!pClient->connect(addr)) return false;

  auto* svc = pClient->getService(BLEUUID(SERVICE_UUID));
  if (!svc) return false;

  pAuth = svc->getCharacteristic(BLEUUID(CHAR_AUTH_UUID));
  pSsid = svc->getCharacteristic(BLEUUID(CHAR_SSID_UUID));
  pPass = svc->getCharacteristic(BLEUUID(CHAR_PASS_UUID));

  return (pAuth && pSsid && pPass);
}

void disconnectBLE()
{
  if (pClient && pClient->isConnected()) pClient->disconnect();
  pAuth = pSsid = pPass = nullptr; pClient = nullptr; bleConectado = false;
}

void setup()
{
  Serial.begin(115200); while (!Serial);
  BLEDevice::init("");
  WiFi.mode(WIFI_STA);
}

void loop()
{
  switch (estadoActual) {

    case INICIO:
      Serial.println("ESTADO: INICIO");
      estadoActual = INICIAR_WIFI_BLE;
      delay(1000);
      break;

    case INICIAR_WIFI_BLE:
      Serial.println("ESTADO: INICIAR_WIFI_BLE");
      estadoActual = ESCANEAR_BLE;
      delay(1000);
      break;

    case ESCANEAR_BLE: {
      Serial.println("ESTADO: ESCANEAR_BLE");
      BLEScan* scan = BLEDevice::getScan();
      scan->setActiveScan(true);
      BLEScanResults* res = scan->start(3, false);
      bool found = false;

      for (int i = 0; i < res->getCount(); ++i) {
        BLEAdvertisedDevice d = res->getDevice(i);
        if (d.haveName() && d.getName() == expectedDeviceName) {
          dispositivoObjetivo = d;
          found = true; break;
        }
      }

      scan->clearResults();
      scan->stop();
      estadoActual = found ? ESPERAR_CONEXION_BLE : ESCANEAR_BLE;
      break;
    }

    case ESPERAR_CONEXION_BLE:
      Serial.println("ESTADO: ESPERAR_CONEXION_BLE");
      bleConectado = connectToServer(dispositivoObjetivo.getAddress());
      if (!bleConectado) Serial.println("RESULTADO: FAIL");
      estadoActual = bleConectado ? AUTENTICAR : ESCANEAR_BLE;
      break;

    case AUTENTICAR: {
      Serial.println("ESTADO: AUTENTICAR");
      if (!pAuth || !pAuth->canWrite()) {
        Serial.println("RESULTADO: FAIL");
        estadoActual = DESCONECTAR_BLE; break;
      }
      pAuth->writeValue((uint8_t*)token, strlen(token), true);
      estadoActual = LEER_CREDENCIALES;
      break;
    }

    case LEER_CREDENCIALES:
      Serial.println("ESTADO: LEER_CREDENCIALES");
      if (!pSsid || !pPass) {
        Serial.println("RESULTADO: FAIL");
        estadoActual = DESCONECTAR_BLE; break;
      }
      ssid = pSsid->readValue();
      password = pPass->readValue();

      if (ssid.length() == 0 || password.length() == 0) {
        Serial.println("RESULTADO: FAIL");
        estadoActual = ESCANEAR_BLE;
      } else {
        Serial.println("RESULTADO: OK");
        estadoActual = DESCONECTAR_BLE;
        delay(100);
      }
      break;

    case DESCONECTAR_BLE:
      Serial.println("ESTADO: DESCONECTAR_BLE");
      disconnectBLE();
      estadoActual = CONECTAR_WIFI;
      delay(100);
      break;

    case CONECTAR_WIFI:
      Serial.println("ESTADO: CONECTAR_WIFI");
      if (ssid.isEmpty()) {
        Serial.println("RESULTADO: FAIL");
        estadoActual = ESCANEAR_BLE; break;
      }
      WiFi.begin(ssid.c_str(), password.c_str());
      for (int i = 0; WiFi.status() != WL_CONNECTED && i < 20; ++i)
        delay(500);
      estadoActual = (WiFi.status() == WL_CONNECTED) ?
                      CAPTURAR_IP : CONECTAR_WIFI;
      delay(100);
      break;

    case CAPTURAR_IP:
      Serial.println("ESTADO: CAPTURAR_IP");
      Serial.print("IP: ");
      Serial.println(WiFi.localIP());
      estadoActual = FIN;
      delay(1000);
      break;

    case FIN:
      Serial.println("ESTADO: FIN");
      while (true) delay(1000);
      break;
  }
}
