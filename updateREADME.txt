#New way to run the wifi version with the visuals update:

docker compose -f docker-compose-base.yml -f docker-compose-back.yml
-f docker-compose-wifi.yml up -d

--------------------------

For visuals to work make sure the "http://127.0.0.1:5000" is free

--------------------------

