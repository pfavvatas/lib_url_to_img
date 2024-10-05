import React, { useState, useEffect } from 'react';
import { Box, TextField, Chip, FormControl, Button, useTheme, Snackbar, CircularProgress, Grid2 as Grid } from '@mui/material';
import MuiAlert from '@mui/material/Alert';

const URLChipForm = () => {
    const [urls, setUrls] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [warning, setWarning] = useState("");
    const [success, setSuccess] = useState(""); // State for success message
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const theme = useTheme();

    const handleInputChange = (e) => {
        setInputValue(e.target.value);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addUrls(inputValue);
        }
    };

    const handlePaste = (e) => {
        e.preventDefault();
        const pastedText = e.clipboardData.getData('text');
        addUrls(pastedText);
    };

    const isValidUrl = (url) => {
        try {
            new URL(url);
            return true;
        } catch (_) {
            return false;
        }
    };

    const addUrls = (input) => {
        const newUrls = input.split(/\s+/).filter(url => url.trim().length > 0);
        const validUrls = newUrls.filter(url => isValidUrl(url));
        const invalidUrls = newUrls.filter(url => !isValidUrl(url));

        if (invalidUrls.length > 0) {
            setWarning(`Invalid URLs: ${invalidUrls.join(', ')}`);
        }

        if (validUrls.length > 0) {
            setUrls([...urls, ...validUrls]);
            setInputValue('');
        }
    };

    const handleDelete = (urlToDelete) => {
        setUrls(urls.filter(url => url !== urlToDelete));
    };

    const handleRun = async () => {
        setLoading(true);
        try {
            const response = await fetch("http://localhost:5000/process-urls", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls })
            });
            const data = await response.json();

            if (data.status === "success") {
                // Display success notification
                setSuccess(data.message);

                // Handle file conversion and download
                if (data.files && data.files.length > 0) {
                    data.files.forEach(file => {
                        const hexString = file.data;
                        const binaryData = new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
                        const blob = new Blob([binaryData], { type: 'application/zip' });
                        // Generate timestamp
                        const timestamp = new Date().toISOString().replace(/[-:.]/g, '').slice(0, 15);
                        const filenameWithTimestamp = `${timestamp}_${file.filename}`;
                        const link = document.createElement('a');
                        link.href = URL.createObjectURL(blob);
                        link.download = filenameWithTimestamp;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                    });
                }
            } else if (data.status === "error") {
                // Display error notification
                alert(`Error: ${data.message}\nStack Trace: ${data.stack}`);
            }

            setResult(data.body);
        } catch (error) {
            console.error("Error:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setUrls([]);
        setResult(null);
    };

    useEffect(() => {
        if (warning) {
            const timer = setTimeout(() => {
                setWarning('');
            }, 3000); // Adjust the duration as needed
            return () => clearTimeout(timer);
        }
    }, [warning]);

    useEffect(() => {
        if (success) {
            const timer = setTimeout(() => {
                setSuccess('');
            }, 3000); // Adjust the duration as needed
            return () => clearTimeout(timer);
        }
    }, [success]);

    return (
        <Grid
            container
            direction="column"
            justifyContent="center"
            alignItems="center"
            spacing={4}
            sx={{
                paddingTop: theme.spacing(4),
                paddingLeft: theme.spacing(2),
                paddingRight: theme.spacing(2),
                boxSizing: 'border-box'
            }}
        >
            <FormControl fullWidth>
                <Box sx={{ margin: '0 30%' }}>
                    <TextField
                        label="Paste your URLs"
                        placeholder="Paste URLs and press Enter"
                        value={inputValue}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        onPaste={handlePaste}
                        fullWidth
                        variant="outlined"
                    />
                </Box>
                <Box
                    sx={{
                        mt: theme.spacing(2),
                        display: 'flex',
                        flexWrap: 'wrap',
                        gap: theme.spacing(1),
                        maxHeight: '200px',
                        overflowY: 'auto',
                        justifyContent: 'center' // Center the URLs
                    }}
                >
                    {urls.map((url, index) => (
                        <Chip
                            key={index}
                            label={url}
                            onDelete={() => handleDelete(url)}
                            color="primary"
                        />
                    ))}
                </Box>
                <Box
                    sx={{
                        mt: theme.spacing(2),
                        display: 'flex',
                        justifyContent: 'center',
                        gap: theme.spacing(2)
                    }}
                >
                    <Button
                        variant="contained"
                        color="primary"
                        onClick={handleRun}
                        sx={{ borderRadius: '20px' }}
                        disabled={urls.length === 0}
                    >
                        Run
                    </Button>
                    <Button
                        variant="contained"
                        color="secondary"
                        onClick={handleClear}
                        sx={{ borderRadius: '20px' }}
                        disabled={urls.length === 0}
                    >
                        Clear
                    </Button>
                </Box>
            </FormControl>
            {loading && (
                <Grid
                    item
                    xs={12}
                    sx={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        minHeight: '100vh',
                        position: 'fixed',
                        top: 0,
                        left: 0,
                        width: '100%',
                        zIndex: 999
                    }}
                >
                    <CircularProgress />
                </Grid>
            )}
            {result && (
                <Grid
                    item
                    xs={12}
                    sm={8}
                    md={6}
                    sx={{
                        mt: theme.spacing(4),
                        width: '100%',
                        padding: theme.spacing(4),
                        borderRadius: '8px',
                        overflowX: 'auto'
                    }}
                >
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                </Grid>
            )}
            <Snackbar
                open={Boolean(warning)}
                autoHideDuration={3000}
                onClose={() => setWarning('')}
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <MuiAlert onClose={() => setWarning('')} severity="error" sx={{ width: '100%' }}>
                    {warning}
                </MuiAlert>
            </Snackbar>
            <Snackbar
                open={Boolean(success)}
                autoHideDuration={3000}
                onClose={() => setSuccess('')}
                anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
            >
                <MuiAlert onClose={() => setSuccess('')} severity="success" sx={{ width: '100%' }}>
                    {success}
                </MuiAlert>
            </Snackbar>
        </Grid>
    );
};

export default URLChipForm;