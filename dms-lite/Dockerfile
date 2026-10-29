FROM node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205 AS assets
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY styles ./styles
COPY views ./views
COPY public/new-js ./public/new-js
RUN npm run build:css

FROM node:24.22.1-bookworm-slim@sha256:55fb5f5a527ea2c5c4a95f963e48ef90aa38c7b346054fdc8ee9957a2b55d205
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund
COPY . .
COPY --from=assets /app/public/stylesheets/app.css ./public/stylesheets/app.css
ENV NODE_ENV=production
USER node
EXPOSE 3000
CMD ["node", "bin/www"]
