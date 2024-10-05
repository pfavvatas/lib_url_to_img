import React, { useState, useEffect } from 'react';
import { Box, TextField, Chip, FormControl, Button, useTheme, Alert, CircularProgress } from '@mui/material';

const URLChipForm = () => {
    const [urls, setUrls] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [warning, setWarning] = useState("");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [formAtTop, setFormAtTop] = useState(false);
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
        console.log("Pasted text:", pastedText); // Debugging line
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
        console.log("Input received:", input); // Debugging line
        const newUrls = input.split(/\s+/).filter(url => url.trim().length > 0);
        console.log("Parsed URLs:", newUrls); // Debugging line
        const validUrls = newUrls.filter(url => isValidUrl(url));
        const invalidUrls = newUrls.filter(url => !isValidUrl(url));
        console.log("Valid URLs:", validUrls); // Debugging line
        console.log("Invalid URLs:", invalidUrls); // Debugging line

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
        setFormAtTop(true);
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
            setResult(data);
        } catch (error) {
            console.error("Error:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setUrls([]);
        setResult(null);
        setFormAtTop(false);
    };

    useEffect(() => {
        if (warning) {
            const timer = setTimeout(() => {
                setWarning('');
            }, 2000);
            return () => clearTimeout(timer);
        }
    }, [warning]);

    return (
        <Box
            sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                minHeight: '100vh',
                flexDirection: 'column',
                paddingTop: theme.spacing(4),
                width: '100%',
                paddingLeft: theme.spacing(2),
                paddingRight: theme.spacing(2),
                overflowX: 'hidden',
                boxSizing: 'border-box'
            }}
        >
            <Box
                sx={{
                    width: '100%',
                    maxWidth: '600px',
                    margin: '0 auto',
                    transition: 'all 0.5s ease',
                    position: formAtTop ? 'fixed' : 'relative',
                    top: formAtTop ? theme.spacing(2) : 'auto',
                    left: formAtTop ? '50%' : 'auto',
                    transform: formAtTop ? 'translateX(-50%)' : 'none',
                    zIndex: formAtTop ? 1000 : 'auto',
                    paddingBottom: theme.spacing(2)
                }}
            >
                <FormControl fullWidth>
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
                    {warning && (
                        <Alert severity="error" sx={{ mt: theme.spacing(1) }}>
                            {warning}
                        </Alert>
                    )}
                    <Box
                        sx={{
                            mt: theme.spacing(2),
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: theme.spacing(1),
                            maxHeight: '200px',
                            overflowY: 'auto'
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
            </Box>
            {loading && (
                <Box
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
                </Box>
            )}
            {result && (
                <Box
                    sx={{
                        mt: theme.spacing(2),
                        width: '100%',
                        padding: theme.spacing(2),
                        backgroundColor: '#f5f5f5',
                        borderRadius: '8px',
                        boxShadow: '0 0 10px rgba(0,0,0,0.1)',
                        overflowX: 'auto'
                    }}
                >
                    <pre>{JSON.stringify(result, null, 2)}</pre>
                </Box>
            )}
        </Box>
    );
};

export default URLChipForm;