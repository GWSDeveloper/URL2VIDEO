# Use Node.js as the base imag
FROM node:18-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg python3 python3-pip

# Install yt-dlp using pip
RUN pip3 install yt-dlp

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and install Node.js dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application files
COPY . .

# Expose the app's port
EXPOSE 9999

# Start the server
CMD ["node", "server.js"]

node_modules
downloads
npm-debug.log
