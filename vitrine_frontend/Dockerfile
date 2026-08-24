# syntax=docker/dockerfile:1
#
# Build multi-stage do frontend Vitrine (React + Vite), servido por nginx.
#
# Por padrão, VITE_API_URL=/api e o nginx faz proxy para o container do
# backend (same-origin, sem CORS) — ver nginx.conf. Para hospedar o
# frontend separado do backend (ex: Vercel + backend em outro host),
# sobrescreva VITE_API_URL no build com a URL absoluta do backend.

FROM node:22-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
