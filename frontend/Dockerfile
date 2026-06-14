# Build stage
# B1/B2: Node 18 EOL → 22 (maintenance LTS). Digest from clean CI Unblock generation
# (sha256:9385cd9f3001dfc3431e8ead12c43e9e1f87cc1b9b5c6cfd0f73865d405b27c4).
# Confirm fresh digest at implementation time. CI matrix already updated (20.x/22.x).
FROM node:22-alpine@sha256:9385cd9f3001dfc3431e8ead12c43e9e1f87cc1b9b5c6cfd0f73865d405b27c4 AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (reproducible via lockfile from CI Unblock A3)
RUN npm ci

# Copy source code
COPY . .

# Build the React app
RUN npm run build

# Runtime stage
# B2: Using nginx:stable-alpine for better predictability. Pull and pin exact current-stable
# digest (e.g. nginx:stable-alpine@sha256:...) at implementation time alongside node digest above.
FROM nginx:stable-alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Patch main nginx config for non-root operation
RUN sed -i 's/user  nginx;/#user  nginx;/' /etc/nginx/nginx.conf && \
    sed -i 's|pid        /run/nginx.pid;|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf

# Copy built React app from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create nginx non-root user
RUN addgroup -g 101 -S nginx 2>/dev/null || true && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx 2>/dev/null || true

# Fix permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chmod -R 755 /usr/share/nginx/html

# Use non-root user
USER nginx

# Expose port
EXPOSE 3000

# Health check
# B4: Use explicit /health (defined in nginx.conf, lightweight, consistent with compose
# and the verified probe). Standalone runs and compose both benefit.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
