-using "CamWwebServer" example codes of ESP32S3 Dev Module on arduino IDE.
-replace the code in "CamWebServer.ino" from CamWebServer's file with the given CamWebServer.ino code. Also replace WIFI_NAME and WIFI_PASSWORD with correct info.
-download and keep the yolov3.cfg, yolov3.weights and coco.names in the same directory as detector.py file.

[The stream from the ESP32 cam module is fed to the detector.py file. Where it processes the feed and in case of any sort of rule violation it takes a screenshot of the incident and buzzes an alarm  and lights a red indicator both of which are connected to the ESP32]
