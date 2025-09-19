FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 5173

# Start application
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
