const express = require('express');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = process.env.PORT || 9999; // Use dynamic port for Render

// Middleware to handle JSON
app.use(express.json());
app.use(express.static('static')); // Serve static files (e.g., index.html)

// Ensure the downloads directory exists
const downloadsDir = path.join(__dirname, 'downloads');
if (!fs.existsSync(downloadsDir)) {
  fs.mkdirSync(downloadsDir);
}

// Endpoint to download video
app.post('/download/video', (req, res) => {
  const url = req.body.url;

  if (!url) {
    return res.status(400).send({ error: 'URL is required' });
  }

  const name = `video_${Date.now()}`; // Generate a unique name for the file
  const outputFile = path.join(downloadsDir, `${name}.mp4`);

  // Command to download the video
  const command = `yt-dlp -o "${outputFile}" -f 18 "${url}"`;

  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error downloading video: ${error.message}`);
      return res.status(500).send({ error: 'Failed to download video' });
    }

    console.log(stdout);

    // Serve the downloaded file
    res.download(outputFile, `${name}.mp4`, (err) => {
      if (err) {
        console.error(`Error serving file: ${err.message}`);
      }
      // Delete file after serving
      fs.unlinkSync(outputFile);
    });
  });
});

// Endpoint to download audio
app.post('/download/audio', (req, res) => {
  const url = req.body.url;

  if (!url) {
    return res.status(400).send({ error: 'URL is required' });
  }

  const name = `audio_${Date.now()}`; // Generate a unique name for the file
  const outputFile = path.join(downloadsDir, `${name}.mp3`);

  // Command to download audio only
  const command = `yt-dlp -o "${outputFile}" --extract-audio --audio-format mp3 "${url}"`;

  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error downloading audio: ${error.message}`);
      return res.status(500).send({ error: 'Failed to download audio' });
    }

    console.log(stdout);

    // Serve the downloaded file
    res.download(outputFile, `${name}.mp3`, (err) => {
      if (err) {
        console.error(`Error serving file: ${err.message}`);
      }
      // Delete file after serving
      fs.unlinkSync(outputFile);
    });
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
