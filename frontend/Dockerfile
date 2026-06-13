# --- Frontend: build bằng Node, phục vụ static bằng nginx -------------------
FROM node:20-alpine AS build

WORKDIR /app

# Cài deps trước (cache layer).
COPY package.json package-lock.json* ./
RUN npm ci 2>/dev/null || npm install

COPY . .
RUN npm run build

# --- Runtime: nginx tĩnh, proxy /api sang backend --------------------------
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
