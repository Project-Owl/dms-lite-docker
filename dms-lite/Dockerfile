FROM node:lts-alpine

COPY . .

# Installs the DMS Lite packages
RUN npm install

#port in which App is running at Localhost:3000
EXPOSE 3000

# ENTRYPOINT [ "node", "app.js" ]
ENTRYPOINT ["npm", "start"]
