# Use the official nginx image as base
FROM nginx:alpine

# Set working directory
WORKDIR /usr/share/nginx/html

# Copy static files
COPY HTML/ ./         
COPY CSS/ ./CSS      
COPY JS/ ./JS         

# Copy custom nginx config if needed (optional)
# COPY nginx.conf /etc/nginx/nginx.conf

# Create a default env.js file to allow runtime injection
RUN echo "window.env = { BASE_URL: '' };" > ./env.js

# Expose port 80
EXPOSE 80