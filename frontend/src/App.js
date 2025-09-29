import React, { useState, useMemo } from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AppBar, Toolbar, Typography, Box, IconButton, Link, Tooltip } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import URLChipForm from './components/URLChipForm';
import { lightTheme, darkTheme } from './theme';

function App() {
  const [darkMode, setDarkMode] = useState(false);

  const theme = useMemo(() => {
    return darkMode ? darkTheme : lightTheme;
  }, [darkMode]);

  const handleThemeChange = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        {/* Top Bar */}
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              S⁴D: Style and Structure Similarity for Site Domains
            </Typography>
            <Tooltip title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}>
              <IconButton color="inherit" onClick={handleThemeChange}>
                {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
              </IconButton>
            </Tooltip>
            <Link href="https://github.com/pfavvatas/lib_url_to_img" target="_blank" rel="noopener" color="inherit">
              <Tooltip title="View on GitHub">
                <IconButton color="inherit">
                  <GitHubIcon />
                </IconButton>
              </Tooltip>
            </Link>
          </Toolbar>
        </AppBar>

        {/* Main Content (Component) */}
        <Box sx={{ p: 2 }}>
          <URLChipForm darkMode={darkMode} onThemeChange={handleThemeChange} />
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default App;