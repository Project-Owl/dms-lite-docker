FROM node@sha256:418e07e94bad2fa2b2f148e1025775e4b249528ddea07d353eb350d7eb108fd1

COPY . .

# Installs the DMS Lite packages
RUN npm install

#port in which App is running at Localhost:3000
EXPOSE 3000

# ENTRYPOINT [ "node", "app.js" ]
ENTRYPOINT ["npm", "start"]
