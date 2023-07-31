![Imgur](https://i.imgur.com/XLb61lc.png)

[![Slack](https://img.shields.io/badge/Join-Slack-blue?logo=slack&style=flat-square)](https://www.project-owl.com/slack)  ![GitHub](https://img.shields.io/github/license/project-owl/dms-lite-docker?style=flat-square) ![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/project-owl/dms-lite-docker?logo=github&style=flat-square)


![Imgur](https://i.imgur.com/3zInWHg.jpg)


## About
DMS LITE is a lightweight version of the OWL **DMS** that runs in the cloud. The DMS Lite is built to run on a local device if internet connectivity is not available. The DMS (Data Managment System) is built to collect data from the [ClusterDuck Protocol](https://github.com/Call-for-Code/ClusterDuck-Protocol) and provide simple data management, analytics, and network activity.

## How it Works
There are two different ways to get the data from your ClusterDuck network into the DMS locally: using a USB Serial connection or WiFi.

- **Serial Connection (Currently only for Raspberry Pi):** Using the serial connection, the Raspberry Pi or other device reads the incoming messages from the serial monitor by a wired connection from the [modifed PapaDuck](https://github.com/Call-for-Code/ClusterDuck-Protocol/tree/master/examples/6.PaPi-DMS-Lite-Examples/Serial-PaPiDuckExample) and writes the data into the database.
- **WiFi Connection** If you use the WiFi option your [modified PapaDuck](https://github.com/Call-for-Code/ClusterDuck-Protocol/tree/master/examples/6.PaPi-DMS-Lite-Examples/PapiDuckExample-wifi) will publish all its data to an MQTT broker that runs on your local device.

The PapaDucks are running [a different firmware](https://github.com/Call-for-Code/ClusterDuck-Protocol/tree/master/examples/6.PaPi-DMS-Lite-Examples) than the regular ClusterDuck Protocol PapaDuck example.


![Imgur](https://i.imgur.com/B5NbR0k.jpg)

## Prerequisites:

-  **Docker** Download and install Docker for your operating system. To do this please go to the official installation page: [Install Docker](https://docs.docker.com/get-docker/).

- **Docker Compose** We use Docker Compose to handle building and running each container in this solution together, so you
will need to install Docker Compose for your operating system.

-  **ClusterDuck Protocol** Install the CDP Library onto your computer by following these instructions:  [CDP installation](https://github.com/Call-for-Code/ClusterDuck-Protocol/wiki/getting-started). _you will need a WiFi or Serial PapaDuck as well as a DuckLink device to test the DMS Lite._

- **RaspAp - Only for Local Raspberry Pi Solution** If you don't have a local network to connect your WiFi PapaDuck to you can turn your Raspberry Pi into an access point by installing [RaspAp](https://raspap.com/#quick). *Note: Install RaspAp after successfully installing the Docker image if your Pi uses a WiFi connection*

## Images
In the root folder, there are three subfolders that each contain code to build a Docker image:

 1. **dms-lite** Contains the web application/front end.
 2. **wifi-sql-writer** Writes your incoming data from MQTT into the database
 3. **serial-sql-writer** If a serial-usb connection is used this image will write incoming serial data to the database.

## Install

1. Download the source code onto your local machine
 `git clone https://github.com/Project-Owl/dms-lite-docker.git`

2. Navigate to the `dms-lite-docker` folder you just copied. There, you should see the three sub-folders.

3. Setup environment variable file
- Make a copy of the file named `.env.example` and save it as `.env`.
- Modify the new `.env` and enter the information for the `MYSQL` variables. These can be any values you would like as they are applied to the MariaDB instance. These variables are copied to all of the container images. For the two `PASSWORD` fields, make sure these values are at least 6 characters in length. For the `MYSQL_HOST` variable, you will input `mariadb`. This matches the name of the container for the Maria database defined in `docker-compose-base.yml`.

4. If you are planning to run the `serial` version, you will also need to modify `docker-compose-serial.yml` with the correct USB mapping:

   * For a Linux-based host, the mapping should be `"/dev/ttyUSB0:/dev/ttyUSB0"`
   * For a macOS-based host, the mapping should be `"/dev/cu.usbserialXXXXX:/dev/ttyUSB0"`. It is possible the macOS host will assign a unique identifier to the port. You can verify from a Terminal window by running `ls /dev/cu*` to identify the correct port.
   * For a Windows-based host, the mapping should be `"class/86E0D1E0-8089-11D0-9CE4-08003E301F73:/dev/ttyUSB0"`. This is for USB devices that show up as a COM port in the Windows devices list. For the list of class GUIDs, please refer to [this](https://docs.microsoft.com/en-us/virtualization/windowscontainers/deploy-containers/hardware-devices-in-containers?WT.mc_id=IoT-MVP-5002324) documentation.


5. Run and build the Docker Images
   - **Serial Connection** run the following command
 `docker compose -f docker-compose-base.yml -f docker-compose-serial.yml up -d`
 *Note: Your [Serial-Papa](https://github.com/Call-for-Code/ClusterDuck-Protocol/tree/master/examples/6.PaPi-DMS-Lite-Examples/Serial-PaPiDuckExample) needs to be connected to a USB port to build successfully*

    - **WiFi Connection** run the following command
 `docker compose -f docker-compose-base.yml -f docker-compose-wifi.yml up -d`
 *Note: Follow these instructions to connect to your [WiFi-PapaDuck](https://github.com/Call-for-Code/ClusterDuck-Protocol/tree/master/examples/6.PaPi-DMS-Lite-Examples/PapiDuckExample-wifi) to your local MQTT Broker*

6. After you successfully installed and started your Docker images, you can see the DMS Lite by going to `localhost:3000` inside of a browser.

7. If you would like to stop running your services:
   - Run `docker compose -f docker-compose-base.yml -f docker-compose-serial.yml down` for the Serial version
   - Run `docker compose -f docker-compose-base.yml -f docker-compose-wifi.yml down` for the Wifi version


## Setup your network

### Setup Serial PapaDuck
Setup you [Serial PapaDuck](https://github.com/Call-for-Code/ClusterDuck-Protocol/blob/master/examples/6.PaPi-DMS-Lite-Examples/Serial-PaPiDuckExample/Serial-PaPiDuckExample.ino) by downloading the source code and flashing your development board. After you have successfully setup your Duck, connect it to your Local machine by USB cable.

### Setup WiFi PapaDuck
If you are using the WiFi-PapaDuck.ino to connect to your local network you need to enter the IP address of your local MQTT network **(the machine Docker is running on and not the IP of the container)** and your WiFi Network name and Password to the [Papa's .ino file](https://github.com/Call-for-Code/ClusterDuck-Protocol/blob/master/examples/6.PaPi-DMS-Lite-Examples/PapiDuckExample-wifi/PapiDuckExample-wifi.ino). If you are using a raspberry Pi and RaspAp and want a fully offline solution you can use the default .ino file credentials.

```c
const char* user = "raspi-webgui"; // change to your home WiFi SSID if not using RaspAp
const char* pass = "ChangeMe"; // change to your home WiFi password if not using RaspAp
const char* mqtt_server = "10.3.141.1"; // change to local IP if not using RaspAp
```

## Troubleshooting

### Container logs
If you would like to see the logging output of a particular container, and you are running in detached mode (the `-d` flag above),
first run the `docker container ls` command to get the list of all running containers. Under the `NAMES` column, copy the name of the container
you want to view and then run `docker logs <containername>`. This will output the most recent log information.

### Failed to execute script
If you get this error `Failed to execute script docker-compose`, make sure Docker is running.

### Local container image cleanup
If you are running into errors and need to clean up the existing images to rebuild them, first make sure you are not running any
DMS Lite components by running the appropriate `docker-compose down` script from the steps above. You can also check for any running
images with `docker container ls`.

Next, run `docker images`. This will output all of the container images stored on your system. Identify the name of the image under
REPOSITORY and it's TAG and then run `docker image rm IMAGENAME:TAG`, replacing `IMAGENAME` and `TAG` with the corresponding values.

Rerunning the docker compose step from above will rebuild the image again from scratch.


## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our Code of Conduct, and the process for submitting DMS-Lite improvements. You can reach out directly on our [Slack Workspace](https://www.project-owl.com/slack) for any questions and work with the community.


## License

This project is licensed under the Apache 2 License - see the [LICENSE](LICENSE) file for details.

## Version
v1.0.0


