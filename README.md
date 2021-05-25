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

-  **Docker** Download and install Docker for your operating system. To do this please go to the official installation page: [Install Docker](https://docs.docker.com/get-docker/)
-  **SQLite** You need to install SQLite on your machine to host the database. Follow the installation for your OS here [SQLite] ([https://www.sqlite.org/download.html](https://www.sqlite.org/download.html))
-  **ClusterDuck Protocol** Install the CDP Library onto your computer by following these instructions:  [CDP installation](https://github.com/Call-for-Code/ClusterDuck-Protocol/wiki/getting-started). _you will need a WiFi or Serial PapaDuck as well as a DuckLink device to test the DMS Lite._
- **RaspAp - Only for Local Raspberry Pi Solution** If you don't have a local network to connect your WiFi PapaDuck to you can turn your Raspberry Pi into an access point by installing [RaspAp](https://raspap.com/#quick). *Note: Install RaspAp after successfully installing the Docker image if your Pi uses a WiFi connection*

## Images 
In the root folder, there are three subfolders that each contain code to build a Docker image:

 1. **Web** Contains the web application/front end.
 2. **WiFi-Data-Writer** Writes your incoming data from MQTT into the database
 3. **Serial-Data-Writer** If a serial-usb connection is used this image will write incoming serial data to the database.
 
## Install

1. Download the source code onto your local machine
 `git clone https://github.com/Project-Owl/dms-lite-docker.git`
 
2. Navigate to the `dms-lite-docker` folder you just copied, you should see the three sub-folders. 

3. Initalize the database
    - Open a terminal and type `sqlite3 data.db` to create a database
    - Next create a table by running 
    `CREATE TABLE IF NOT EXISTS clusterData (timestamp datetime, duck_id TEXT, topic TEXT, message_id TEXT, payload TEXT, path TEXT, hops INT, duck_type INT);`
    - Copy the file path of your data.db file 
    
    Now that your database is set up, we can move on to telling Docker where the database file is located.

4. Setup environment variable file  
- Make a copy of the file named `.env.example` and save it as `.env`.
- Modify the new `.env` file and place the full path of the data.db file you created in the previous step where it says `<your_db_file_location_here>`.
-  *Note only copy the full path; Do not include data.db name*; For example: `home/dev/dmslite/`. 

5. Run and build the Docker Images
- **Serial Connection** run the following command
 `docker-compose -f docker-compose-serial.yml up -d` 
 *Note: Your [Serial-Papa](https://github.com/Call-for-Code/ClusterDuck-Protocol/tree/master/examples/6.PaPi-DMS-Lite-Examples/Serial-PaPiDuckExample) needs to be connected to a USB port to build successfully*
 
 - **WiFi Connection** run the following command
 `docker-compose -f docker-compose-wifi.yml up -d` 
 *Note: Follow these instructions to connect to your [WiFi-PapaDuck](https://github.com/Call-for-Code/ClusterDuck-Protocol/tree/master/examples/6.PaPi-DMS-Lite-Examples/PapiDuckExample-wifi) to your local MQTT Broker*
 
7. After you successfully insalled and started your Docker images, you can see the DMS-Lite by going to `localhost:3000` inside of a browser.
8. If you would like to stop running your services run  `docker-compose down`.


## Setup your network

### Setup Serial PapaDuck
Setup you [Serial PapaDuck](https://github.com/Call-for-Code/ClusterDuck-Protocol/blob/master/examples/6.PaPi-DMS-Lite-Examples/Serial-PaPiDuckExample/Serial-PaPiDuckExample.ino) by downloading the source code and flashing your development board. After you have successfully setup your Duck, connect it to your Local machine by USB cable. 

### Setup WiFi PapaDuck
If you are using the WiFi-PapaDuck to connect to your local network you need to enter the IP address of your local MQTT network to the [Papa's .ino file](https://github.com/Call-for-Code/ClusterDuck-Protocol/blob/master/examples/6.PaPi-DMS-Lite-Examples/PapiDuckExample-wifi/PapiDuckExample-wifi.ino). If you are using a raspberry Pi and RaspAp and want a fully offline solution you can use the default .ino file credentials.

```c
const char* user = "raspi-webgui"; // change to your home WiFi SSID if not using RaspAp
const char* pass = "ChangeMe"; // change to your home WiFi password if not using RaspAp
const char* mqtt_server = "10.3.141.1"; // change to local IP if not using RaspAp
```

If you need to know how to find your Local IP address your MQTT broker inside your Docker container is operating follow these instructions.



## Troubleshooting:

-   If you would like to see the logging output of all the containers running then run `docker-compose -f docker-compose-serial.yml or docker-compose-wifi-serial.yml up`. This will show a bunch of output of the running containers. If you would like to close out the service hit ctrl+c on your machine's keyboard.

- If you get this error `ERROR: Named volume "<PATH_TO_DB>:/db:rw" is used in service "web" but no declaration was found in the volumes section.` make sure your file path is correct in the .env file and make sure data.db is not at the end of your path.

- If you get this error `Failed to execute script docker-compose` make sure your Docker Desktop is open.


## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our Code of Conduct, and the process for submitting DMS-Lite improvements. You can reach out directly on our [Slack Workspace](https://www.project-owl.com/slack) for any questions and work with the community. 


## License

This project is licensed under the Apache 2 License - see the [LICENSE](LICENSE) file for details.

## Version
v 1.0.0


