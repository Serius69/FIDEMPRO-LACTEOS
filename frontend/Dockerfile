# ─────────────────────────────────────────────
# STAGE 1: Builder — compila el SPA React/Vite
# ─────────────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

COPY . .
# base=/app/ se aplica en build (ver vite.config.ts).
# VITE_BACKEND_URL vacío → enlaces server-rendered relativos (same-origin).
ARG VITE_BACKEND_URL=""
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL
RUN npm run build

# ─────────────────────────────────────────────
# STAGE 2: Runtime — nginx non-root (UID 101)
# OBLIGATORIO: la imagen corre como non-root, por eso usa
# nginx-unprivileged y escucha en 8080 (no puede bind a 80).
# ─────────────────────────────────────────────
FROM nginxinc/nginx-unprivileged:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html/app
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
