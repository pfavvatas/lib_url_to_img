import React, { useState, useEffect } from 'react';
import { Box, TextField, Chip, FormControl, Button, useTheme, Snackbar, CircularProgress, Grid2 as Grid, TextareaAutosize, Accordion, AccordionSummary, AccordionDetails, Typography, IconButton, Tooltip, Card, CardContent, CardHeader, Switch, FormControlLabel } from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import DeleteIcon from '@mui/icons-material/Delete';

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
    const [isNewMode, setIsNewMode] = useState(false);
    const [abortController, setAbortController] = useState(null);
    const theme = useTheme();

    // Function to extract domain from URL
    const getDomain = (url) => {
        try {
            const urlObj = new URL(url);
            return urlObj.hostname;
        } catch {
            return url;
        }
    };

    // Group URLs by domain
    const groupedUrls = urls.reduce((acc, url) => {
        const domain = getDomain(url);
        if (!acc[domain]) {
            acc[domain] = [];
        }
        acc[domain].push(url);
        return acc;
    }, {});

    // Sort domains alphabetically
    const sortedDomains = Object.keys(groupedUrls).sort();

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
        setError(null);
        
        // Create new AbortController for this request
        const controller = new AbortController();
        setAbortController(controller);

        try {
            const response = await fetch("http://localhost:5000/process-urls", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    urls, 
                    levels: selectedLevels,
                    mode: isNewMode ? 1 : 0
                }),
                signal: controller.signal
            });
            const data = await response.json();
            console.log("API Response:", data);

            if (data.status === "success") {
                setSuccess(data.message);
                console.log("Setting result:", data);
                setResult(data);

                if (data.files && data.files.length > 0) {
                    data.files.forEach(file => {
                        const hexString = file.data;
                        const binaryData = new Uint8Array(hexString.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
                        const blob = new Blob([binaryData], { type: 'application/zip' });
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
                setError({ message: data.message, stack: data?.stack_trace });
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                setSuccess('Request cancelled');
            } else {
                console.error("Error:", error);
                setError({ message: error.message, stack: error.stack });
            }
        } finally {
            setLoading(false);
            setAbortController(null);
        }
    };

    const handleCancel = () => {
        if (abortController) {
            abortController.abort();
            setAbortController(null);
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
        // Clean up the text to remove excessive spacing and newlines
        let cleanedText = text;
        
        // If it's JSON, format it more compactly
        if (typeof text === 'object' || text.startsWith('{') || text.startsWith('[')) {
            try {
                const parsed = typeof text === 'object' ? text : JSON.parse(text);
                cleanedText = JSON.stringify(parsed, null, 1); // Use 1 space instead of 2
            } catch (e) {
                // If it's not valid JSON, just use the original text
                cleanedText = text;
            }
        }
        
        navigator.clipboard.writeText(cleanedText);
        setSuccess('Copied to clipboard!');
    };

    // Custom formatting function for sites data
    const formatSitesData = (sitesData) => {
        const sites = sitesData;
        let formatted = 'sites: {\n';
        
        Object.entries(sites).forEach(([url, array], index) => {
            formatted += `  "${url}":\n[${array.join(',')}]`;
            if (index < Object.keys(sites).length - 1) {
                formatted += ',';
            }
            formatted += '\n';
        });
        
        formatted += '}';
        return formatted;
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

        // Handle domain-based results (mode 1)
        if (result.domain_results) {
            return (
                <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1200px', mx: 'auto' }}>
                    <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                        Domain-Based Clustering Results
                    </Typography>
                    
                    {result.domain_results.map((domainResult, domainIndex) => (
                        <Accordion 
                            key={`domain-result-${domainIndex}`} 
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
                                    backgroundColor: domainResult.status === 'success' ? 'success.light' : 'error.light',
                                    '&:hover': {
                                        backgroundColor: domainResult.status === 'success' ? 'success.main' : 'error.main',
                                        color: 'white',
                                    },
                                    '& .MuiAccordionSummary-expandIconWrapper': {
                                        color: 'inherit'
                                    }
                                }}
                            >
                                <Typography sx={{ fontWeight: 'bold' }}>
                                    Domain: {domainResult.domain} - {domainResult.status}
                                </Typography>
                            </AccordionSummary>
                            <AccordionDetails sx={{ p: 3 }}>
                                {/* HTML Files Section */}
                                {domainResult.html_files && domainResult.html_files.length > 0 && (
                                    <Box sx={{ mb: theme.spacing(2) }}>
                                        <Typography variant="h6" gutterBottom>Generated HTML Files</Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                            {domainResult.html_files.map((file, index) => (
                                                <Button
                                                    key={index}
                                                    variant="contained"
                                                    color="primary"
                                                    onClick={() => window.open(`http://localhost:5000/${file.path}`, '_blank')}
                                                    sx={{ mb: 1 }}
                                                >
                                                    Open {file.filename}
                                                </Button>
                                            ))}
                                        </Box>
                                    </Box>
                                )}

                                {/* Rest of the domain result content */}
                                <Box sx={{ mb: theme.spacing(2) }}>
                                    <Typography variant="h6" gutterBottom>URLs in Domain</Typography>
                                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                        {domainResult.urls.map((url, index) => (
                                            <Chip
                                                key={index}
                                                label={url}
                                                color="primary"
                                                size="small"
                                            />
                                        ))}
                                    </Box>
                                </Box>

                                {domainResult.status === 'success' && (
                                    <>
                                        {/* Clustering Results Section */}
                                        {domainResult.clustering_results && domainResult.clustering_results.map((clusterResult, index) => (
                                            <Accordion 
                                                key={`cluster-result-${domainIndex}-${index}`} 
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
                                                        backgroundColor: clusterResult.status === 'error' ? 'error.light' : 'primary.light',
                                                        '&:hover': {
                                                            backgroundColor: clusterResult.status === 'error' ? 'error.main' : 'primary.main',
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
                                                    {/* Show error message if status is error */}
                                                    {clusterResult.status === 'error' && (
                                                        <Box sx={{ mb: theme.spacing(2) }}>
                                                            <Typography variant="h6" gutterBottom color="error">
                                                                Error in Level {clusterResult.level}
                                                            </Typography>
                                                            <Box sx={{ 
                                                                p: 3, 
                                                                bgcolor: 'error.light', 
                                                                borderRadius: 2,
                                                                border: '1px solid',
                                                                borderColor: 'error.main',
                                                                color: 'error.contrastText'
                                                            }}>
                                                                <Typography variant="body1">
                                                                    {clusterResult.message}
                                                                </Typography>
                                                                {clusterResult.stack_trace && (
                                                                    <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 1 }}>
                                                                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                                            Stack Trace:
                                                                        </Typography>
                                                                        <pre style={{ 
                                                                            fontSize: '0.8rem', 
                                                                            overflow: 'auto', 
                                                                            maxHeight: '200px',
                                                                            margin: 0,
                                                                            whiteSpace: 'pre-wrap'
                                                                        }}>
                                                                            {clusterResult.stack_trace}
                                                                        </pre>
                                                                    </Box>
                                                                )}
                                                            </Box>
                                                        </Box>
                                                    )}

                                                    {/* Show cluster info only if it exists and status is not error */}
                                                    {clusterResult.cluster_info && clusterResult.status !== 'error' && (
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
                                                    )}

                                                    {/* Show clusters only if they exist and status is not error */}
                                                    {clusterResult.clusters && clusterResult.status !== 'error' && (
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
                                                                    value={JSON.stringify(clusterResult.clusters, null, 1)}
                                                                    readOnly
                                                                />
                                                            </Box>
                                                            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                                                <Tooltip title="Copy to clipboard">
                                                                    <IconButton 
                                                                        size="small" 
                                                                        onClick={() => handleCopyToClipboard(JSON.stringify(clusterResult.clusters, null, 1))}
                                                                    >
                                                                        <ContentCopyIcon />
                                                                    </IconButton>
                                                                </Tooltip>
                                                            </Box>
                                                        </Box>
                                                    )}
                                                </AccordionDetails>
                                            </Accordion>
                                        ))}

                                        {/* Processed Clusters Section */}
                                        {domainResult.processed_clusters && domainResult.processed_clusters.map((processedCluster, index) => (
                                            <Accordion 
                                                key={`processed-cluster-${domainIndex}-${index}`} 
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
                                                                value={formatSitesData(processedCluster.processed_data.sites)}
                                                                readOnly
                                                            />
                                                        </Box>
                                                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                                            <Tooltip title="Copy to clipboard">
                                                                <IconButton 
                                                                    size="small" 
                                                                    onClick={() => handleCopyToClipboard(formatSitesData(processedCluster.processed_data.sites))}
                                                                >
                                                                    <ContentCopyIcon />
                                                                </IconButton>
                                                            </Tooltip>
                                                        </Box>
                                                    </Box>
                                                </AccordionDetails>
                                            </Accordion>
                                        ))}
                                    </>
                                )}
                            </AccordionDetails>
                        </Accordion>
                    ))}
                </Box>
            );
        }

        // Original results rendering (mode 0)
        return (
            <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1200px', mx: 'auto' }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                    Clustering Results
                </Typography>
                
                {/* HTML Files Section */}
                {result.html_files && result.html_files.length > 0 && (
                    <Box sx={{ mb: theme.spacing(2) }}>
                        <Typography variant="h6" gutterBottom>Generated HTML Files</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {result.html_files.map((file, index) => (
                                <Button
                                    key={index}
                                    variant="contained"
                                    color="primary"
                                    onClick={() => window.open(`http://localhost:5000/${file.path}`, '_blank')}
                                    sx={{ mb: 1 }}
                                >
                                    Open {file.filename}
                                </Button>
                            ))}
                        </Box>
                    </Box>
                )}
                
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
                                backgroundColor: clusterResult.status === 'error' ? 'error.light' : 'primary.light',
                                '&:hover': {
                                    backgroundColor: clusterResult.status === 'error' ? 'error.main' : 'primary.main',
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
                            {/* Show error message if status is error */}
                            {clusterResult.status === 'error' && (
                                <Box sx={{ mb: theme.spacing(2) }}>
                                    <Typography variant="h6" gutterBottom color="error">
                                        Error in Level {clusterResult.level}
                                    </Typography>
                                    <Box sx={{ 
                                        p: 3, 
                                        bgcolor: 'error.light', 
                                        borderRadius: 2,
                                        border: '1px solid',
                                        borderColor: 'error.main',
                                        color: 'error.contrastText'
                                    }}>
                                        <Typography variant="body1">
                                            {clusterResult.message}
                                        </Typography>
                                        {clusterResult.stack_trace && (
                                            <Box sx={{ mt: 2, p: 2, bgcolor: 'rgba(0,0,0,0.1)', borderRadius: 1 }}>
                                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                    Stack Trace:
                                                </Typography>
                                                <pre style={{ 
                                                    fontSize: '0.8rem', 
                                                    overflow: 'auto', 
                                                    maxHeight: '200px',
                                                    margin: 0,
                                                    whiteSpace: 'pre-wrap'
                                                }}>
                                                    {clusterResult.stack_trace}
                                                </pre>
                                            </Box>
                                        )}
                                    </Box>
                                </Box>
                            )}

                            {/* Show cluster info only if it exists and status is not error */}
                            {clusterResult.cluster_info && clusterResult.status !== 'error' && (
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
                            )}

                            {/* Show clusters only if they exist and status is not error */}
                            {clusterResult.clusters && clusterResult.status !== 'error' && (
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
                                            value={JSON.stringify(clusterResult.clusters, null, 1)}
                                            readOnly
                                        />
                                    </Box>
                                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                        <Tooltip title="Copy to clipboard">
                                            <IconButton 
                                                size="small" 
                                                onClick={() => handleCopyToClipboard(JSON.stringify(clusterResult.clusters, null, 1))}
                                            >
                                                <ContentCopyIcon />
                                            </IconButton>
                                        </Tooltip>
                                    </Box>
                                </Box>
                            )}
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
                                        value={formatSitesData(processedCluster.processed_data.sites)}
                                        readOnly
                                    />
                                </Box>
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1 }}>
                                    <Tooltip title="Copy to clipboard">
                                        <IconButton 
                                            size="small" 
                                            onClick={() => handleCopyToClipboard(formatSitesData(processedCluster.processed_data.sites))}
                                        >
                                            <ContentCopyIcon />
                                        </IconButton>
                                    </Tooltip>
                                </Box>
                            </Box>
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

                        {/* Mode Switch */}
                        <Box sx={{ margin: '0 30%', mt: theme.spacing(2), display: 'flex', justifyContent: 'center' }}>
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={isNewMode}
                                        onChange={(e) => setIsNewMode(e.target.checked)}
                                        color="primary"
                                    />
                                }
                                label={isNewMode ? "New Mode" : "Old Mode"}
                            />
                        </Box>

                        {/* URL Cards */}
                        <Box sx={{ 
                            margin: '0 30%', 
                            mt: theme.spacing(2),
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
                            gap: 2
                        }}>
                            {sortedDomains.map(domain => (
                                <Card key={domain} sx={{ 
                                    height: '100%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    transition: 'transform 0.2s, box-shadow 0.2s',
                                    '&:hover': {
                                        transform: 'translateY(-4px)',
                                        boxShadow: '0 8px 16px rgba(0,0,0,0.1)',
                                    },
                                    boxShadow: '0 4px 8px rgba(0,0,0,0.05)',
                                    borderRadius: 2,
                                    border: '1px solid',
                                    borderColor: 'divider',
                                    bgcolor: 'background.paper'
                                }}>
                                    <CardHeader
                                        title={domain}
                                        titleTypographyProps={{ 
                                            variant: 'h6',
                                            sx: { 
                                                fontSize: '1rem',
                                                fontWeight: 'bold',
                                                overflow: 'hidden',
                                                textOverflow: 'ellipsis',
                                                whiteSpace: 'nowrap',
                                                color: 'white'
                                            }
                                        }}
                                        sx={{
                                            bgcolor: 'primary.main',
                                            color: 'white',
                                            py: 1.5,
                                            '& .MuiCardHeader-content': {
                                                overflow: 'hidden'
                                            }
                                        }}
                                    />
                                    <CardContent sx={{ 
                                        flexGrow: 1,
                                        overflow: 'auto',
                                        maxHeight: '200px',
                                        p: 2,
                                        '&::-webkit-scrollbar': {
                                            width: '8px',
                                        },
                                        '&::-webkit-scrollbar-track': {
                                            background: 'transparent',
                                        },
                                        '&::-webkit-scrollbar-thumb': {
                                            background: 'rgba(0,0,0,0.2)',
                                            borderRadius: '4px',
                                        },
                                        '&::-webkit-scrollbar-thumb:hover': {
                                            background: 'rgba(0,0,0,0.3)',
                                        }
                                    }}>
                                        <Box sx={{ 
                                            display: 'flex', 
                                            flexWrap: 'wrap', 
                                            gap: 1 
                                        }}>
                                            {groupedUrls[domain].map((url, index) => (
                                                <Chip
                                                    key={index}
                                                    label={url}
                                                    onDelete={() => handleDelete(url)}
                                                    color="primary"
                                                    size="small"
                                                    sx={{ 
                                                        mb: 1,
                                                        '&:hover': {
                                                            bgcolor: 'primary.main',
                                                            color: 'primary.contrastText'
                                                        },
                                                        transition: 'background-color 0.2s'
                                                    }}
                                                />
                                            ))}
                                        </Box>
                                    </CardContent>
                                </Card>
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
                            {loading ? (
                                <>
                                    <Button
                                        variant="contained"
                                        color="error"
                                        onClick={handleCancel}
                                        sx={{ borderRadius: '20px' }}
                                    >
                                        Cancel
                                    </Button>
                                    <CircularProgress size={24} sx={{ ml: 1 }} />
                                </>
                            ) : (
                                <>
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
                                </>
                            )}
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
                                onClick={() => window.open(`http://localhost:5000/${file}`, '_blank')}
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