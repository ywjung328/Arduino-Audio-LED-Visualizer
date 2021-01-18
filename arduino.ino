#include <FastLED.h>

#define LED_PIN     8
#define LED_NUM     56
#define BRIGHTNESS  255

#define LED_TYPE    WS2812B
#define COLOR_ORDER RGB

#define PERIOD      100
#define HUE_DAMPER  8
#define VAL_DAMPER  8
#define VAL_MIN     63

CRGB leds[LED_NUM];
static float pulseSpeed = 0.5;

uint8_t hueA = 15;  // Start hue at valueMin.
uint8_t satA = 63;  // Start saturation at valueMin.
float valueMin = 0.0;  // Pulse minimum value (Should be less then valueMax).

uint8_t hueB = 95;  // End hue at valueMax.
uint8_t satB = 127;  // End saturation at valueMax.
float valueMax = 255.0;  // Pulse maximum value (Should be larger then valueMin).

uint8_t _hue = hueA;  // Do Not Edit
uint8_t _sat = satA;  // Do Not Edit
float _val = valueMin;  // Do Not Edit
uint8_t hueDelta = hueA - hueB;  // Do Not Edit
static float delta = (valueMax - valueMin) / 2.35040238;  // Do Not Edit

unsigned long start_time = 0;
bool trigger = false;

// boolean val_rise = true;

int brt = 0;
int hue = 0;
int val = 0;

void setup() {
  // put your setup code here, to run once:
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.addLeds<LED_TYPE, LED_PIN, COLOR_ORDER>(leds, LED_NUM).setCorrection(TypicalLEDStrip);
  
  fill_solid(leds, LED_NUM, CRGB(255, 255, 255));

  hue = 0;

  FastLED.show();
  
  Serial.begin(9600);
  Serial.setTimeout(100);
  // delay(3000);
}

void loop() {
  if (Serial.available() > 0) {
    trigger = false;
    val = Serial.parseInt();
    hue = (hue + 1) % (256 * HUE_DAMPER);

    fill_solid(leds, LED_NUM, CHSV((int)(hue / HUE_DAMPER), 127, val));
  } else {
    if (trigger == false) {
      start_time = millis();
      trigger = true;
    } else {
      float dV = ((exp(sin(pulseSpeed * (millis() - start_time) / 2000.0* PI)) - 0.36787944) * delta);
      _val = valueMin + dV;
      _hue = map(_val, valueMin, valueMax, hueA, hueB);  // Map hue based on current val
      _sat = map(_val, valueMin, valueMax, satA, satB);  // Map sat based on current val
    
      for (int i = 0; i < LED_NUM; i++) {
        leds[i] = CHSV(_hue, _sat, _val);
    
        // You can experiment with commenting out these dim8_video lines
        // to get a different sort of look.
        leds[i].r = dim8_video(leds[i].r);
        leds[i].g = dim8_video(leds[i].g);
        leds[i].b = dim8_video(leds[i].b);
      }

      // Serial.println(_val);
    }
  }

  FastLED.show();
}
