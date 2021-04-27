![Imgur](https://i.imgur.com/xIHNbkz.png)
 [![Slack](https://img.shields.io/badge/Join-Slack-blue)](https://www.project-owl.com/slack)
 The DMS LITE is the open source version of the cloud DMS. DMS LITE gives you simple network activity and data visuals.

## About
The DMS LITE is a light weight version of the OWL **DMS** that runs in the cloud. The DMS Lite is built to run on a local device if internet connectivity is not available. The DMS (Data Managment System) is build to collect data from the [ClusterDuck Protocol](https://github.com/Call-for-Code/ClusterDuck-Protocol) and provide simple data managment, analytics and network activity. 

## How it Works
There are two different ways to get the data from your ClusterDuck network into the DMS locally: using a USB Serial connection or WiFi. Using the serial connection, the Raspberry Pi or other device reads the incoming messages from the serial monitor by a wired connection from the papaduck and writes the data into the database. Using the Wifi connection the Raspberry pi turns into an acces point. This allows the Papa Ducks to send data over WiFi to a MQTT broker that writes the data into the database.

The PaPa Duck is running a different Firmware than the regular ClusterDuck Protocol PaPa example.

### Example of ClusterDuck Protocol Network

![Imgur](https://i.imgur.com/SMRbAKk.jpg)

### Local ClusterDuck Protocol Network

![Imgur](https://i.imgur.com/B5NbR0k.jpg)

## Pre-requirements:

-   You must install docker for your host operating system. To do this please go to the official install website:  [Install Docker](https://docs.docker.com/get-docker/)
-   You must also install Sqlite on your host machine in order to create the Database file. [Sqlite] ([https://www.sqlite.org/download.html](https://www.sqlite.org/download.html))
-   Goto github and install the CDP Library into your Arduino IDE or Platform IO and  [Flash Duck Device](https://github.com/Call-for-Code/ClusterDuck-Protocol).  _you will need a WiFi or Serial PapiDevice as well as a duck link device_

**Using DMS-Lite Docker**

-   You will notice there is a root folder and then three sub-folders DMS-Lite, Wifi-sql writer, and Serial-sql-writer. DMS-Lite is where your Docker setup for the web portion of dms lite. Wifi-sql-writer is where the python code is hosted for db writing from MQTT. Serial-sql-writer is where the python code is that reads from a plugged in duck device over usb and writes to the database.

**Run DMS Lite Docker Version:**

1.  Download the code to your machine using githubs git commands  `git clone <repo link>`
2.  Navigate to the folder where you stored this code. make sure you are on the root folder you should see the three sub-folders. From the root folder you will see .env.example
3.  We will need to edit the .env.example - In the .env file just tell it where your db (database) file is stored. Once you do that save the file as .env so docker knows to check it.
4.  Now you edited those files it is time to build your docker image. you can do this by running the following command  `docker-compose -f docker-compose-serial.yml or docker-compose-wifi-serial.yml build` this will take a few mins. Once that is done you can go ahead and run dms-lite  _make sure your duck is plugged in via usb if using serialUSB version_. Run it via this command  `docker-compose -f docker-compose-serial.yml or docker-compose-wifi-serial.yml up -d`. This will start DMS-Lite on localhost:3000
5.  Open up your favorite web browser and go to that link and you should see DMS-Lite
6.  If you would like to stop it running at anytime go back to your terminal and run  `docker-compose down`

Trouble Shooting:

-   If you would like to see the logging output of all the containers running then run  `docker-compose -f docker-compose-serial.yml or docker-compose-wifi-serial.yml up`. This will show a bunch of output of the running containers. If you would like to close out the service hit ctrl+c on your machines keyboard.