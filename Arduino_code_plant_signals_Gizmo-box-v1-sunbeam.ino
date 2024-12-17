/* example1_basic.ino

 This example shows basic data retrieval from the SparkFun Indoor Air Quality Sensor - ENS160.

 Written by: 
	Elias Santistevan @ SparkFun Electronics October, 2022

 Product: 
  https://www.sparkfun.com/products/20844
 
 Repository:
	https://github.com/sparkfun/SparkFun_Indoor_Air_Quality_Sensor-ENS160_Arduino_Library

 SparkFun code, firmware, and software is released under the MIT
 License(http://opensource.org/licenses/MIT).

*/
#include <Wire.h>
#include "SparkFun_ENS160.h"
#include <Adafruit_AHTX0.h>
SparkFun_ENS160 myENS; 
Adafruit_AHTX0 aht;   
int ensStatus; 
const int lightSensorPin = A1;
const int soilHumidityPin = A3;
void setup()
{
	Wire.begin();

	Serial.begin(115200);


  // Initialize AHT21 Sensor
  if (!aht.begin()) {
    Serial.println("Could not find AHT21 sensor!");
    while (1) delay(10);
  }
  Serial.println("AHT21 sensor found!");


	if( !myENS.begin() )
	{
		Serial.println("Could not communicate with the ENS160, check wiring.");
		while(1);
	}

  Serial.println("Example 1 Basic Example.");

	// Reset the indoor air quality sensor's settings.
	if( myENS.setOperatingMode(SFE_ENS160_RESET) )
		Serial.println("Ready.");

	delay(100);

	// Device needs to be set to idle to apply any settings.
	// myENS.setOperatingMode(SFE_ENS160_IDLE);

	// Set to standard operation
	// Others include SFE_ENS160_DEEP_SLEEP and SFE_ENS160_IDLE
	myENS.setOperatingMode(SFE_ENS160_STANDARD);

	// There are four values here: 
	// 0 - Operating ok: Standard Operation
	// 1 - Warm-up: occurs for 3 minutes after power-on.
	// 2 - Initial Start-up: Occurs for the first hour of operation.
  //												and only once in sensor's lifetime.
	// 3 - No Valid Output
	ensStatus = myENS.getFlags();
	Serial.print("Gas Sensor Status Flag (0 - Standard, 1 - Warm up, 2 - Initial Start Up): ");
	Serial.println(ensStatus);
	
}

void loop()
{
sensors_event_t humidity, temp;
  aht.getEvent(&humidity, &temp);

  float temperatureC = temp.temperature;
  float humidityRH   = humidity.relative_humidity;

  int lightValue = analogRead(lightSensorPin);
  int lightPercent = map(lightValue, 660, 5, 0, 100);
    int soilHumidityValue = analogRead(soilHumidityPin);
      int soilPercent = map(soilHumidityValue, 660, 400, 0, 100);

	if( myENS.checkDataStatus() )
	{
    Serial.print("Temperature: ");
  Serial.print(temperatureC);
  Serial.print(" °C, Humidity: ");
  Serial.print(humidityRH);

Serial.print(", Light: ");
  Serial.print(lightPercent);
  Serial.print(" %, Soil Humidity: ");
  Serial.print(soilPercent);
  Serial.print(" %");


		Serial.print(", Air Quality Index (1-5) : ");
		Serial.print(myENS.getAQI());

		Serial.print(", Total Volatile Organic Compounds: ");
		Serial.print(myENS.getTVOC());
		Serial.print("ppb");

		Serial.print(", CO2 concentration: ");
		Serial.print(myENS.getECO2());
		Serial.print("ppm");

	Serial.print(", Gas Sensor Status Flag (0 - Standard, 1 - Warm up, 2 - Initial Start Up): ");
    Serial.print(myENS.getFlags());

		Serial.println();


	}

	delay(1000);
}
