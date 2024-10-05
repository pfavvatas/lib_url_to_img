import React from 'react';
import { AppBar, Toolbar, Typography, Box, IconButton, Link } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import URLChipForm from './components/URLChipForm';

function App() {
  return (
    <Box sx={{ flexGrow: 1 }}>
      {/* Top Bar */}
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            lib url to img
          </Typography>
          <Link href="https://github.com/pfavvatas/lib_url_to_img" target="_blank" rel="noopener" color="inherit">
            <IconButton color="inherit">
              <GitHubIcon />
            </IconButton>
          </Link>
        </Toolbar>
      </AppBar>

      {/* Main Content (Component) */}
      <Box sx={{ p: 2 }}>
        <URLChipForm />
      </Box>
    </Box>
  );
}

export default App;