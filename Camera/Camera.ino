#include <WiFi.h>
#include <string.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"

//#define CAMERA_MODEL_AI_THINKER
// Cấu hình chân camera cho AI Thinker
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define CHUNK_SIZE 1024

#define CMD_WIFI  1

char deviceName[20] = "esp32-cam"; 

enum Mode {
    MODE_WIFI_CONFIG,
    MODE_WEBSOCKET_CONFIG,
    MODE_PROCESSING
};

Mode mode = MODE_WIFI_CONFIG;

WebSocketsClient webSocket;

char websocket_host[20] = "192.168.4.1";
const uint16_t websocket_port = 80;
const char* websocket_path = "/ws";

StaticJsonDocument<200> doc;

// Cấu hình FPS và chất lượng - TỐI ƯU CHO 30FPS
const int targetFPS = 10;                  //khung hình/giây
const int jpegQuality = 15;                // Chất lượng JPEG cân bằng (1-63)
const framesize_t frameSize = FRAMESIZE_240X240; // Độ phân giải HQVGA (320x240)
unsigned long lastFrameTime = 0;
bool isStreaming = false;

uint32_t frameDelay;
uint32_t now;

char ssid[50] = "ESP32_Gateway";
char password[50] = "12345678";

bool wifi_flag = true;
bool websocket_initialized = false;
int changing_wifi_time = 0;

// Khai báo
void setupCamera();
void connectToWiFi(const char* ssid, const char* password);
void webSocketEvent(WStype_t type, uint8_t * payload, size_t length);
void readGatewayMessage(char message[]);
void sendImage();

void setup() {
  Serial.begin(115200);
  setupCamera();
  delay(500);
}

void loop() {
  webSocket.loop();  

  switch(mode) {
    case MODE_WIFI_CONFIG:
      if (wifi_flag) {
        delay(1000);
        webSocket.disconnect();
        websocket_initialized = false;

        connectToWiFi(ssid, password);

        wifi_flag = false;
        changing_wifi_time++;
        mode = MODE_WEBSOCKET_CONFIG;
      }
      break;

    case MODE_WEBSOCKET_CONFIG:
      if (!websocket_initialized) {
      //  delay(1000);
        //serial.print(websocket_host);
        //serial.print("  ");
        //serial.print(websocket_port);
        //serial.print("  ");
        //serial.print(websocket_path);
        //serial.println("  ");
        webSocket.begin(websocket_host, websocket_port, websocket_path);
        webSocket.onEvent(webSocketEvent);
        webSocket.setReconnectInterval(2000);
        websocket_initialized = true;

      if (changing_wifi_time == 1)
        mode = MODE_WEBSOCKET_CONFIG;
      else
        mode = MODE_PROCESSING;
      }
      break;

    case MODE_PROCESSING:
      sendImage();
      break;
    default:
      break;
  }
}

void setupCamera(){
  // Khởi tạo camera với cấu hình tối ưu
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 24000000;         // Tần số XCLK 24MHz
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Cấu hình chất lượng ảnh cho FPS cao
  config.frame_size = frameSize;
  config.jpeg_quality = jpegQuality;
  config.fb_count = 2;                     // Tăng buffer lên 3 để hỗ trợ FPS cao

  // Khởi động camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Lỗi khởi động camera: 0x%x", err);
    setupCamera();
    return;
  }
}

void connectToWiFi(const char* ssid, const char* password){
  WiFi.disconnect(true);
  delay(200);
  WiFi.begin(ssid, password);
  //serial.print("Connecting to Wifi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    //serial.print(".");
  }

  //serial.print("\n");
  //serial.print(WiFi.SSID());
  //serial.println(" connected!");
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      //serial.println("[WebSocket] Connected to Gateway.");
      webSocket.sendTXT("{\"device\": \"esp-cam\"}");
      break;

    case WStype_DISCONNECTED:
      //serial.println("[WebSocket] Disconnected to gateway.");
      break;

    case WStype_TEXT:
      //serial.printf("[WebSocket] Got message: %s\n", payload);
      readGatewayMessage((char*)payload);
      break;
      
    default:
      break;
  }
}

void readGatewayMessage(char json[]) {
  ////serial.println(json);
  DeserializationError err = deserializeJson(doc, json);
  if (err) {
    //serial.print("Lỗi JSON: ");
    //serial.println(err.f_str());
    return;
  }

  int cmd = doc["cmd"];
  switch(cmd) {
    case CMD_WIFI:
      strcpy(ssid, doc["ssid"]);
      strcpy(password, doc["password"]);
      strcpy(websocket_host, doc["IP"]);
      //serial.printf("ssid: %s | password: %s\n", ssid, password);

      webSocket.sendTXT("{\"cmd\": 10, \"device\": 0}");
      //serial.printf("Sent cmd: 10, device: 0");

      mode = MODE_WIFI_CONFIG;
      wifi_flag = true;
    //  websocket_initialized = false; // Để kết nối lại WebSocket ở IP mới
      break;
  }
}

void sendImage(){
  // Tính thời gian giữa các frame để đạt target FPS
  frameDelay = 955 / targetFPS;
  now = millis();
  //serial.println("Gửi ảnh tới Gateway...");

  if (now - lastFrameTime >= frameDelay) {
    lastFrameTime = now;

    // Lấy frame từ camera
    camera_fb_t *fb = esp_camera_fb_get();
    if (fb) {
      uint32_t imageSize = fb->len;
      uint8_t *imageData = fb->buf;

      // Gửi 4 byte header chứa kích thước ảnh (big-endian)
      uint8_t header[4];
      header[0] = (imageSize >> 24) & 0xFF;
      header[1] = (imageSize >> 16) & 0xFF;
      header[2] = (imageSize >> 8) & 0xFF;
      header[3] = imageSize & 0xFF;
      webSocket.sendBIN(header, 4);
      delay(1); 

      // Chia nhỏ ảnh thành nhiều gói để gửi dần
      for (uint32_t i = 0; i < imageSize; i += CHUNK_SIZE) {
        uint32_t chunkLen = CHUNK_SIZE < imageSize - i ? CHUNK_SIZE : imageSize - i;
        webSocket.sendBIN(imageData + i, chunkLen);
        delay(10);  
      }

      // Trả lại bộ nhớ ảnh cho hệ thống
      esp_camera_fb_return(fb);
    }
  }
}
