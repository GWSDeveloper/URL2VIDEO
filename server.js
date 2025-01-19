const express = require('express');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

const app = express();
const PORT = 9999;

// Middleware to handle JSON
app.use(express.json());
app.use(express.static('index.html'); // Serve the downloads folder

// Endpoint to download video
app.post('/download/video', (req, res) => {
  const url = req.body.url;

  if (!url) {
    return res.status(400).send({ error: 'URL is required' });
  }

  const name = url.slice(17,26)
  
  const outputFile = path.join(__dirname, 'downloads', `${name}.mp4`);

  // Command to download the video
  const command = `yt-dlp -o "${outputFile}" -f 18 "${url}"`;

  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error.message}`);
      return res.status(500).send({ error: 'Failed to download video' });
    }
    console.log(stdout);

    // Serve the downloaded file
    res.download(outputFile, `${name}.mp4`, () => {
      // Delete file after download
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

  const name = url.slice(17,26)
  const outputFile = path.join(__dirname, 'downloads', `${name}.mp3`);

  // Command to download audio only
  const command = `yt-dlp -o "${outputFile}" --extract-audio --audio-format mp3 "${url}"`;

  exec(command, (error, stdout, stderr) => {
    if (error) {
      console.error(`Error: ${error.message}`);
      return res.status(500).send({ error: 'Failed to download audio' });
    }
    console.log(stdout);

    // Serve the downloaded file
    res.download(outputFile, `${name}.mp3`, () => {
      // Delete file after download
      fs.unlinkSync(outputFile);
    });
  });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
