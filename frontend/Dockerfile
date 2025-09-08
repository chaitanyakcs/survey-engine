# Multi-stage build for React frontend
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx config
RUN printf 'server {\n    listen 80;\n    server_name _;\n    root /usr/share/nginx/html;\n    index index.html;\n\n    # Handle React Router (SPA)\n    location / {\n        try_files $uri $uri/ /index.html;\n    }\n\n    # API proxy (adjust backend URL as needed)\n    location /api/ {\n        proxy_pass http://backend:8000;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_connect_timeout 120s;\n        proxy_send_timeout 120s;\n        proxy_read_timeout 120s;\n    }\n\n    # WebSocket proxy\n    location /ws/ {\n        proxy_pass http://websocket:8001;\n        proxy_http_version 1.1;\n        proxy_set_header Upgrade $http_upgrade;\n        proxy_set_header Connection "upgrade";\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n        proxy_connect_timeout 120s;\n        proxy_send_timeout 120s;\n        proxy_read_timeout 120s;\n    }\n\n    # Health check endpoint\n    location /health {\n        access_log off;\n        return 200 "healthy\\n";\n        add_header Content-Type text/plain;\n    }\n\n    # Gzip compression\n    gzip on;\n    gzip_vary on;\n    gzip_min_length 1024;\n    gzip_types\n        text/plain\n        text/css\n        text/xml\n        text/javascript\n        application/javascript\n        application/json;\n}\n' > /etc/nginx/conf.d/default.conf

# Copy built application from build stage
COPY --from=build /app/build /usr/share/nginx/html

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]