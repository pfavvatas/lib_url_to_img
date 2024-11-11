const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();

// Serve static files from the "output_html_files" directory
const outputDir = path.join(__dirname, '../api/output_html_files');
app.use('/output_html_files', express.static(outputDir));

app.listen(5005, () => {
  console.log('Server is running on port 5005');

  // Read the files in the output_html_files directory
  fs.readdir(outputDir, (err, files) => {
    if (err) {
      return console.error('Unable to scan directory:', err);
    }
    // Print the files and their URLs
    files.forEach(file => {
      console.log(`File: ${file}`);
      console.log(`URL: http://localhost:5005/output_html_files/${file}`);
    });
  });
});