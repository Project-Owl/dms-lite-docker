FROM node:16-buster

#RUN apt update && apt install -y node-sqlite3
COPY . .

# Installs the DMS Lite packages
RUN npm install

# Installs the SQLite 3 package for node and uses bindings from the underlying OS to install
RUN npm install sqlite3 --build-from-source --sqlite=/os-sqlite

#port in which App is running at Localhost:3000
EXPOSE 3000

# ENTRYPOINT [ "node", "app.js" ]
ENTRYPOINT ["npm", "start"]
