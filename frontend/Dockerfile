# Build Stage
FROM node:20-slim AS build

WORKDIR /workspace

COPY package.json ./
RUN npm install

COPY . .

# Pass environment variable at build time (or default to empty for runtime fallback)
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# Production Stage
FROM nginx:alpine

COPY --from=build /workspace/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
