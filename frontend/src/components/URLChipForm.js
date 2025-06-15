import React, { useState, useEffect } from 'react';
import { Box, TextField, Chip, FormControl, Button, useTheme, Snackbar, CircularProgress, Grid2 as Grid, TextareaAutosize, Accordion, AccordionSummary, AccordionDetails, Typography, IconButton, Tooltip, Switch, FormControlLabel } from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

const URLChipForm = ({ darkMode, onThemeChange }) => {
    const [urls, setUrls] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [warning, setWarning] = useState("");
    const [success, setSuccess] = useState(""); // State for success message
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [filePaths, setFilePaths] = useState(null);
    const [error, setError] = useState(null); // State for error message and stack trace
    const [selectedLevels, setSelectedLevels] = useState([]); // State for selected levels
    const [currentView, setCurrentView] = useState('home'); // State for current view
    const [clusterInput, setClusterInput] = useState(""); // State for cluster input
    const [showResults, setShowResults] = useState(false); // Add this new state
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
        // const newUrls = input.split(/\s+/).filter(url => url.trim().length > 0);
				const newUrls = input.match(/"[^"]+"|\S+/g).map(url => url.replace(/(^"|"$)/g, ''));
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

    const handleLevelSelect = (level) => {
        if (selectedLevels.includes(level)) {
            setSelectedLevels(selectedLevels.filter(l => l !== level));
        } else {
            setSelectedLevels([...selectedLevels, level]);
        }
    };

    const handleRun = async () => {
        if (selectedLevels.length === 0) {
            setWarning("You must select at least one level.");
            return;
        }

        setLoading(true);
        setError(null); // Clear previous error
        try {
            const response = await fetch("http://localhost:5000/process-urls", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ urls, levels: selectedLevels })
            });
            const data = await response.json();
            console.log("API Response:", data); // Debug log

            if (data.status === "success") {
                // Display success notification
                setSuccess(data.message);
                console.log("Setting result:", data); // Debug log
                setResult(data); // Store the entire response data

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
                // Set error state
                setError({ message: data.message, stack: data?.stack_trace });
            }

        } catch (error) {
            console.error("Error:", error);
            setError({ message: error.message, stack: error.stack });
        } finally {
            setLoading(false);
        }
    };

    const handleClusterRun = async () => {
        setLoading(true);
        setError(null); // Clear previous error
        try {
            // Serialize the data
            const serializedData = JSON.stringify({ clusters: clusterInput });

            const response = await fetch("http://localhost:5000/process-clusters", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: serializedData
            });
            const data = await response.json();

            if (data.status === "success") {
                setSuccess(data.message);
                const parsedData = JSON.parse(data.body);
                setResult(parsedData);
                const filePaths = parsedData
                    .filter(item => item.startsWith("File created:"))
                    .map(item => item.replace("File created: ", ""))
                    .map(filePath => filePath.split('/').pop()); // Extract the last part of each path
                setFilePaths(filePaths);
            } else if (data.status === "error") {
                setError({ message: data.message, stack: data?.stack_trace });
            }

        } catch (error) {
            console.error("Error:", error);
            setError({ message: error.message, stack: error.stack });
        } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setUrls([]);
        setResult(null);
        setFilePaths(null);
        setError(null); // Clear error when clearing
    };

    const handleCopyToClipboard = (text) => {
        navigator.clipboard.writeText(text);
        setSuccess('Copied to clipboard!');
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

    const renderResults = () => {
        console.log("Current result state:", result);
        if (!result) return null;

        return (
            <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1200px', mx: 'auto' }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                    Clustering Results
                </Typography>
                
                {/* Clustering Results Section */}
                {result.clustering_results && result.clustering_results.map((clusterResult, index) => (
                    <Accordion 
                        key={`cluster-result-${index}`} 
                        sx={{ 
                            mb: theme.spacing(2),
                            '&:before': {
                                display: 'none',
                            },
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            borderRadius: '8px !important',
                            overflow: 'hidden'
                        }}
                    >
                        <AccordionSummary 
                            expandIcon={<ExpandMoreIcon />}
                            sx={{
                                backgroundColor: 'primary.light',
                                '&:hover': {
                                    backgroundColor: 'primary.main',
                                    color: 'white',
                                },
                                '& .MuiAccordionSummary-expandIconWrapper': {
                                    color: 'inherit'
                                }
                            }}
                        >
                            <Typography sx={{ fontWeight: 'bold' }}>
                                Level {clusterResult.level} - {clusterResult.message}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ p: 3 }}>
                            <Box sx={{ mb: theme.spacing(2) }}>
                                <Typography variant="h6" gutterBottom>Cluster Info</Typography>
                                <Box sx={{ 
                                    p: 3, 
                                    bgcolor: 'background.paper', 
                                    borderRadius: 2,
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: 2
                                }}>
                                    <Box sx={{ 
                                        display: 'grid',
                                        gridTemplateColumns: '200px 1fr',
                                        gap: 2,
                                        alignItems: 'center'
                                    }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                            Number of Clusters:
                                        </Typography>
                                        <Typography variant="subtitle1">
                                            {clusterResult.cluster_info.num_clusters}
                                        </Typography>

                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                            DBCV Score:
                                        </Typography>
                                        <Typography variant="subtitle1">
                                            {clusterResult.cluster_info.dbcv_score.toFixed(3)}
                                        </Typography>

                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                            Min Cluster Size:
                                        </Typography>
                                        <Typography variant="subtitle1">
                                            {clusterResult.cluster_info.min_cluster_size}
                                        </Typography>

                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                            Epsilon:
                                        </Typography>
                                        <Typography variant="subtitle1">
                                            {clusterResult.cluster_info.cluster_selection_epsilon}
                                        </Typography>
                                    </Box>

                                    <Box sx={{ 
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: 1,
                                        mt: 1
                                    }}>
                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                            Useful Attributes:
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                            {clusterResult.cluster_info.useful_attributes.map((attr, i) => (
                                                <Chip 
                                                    key={i} 
                                                    label={attr} 
                                                    size="small"
                                                    sx={{ 
                                                        bgcolor: 'primary.light',
                                                        color: 'primary.contrastText',
                                                        '&:hover': {
                                                            bgcolor: 'primary.main'
                                                        }
                                                    }}
                                                />
                                            ))}
                                        </Box>
                                    </Box>
                                </Box>
                            </Box>

                            <Box sx={{ mb: theme.spacing(2) }}>
                                <Typography variant="h6" gutterBottom>Clusters</Typography>
                                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                                    <TextareaAutosize
                                        minRows={2}
                                        maxRows={4}
                                        style={{ 
                                            width: '60%', 
                                            padding: '10px',
                                            fontFamily: 'monospace',
                                            borderRadius: '4px',
                                            border: '1px solid #ccc',
                                            resize: 'vertical',
                                            overflow: 'auto'
                                        }}
                                        value={JSON.stringify(clusterResult.clusters, null, 2)}
                                        readOnly
                                    />
                                </Box>
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                    <Tooltip title="Copy to clipboard">
                                        <IconButton 
                                            size="small" 
                                            onClick={() => handleCopyToClipboard(JSON.stringify(clusterResult.clusters, null, 2))}
                                        >
                                            <ContentCopyIcon />
                                        </IconButton>
                                    </Tooltip>
                                </Box>
                            </Box>
                        </AccordionDetails>
                    </Accordion>
                ))}

                {/* Processed Clusters Section */}
                {result.processed_clusters && result.processed_clusters.map((processedCluster, index) => (
                    <Accordion 
                        key={`processed-cluster-${index}`} 
                        sx={{ 
                            mb: theme.spacing(2),
                            '&:before': {
                                display: 'none',
                            },
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            borderRadius: '8px !important',
                            overflow: 'hidden'
                        }}
                    >
                        <AccordionSummary 
                            expandIcon={<ExpandMoreIcon />}
                            sx={{
                                backgroundColor: 'secondary.light',
                                '&:hover': {
                                    backgroundColor: 'secondary.main',
                                    color: 'white',
                                },
                                '& .MuiAccordionSummary-expandIconWrapper': {
                                    color: 'inherit'
                                }
                            }}
                        >
                            <Typography sx={{ fontWeight: 'bold' }}>
                                Processed Cluster Level {processedCluster.level}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ p: 3 }}>
                            <Box sx={{ mb: theme.spacing(2) }}>
                                <Typography variant="h6" gutterBottom>Processed Data</Typography>
                                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                                    <TextareaAutosize
                                        minRows={2}
                                        maxRows={4}
                                        style={{ 
                                            width: '60%', 
                                            padding: '10px',
                                            fontFamily: 'monospace',
                                            borderRadius: '4px',
                                            border: '1px solid #ccc',
                                            resize: 'vertical',
                                            overflow: 'auto'
                                        }}
                                        value={processedCluster.processed_data.data}
                                        readOnly
                                    />
                                </Box>
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                    <Tooltip title="Copy to clipboard">
                                        <IconButton 
                                            size="small" 
                                            onClick={() => handleCopyToClipboard(processedCluster.processed_data.data)}
                                        >
                                            <ContentCopyIcon />
                                        </IconButton>
                                    </Tooltip>
                                </Box>
                            </Box>

                            <Box sx={{ mb: theme.spacing(2) }}>
                                <Typography variant="h6" gutterBottom>Sites</Typography>
                                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                                    <TextareaAutosize
                                        minRows={2}
                                        maxRows={4}
                                        style={{ 
                                            width: '60%', 
                                            padding: '10px',
                                            fontFamily: 'monospace',
                                            borderRadius: '4px',
                                            border: '1px solid #ccc',
                                            resize: 'vertical',
                                            overflow: 'auto'
                                        }}
                                        value={JSON.stringify(processedCluster.processed_data.sites, null, 2)}
                                        readOnly
                                    />
                                </Box>
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                    <Tooltip title="Copy to clipboard">
                                        <IconButton 
                                            size="small" 
                                            onClick={() => handleCopyToClipboard(JSON.stringify(processedCluster.processed_data.sites, null, 2))}
                                        >
                                            <ContentCopyIcon />
                                        </IconButton>
                                    </Tooltip>
                                </Box>
                            </Box>

                            {/* Full Object Data Section */}
                            <Accordion 
                                sx={{ 
                                    '&:before': {
                                        display: 'none',
                                    },
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                    borderRadius: '8px !important',
                                    overflow: 'hidden'
                                }}
                            >
                                <AccordionSummary 
                                    expandIcon={<ExpandMoreIcon />}
                                    sx={{
                                        backgroundColor: 'grey.100',
                                        '&:hover': {
                                            backgroundColor: 'grey.200',
                                        },
                                        '& .MuiAccordionSummary-expandIconWrapper': {
                                            color: 'inherit'
                                        }
                                    }}
                                >
                                    <Typography sx={{ fontWeight: 'medium' }}>
                                        Full Object Data
                                    </Typography>
                                </AccordionSummary>
                                <AccordionDetails sx={{ p: 2 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                        <Typography variant="h6">Data</Typography>
                                        <Tooltip title="Copy to clipboard">
                                            <IconButton 
                                                size="small" 
                                                onClick={() => handleCopyToClipboard(JSON.stringify(processedCluster.processed_data, null, 2))}
                                            >
                                                <ContentCopyIcon />
                                            </IconButton>
                                        </Tooltip>
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                                        <TextareaAutosize
                                            minRows={2}
                                            maxRows={4}
                                            style={{ 
                                                width: '60%', 
                                                padding: '10px',
                                                fontFamily: 'monospace',
                                                borderRadius: '4px',
                                                border: '1px solid #ccc',
                                                resize: 'vertical',
                                                overflow: 'auto'
                                            }}
                                            value={JSON.stringify(processedCluster.processed_data, null, 2)}
                                            readOnly
                                        />
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                        <Tooltip title="Copy to clipboard">
                                            <IconButton 
                                                size="small" 
                                                onClick={() => handleCopyToClipboard(JSON.stringify(processedCluster.processed_data, null, 2))}
                                            >
                                                <ContentCopyIcon />
                                            </IconButton>
                                        </Tooltip>
                                    </Box>
                                </AccordionDetails>
                            </Accordion>
                        </AccordionDetails>
                    </Accordion>
                ))}
            </Box>
        );
    };

    const renderContent = () => {
        switch (currentView) {
            case 'home':
                return (
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
                        <Box sx={{ position: 'relative', margin: '0 30%', mt: theme.spacing(2), display: 'flex', justifyContent: 'center' }}>
                            <Box sx={{ position: 'absolute', top: '-10px', left: '10px', backgroundColor: 'white', padding: '0 5px', fontWeight: 'bold' }}>Levels</Box>
                            <Box sx={{ border: '1px solid', borderColor: 'grey.400', borderRadius: '8px', padding: theme.spacing(2), display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: theme.spacing(1), width: '-webkit-fill-available' }}>
                                {Array.from({ length: 10 }, (_, i) => i + 1).map(level => (
                                    <Chip
                                        key={level}
                                        label={level}
                                        onClick={() => handleLevelSelect(level)}
                                        color={selectedLevels.includes(level) ? 'primary' : 'default'}
                                    />
                                ))}
                            </Box>
                        </Box>
                        <Box
                            sx={{
                                mt: theme.spacing(2),
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: theme.spacing(1),
                                maxHeight: '200px',
                                overflowY: 'auto',
                                justifyContent: 'center'
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
                        {result && (
                            <Box sx={{ mt: 4, width: '100%' }}>
                                {renderResults()}
                            </Box>
                        )}
                    </FormControl>
                );
            case 'clusters':
                return (
                    <Box sx={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
                        <textarea
                            rows={10}
                            placeholder="Paste your cluster results here"
                            style={{ width: '100%', padding: '10px', boxSizing: 'border-box', maxHeight: '300px', overflowY: 'scroll' }}
                            value={clusterInput}
                            onChange={(e) => setClusterInput(e.target.value)}
                        />
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: theme.spacing(2) }}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleClusterRun}
                                sx={{ borderRadius: '20px' }}
                                disabled={clusterInput.trim() === ''}
                            >
                                Run
                            </Button>
                        </Box>
                    </Box>
                );
            case 'view3':
                return <div>View 3 Content</div>;
            default:
                return <div>Home</div>;
        }
    };

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
                boxSizing: 'border-box',
                bgcolor: 'background.default',
                minHeight: '100vh',
                transition: 'background-color 0.3s ease'
            }}
        >
            <Box sx={{ 
                display: 'flex', 
                justifyContent: 'center', 
                width: '100%', 
                maxWidth: '1200px',
                mb: theme.spacing(2)
            }}>
                <Box sx={{ display: 'flex', gap: theme.spacing(2) }}>
                    <Button variant="contained" onClick={() => setCurrentView('home')}>Home</Button>
                    <Button variant="contained" onClick={() => setCurrentView('clusters')}>Clusters</Button>
                    <Button variant="contained" onClick={() => setCurrentView('view3')}>View 3</Button>
                </Box>
            </Box>
            {renderContent()}
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
                    {filePaths && filePaths.map((file, index) => (
                        <Box key={index} sx={{ mt: theme.spacing(2) }}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={() => window.open(`http://localhost:5005/output_html_files/${file}`, '_blank')}
                            >
                                Open {file}
                            </Button>
                        </Box>
                    ))}
                    {/* <pre>{JSON.stringify(result, null, 2)}</pre> */}
                </Grid>
            )}
            {error && (
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
                        overflowX: 'auto',
                        backgroundColor: '#f8d7da',
                        color: '#721c24'
                    }}
                >
                    <h3>Error: {error.message}</h3>
                    <pre>{error.stack}</pre>
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