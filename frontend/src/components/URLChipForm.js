import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Chip, FormControl, Button, useTheme, Snackbar, CircularProgress, Grid2 as Grid, TextareaAutosize, Card, CardHeader, CardContent, Divider, Dialog, DialogTitle, DialogContent, DialogActions, IconButton, Grid as MuiGrid, InputLabel, Select, MenuItem, Typography, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import CloseIcon from '@mui/icons-material/Close';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const groupUrlsByDomain = (urls) => {
    const groups = {};
    urls.forEach(url => {
        try {
            const domain = new URL(url).hostname;
            if (!groups[domain]) groups[domain] = [];
            groups[domain].push(url);
        } catch (e) {
            // Ignore invalid URLs (shouldn't happen due to validation)
        }
    });
    return groups;
};

const URLChipForm = () => {
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
    const [clusterInput, setClusterInput] = useState({}); // State for cluster input per domain
    const [scrollDirection, setScrollDirection] = useState('horizontal'); // or 'vertical'
    const [showAllModal, setShowAllModal] = useState(false);
    const [customDomains, setCustomDomains] = useState([]);
    const [levelWarning, setLevelWarning] = useState(false);
    const theme = useTheme();
    const cardsContainerRef = useRef(null);
    const groupedUrls = groupUrlsByDomain(urls);

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
        // Remove leading @ if present
        let cleanedInput = input.trim();
        if (cleanedInput.startsWith('@')) {
            cleanedInput = cleanedInput.slice(1);
        }
        // Replace %20 with space
        cleanedInput = cleanedInput.replace(/%20/g, ' ');

        // Split on whitespace
        const newUrls = cleanedInput.split(/\s+/).filter(url => url.trim().length > 0);

        const validUrls = newUrls.filter(url => isValidUrl(url));
        const invalidUrls = newUrls.filter(url => !isValidUrl(url));

        // Prevent duplicates
        const uniqueValidUrls = validUrls.filter(url => !urls.includes(url));
        const duplicateUrls = validUrls.filter(url => urls.includes(url));

        if (invalidUrls.length > 0) {
            setWarning(`Invalid URLs: ${invalidUrls.join(', ')}`);
        }
        if (duplicateUrls.length > 0) {
            setWarning(`Duplicate URLs: ${duplicateUrls.join(', ')}`);
        }

        if (uniqueValidUrls.length > 0) {
            setUrls([...urls, ...uniqueValidUrls]);
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
        setLevelWarning(false);
    };

    const handleRun = async () => {
        if (selectedLevels.length === 0) {
            setWarning("You must select at least one level.");
            setLevelWarning(true);
            return;
        }

        setLoading(true);
        setError(null); // Clear previous error
        setResult(null); // Clear previous results
        setFilePaths(null); // Clear previous file paths
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
            if (data.status === "success") {
                // Display success notification
                setSuccess(data.message);

                // Handle file paths
                if (data.file_paths) {
                    const allFilePaths = [];
                    Object.entries(data.file_paths).forEach(([domain, levels]) => {
                        Object.entries(levels).forEach(([level, filePath]) => {
                            allFilePaths.push({
                                domain,
                                level,
                                path: filePath
                            });
                        });
                    });
                    setFilePaths(allFilePaths);
                }

                // Set the result with the new format
                setResult({
                    summary: data.summary,
                    clustering_data: data.clustering_data
                });
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
            // Get the clustering results from the previous process-urls call
            if (!result?.clustering_data) {
                setError({ message: "No clustering data available. Please run the URL processing first." });
                setLoading(false);
                return;
            }

            // Send the clustering results to the backend
            const response = await fetch("http://localhost:5000/process-clusters", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(result.clustering_data)
            });
            const data = await response.json();
            console.log("Received data from process-clusters:", data); // Debug log

            if (data.status === "success") {
                setSuccess(data.message);
                
                // Update the result with cluster results
                setResult(prev => {
                    const newResult = {
                        ...prev,
                        clusterResults: JSON.parse(data.body),
                        numerical_clusters: data.numerical_clusters
                    };
                    console.log("Updated result with numerical clusters:", newResult); // Debug log
                    return newResult;
                });
                
                // Set file paths from the response
                if (data.file_paths && data.file_paths.length > 0) {
                    console.log("Received file paths:", data.file_paths);
                    setFilePaths(data.file_paths);
                } else {
                    console.log("No file paths received in response");
                }
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

    useEffect(() => {
        const container = cardsContainerRef.current;
        if (!container) return;

        const onWheel = (e) => {
            if (scrollDirection === 'horizontal') {
                // Only scroll horizontally if vertical scroll is not possible
                e.preventDefault();
                container.scrollLeft += e.deltaY;
            }
        };

        container.addEventListener('wheel', onWheel, { passive: false });
        return () => container.removeEventListener('wheel', onWheel);
    }, [scrollDirection]);

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
                            <Box sx={{ 
                                border: '1px solid', 
                                borderColor: levelWarning ? 'error.main' : 'grey.400',
                                borderRadius: '8px', 
                                padding: theme.spacing(2), 
                                display: 'flex', 
                                flexWrap: 'wrap', 
                                justifyContent: 'center', 
                                gap: theme.spacing(1), 
                                width: '-webkit-fill-available',
                                backgroundColor: levelWarning ? 'error.light' : 'background.paper'
                            }}>
                                {Array.from({ length: 10 }, (_, i) => i + 1).map(level => (
                                    <Chip
                                        key={level}
                                        label={level}
                                        onClick={() => handleLevelSelect(level)}
                                        color={selectedLevels.includes(level) ? 'primary' : 'default'}
                                        sx={{
                                            border: levelWarning && !selectedLevels.includes(level) ? '1px solid' : 'none',
                                            borderColor: 'error.main'
                                        }}
                                    />
                                ))}
                            </Box>
                        </Box>
                        <Box
                          ref={cardsContainerRef}
                          sx={{
                            mt: theme.spacing(2),
                            width: '100%',
                            boxSizing: 'border-box',
                            display: 'flex',
                            flexDirection: scrollDirection === 'horizontal' ? 'row' : 'column',
                            overflowX: scrollDirection === 'horizontal' ? 'auto' : 'hidden',
                            overflowY: scrollDirection === 'vertical' ? 'auto' : 'hidden',
                            gap: theme.spacing(2),
                            maxHeight: scrollDirection === 'vertical' ? 400 : 'none',
                            minHeight: scrollDirection === 'horizontal' ? 250 : 'none',
                            mb: theme.spacing(4),
                            py: 4,
                            px: 4,
                          }}
                        >
                          {Object.entries(groupedUrls).map(([domain, domainUrls]) => (
                            <Card
                              key={domain}
                              sx={{
                                minWidth: 300,
                                maxWidth: 400,
                                borderRadius: 3,
                                boxShadow: '0 4px 20px 0 rgba(0,0,0,0.08)',
                                border: '1px solid',
                                borderColor: 'grey.200',
                                transition: 'transform 0.2s, box-shadow 0.2s',
                                '&:hover': {
                                  transform: 'translateY(-4px) scale(1.03)',
                                  boxShadow: '0 8px 32px 0 rgba(0,0,0,0.16)',
                                  borderColor: 'primary.light',
                                },
                                backgroundColor: 'background.paper',
                              }}
                            >
                              <CardHeader
                                title={domain}
                                sx={{
                                  background: theme.palette.primary.main,
                                  fontWeight: 'bold',
                                  textAlign: 'center',
                                  borderTopLeftRadius: 12,
                                  borderTopRightRadius: 12,
                                  borderBottom: '1px solid',
                                  borderColor: 'grey.100',
                                  py: 1.5,
                                  px: 2,
                                  fontSize: '1.1rem',
                                  color: '#fff',
                                }}
                              />
                              <Divider />
                              <CardContent>
                                <Box
                                  sx={{
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: theme.spacing(1),
                                    justifyContent: 'center',
                                    maxHeight: 150,
                                    overflowY: 'auto',
                                    '&::-webkit-scrollbar': {
                                      height: 6,
                                      width: 6,
                                      backgroundColor: '#f0f0f0',
                                      borderRadius: 8,
                                    },
                                    '&::-webkit-scrollbar-thumb': {
                                      background: theme.palette.primary.main,
                                      borderRadius: 8,
                                    },
                                    scrollbarWidth: 'thin', // Firefox
                                    scrollbarColor: '#a18cd1 #f0f0f0', // Firefox
                                  }}
                                >
                                  {domainUrls.map((url, idx) => (
                                    <Chip
                                      key={url}
                                      label={url}
                                      onDelete={() => handleDelete(url)}
                                      color="primary"
                                      sx={{
                                        maxWidth: 250,
                                        fontWeight: 500,
                                        fontSize: '0.95em',
                                        background: theme.palette.primary.main,
                                        color: '#fff',
                                      }}
                                    />
                                  ))}
                                </Box>
                              </CardContent>
                            </Card>
                          ))}
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
                          <Button variant="outlined" onClick={() => setShowAllModal(true)} disabled={urls.length === 0}>
                            Show All Domains
                          </Button>
                        </Box>
                        <Box
                          sx={{
                            mt: theme.spacing(2),
                            display: 'flex',
                            justifyContent: 'center',
                            gap: theme.spacing(2),
                            mb: theme.spacing(2),
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
                );
            case 'clusters':
                const groupedDomainKeys = Object.keys(groupedUrls);
                const allDomains = [
                    ...groupedDomainKeys.map(domain => ({ id: domain, name: domain, isCustom: false })),
                    ...customDomains.map(d => ({ ...d, isCustom: true }))
                ];

                return (
                    <Box sx={{ width: '100%', py: 2 }}>
                        {allDomains.length === 0 ? (
                            <Box>No domains available. Please add URLs in the Home view or add a domain.</Box>
                        ) : (
                            <Box
                                sx={{
                                    display: 'flex',
                                    flexWrap: 'wrap',
                                    gap: 3,
                                    justifyContent: 'center',
                                }}
                            >
                                {allDomains.map(({ id, name, isCustom }) => (
                                    <Box
                                        key={id}
                                        sx={{
                                            minWidth: 280,
                                            maxWidth: 320,
                                            flex: '1 1 300px',
                                            border: '1px solid #ccc',
                                            borderRadius: 2,
                                            p: 2,
                                            background: '#fafafa',
                                            boxShadow: 1,
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'stretch',
                                            position: 'relative',
                                        }}
                                    >
                                        {isCustom ? (
                                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                                <TextField
                                                    value={name}
                                                    onChange={e => {
                                                        const newName = e.target.value;
                                                        setCustomDomains(prev =>
                                                            prev.map(d =>
                                                                d.id === id ? { ...d, name: newName } : d
                                                            )
                                                        );
                                                    }}
                                                    size="small"
                                                    variant="outlined"
                                                    sx={{ flex: 1, mr: 1 }}
                                                    placeholder="Domain name"
                                                />
                                                <IconButton
                                                    size="small"
                                                    onClick={() => {
                                                        setCustomDomains(prev => prev.filter(d => d.id !== id));
                                                        setClusterInput(prev => {
                                                            const updated = { ...prev };
                                                            delete updated[id];
                                                            return updated;
                                                        });
                                                    }}
                                                >
                                                    <CloseIcon fontSize="small" />
                                                </IconButton>
                                            </Box>
                                        ) : (
                                            <Box sx={{ fontWeight: 'bold', mb: 1, textAlign: 'center' }}>{name}</Box>
                                        )}
                                        
                                        {/* Show clustering data for each level */}
                                        {selectedLevels.map(level => {
                                            const clusteringData = result?.clustering_data?.[name]?.[level];
                                            if (!clusteringData) return null;
                                            
                                            return (
                                                <Box key={level} sx={{ mb: 2 }}>
                                                    <Typography variant="subtitle2" sx={{ mb: 1 }}>
                                                        Level {level} Clustering Results:
                                                    </Typography>
                                                    <textarea
                                                        rows={6}
                                                        style={{
                                                            width: '100%',
                                                            padding: '10px',
                                                            boxSizing: 'border-box',
                                                            maxHeight: '200px',
                                                            overflowY: 'scroll',
                                                            fontFamily: 'monospace',
                                                            fontSize: '12px',
                                                            backgroundColor: '#f5f5f5',
                                                            border: '1px solid #ddd',
                                                            borderRadius: '4px'
                                                        }}
                                                        value={JSON.stringify(clusteringData.results, null, 2)}
                                                        readOnly
                                                    />
                                                    {clusteringData.debug && (
                                                        <>
                                                            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
                                                                Debug Information:
                                                            </Typography>
                                                            <textarea
                                                                rows={6}
                                                                style={{
                                                                    width: '100%',
                                                                    padding: '10px',
                                                                    boxSizing: 'border-box',
                                                                    maxHeight: '200px',
                                                                    overflowY: 'scroll',
                                                                    fontFamily: 'monospace',
                                                                    fontSize: '12px',
                                                                    backgroundColor: '#f8f8f8',
                                                                    border: '1px solid #ddd',
                                                                    borderRadius: '4px'
                                                                }}
                                                                value={JSON.stringify(clusteringData.debug.attribute_values, null, 2)}
                                                                readOnly
                                                            />
                                                        </>
                                                    )}
                                                </Box>
                                            );
                                        })}
                                    </Box>
                                ))}
                            </Box>
                        )}
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleClusterRun}
                                sx={{ borderRadius: '20px' }}
                                disabled={!result?.clustering_data}
                            >
                                Run Clustering
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

    // Add a debug section to show raw data
    const renderDebugInfo = () => {
        if (!result?.numerical_clusters) return null;
        
        return (
            <Box sx={{ mt: theme.spacing(2), p: 2, backgroundColor: '#f8f9fa', borderRadius: 1 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>Debug Information:</Typography>
                <Typography variant="body2" component="pre" sx={{ 
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-all',
                    fontFamily: 'monospace',
                    fontSize: '0.8rem'
                }}>
                    {JSON.stringify(result.numerical_clusters, null, 2)}
                </Typography>
            </Box>
        );
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
                boxSizing: 'border-box'
            }}
        >
            <Box sx={{ display: 'flex', justifyContent: 'center', gap: theme.spacing(2), mb: theme.spacing(2) }}>
                <Button variant="contained" onClick={() => setCurrentView('home')}>Home</Button>
                <Button variant="contained" onClick={() => setCurrentView('clusters')}>Clusters</Button>
                <Button variant="contained" onClick={() => setCurrentView('view3')}>View 3</Button>
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
                    {filePaths && filePaths.length > 0 ? (
                        <Box sx={{ mt: theme.spacing(2) }}>
                            <Accordion>
                                <AccordionSummary
                                    expandIcon={<ExpandMoreIcon />}
                                    aria-controls="generated-files-content"
                                    id="generated-files-header"
                                >
                                    <Typography variant="h6">Generated Files</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                        {filePaths.map((fileInfo, index) => (
                                            <Button
                                                key={index}
                                                variant="contained"
                                                color="primary"
                                                onClick={() => window.open(`http://localhost:5000/results/${fileInfo.path}`, '_blank')}
                                                sx={{ 
                                                    justifyContent: 'flex-start',
                                                    textTransform: 'none',
                                                    mb: 1,
                                                    '&:hover': {
                                                        backgroundColor: theme.palette.primary.dark
                                                    }
                                                }}
                                            >
                                                View {fileInfo.domain} - Level {fileInfo.level} Results
                                            </Button>
                                        ))}
                                    </Box>
                                </AccordionDetails>
                            </Accordion>
                        </Box>
                    ) : (
                        <Box sx={{ mt: theme.spacing(2) }}>
                            <Typography variant="body1" color="text.secondary">
                                No files generated yet. Run the clustering process to generate files.
                            </Typography>
                        </Box>
                    )}
                    {result.clusterResults && (
                        <Box sx={{ mt: theme.spacing(2) }}>
                            <Accordion>
                                <AccordionSummary
                                    expandIcon={<ExpandMoreIcon />}
                                    aria-controls="clustering-results-content"
                                    id="clustering-results-header"
                                >
                                    <Typography variant="h6">Clustering Results</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <Box sx={{ 
                                        backgroundColor: 'background.paper',
                                        p: 2,
                                        borderRadius: 1,
                                        maxHeight: '400px',
                                        overflowY: 'auto'
                                    }}>
                                        <pre style={{ margin: 0 }}>
                                            {JSON.stringify(result.clusterResults, null, 2)}
                                        </pre>
                                    </Box>
                                </AccordionDetails>
                            </Accordion>
                        </Box>
                    )}
                    {result.numerical_clusters && (
                        <Box sx={{ mt: theme.spacing(2) }}>
                            <Accordion>
                                <AccordionSummary
                                    expandIcon={<ExpandMoreIcon />}
                                    aria-controls="numerical-clusters-content"
                                    id="numerical-clusters-header"
                                >
                                    <Typography variant="h6">Numerical Cluster Representation</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <Box sx={{ 
                                        backgroundColor: 'background.paper',
                                        p: 2,
                                        borderRadius: 1,
                                        maxHeight: '400px',
                                        overflowY: 'auto'
                                    }}>
                                        {Object.entries(result.numerical_clusters.Sites || {}).map(([siteName, clusters]) => (
                                            <Box key={siteName} sx={{ mb: 3, p: 2, border: '1px solid', borderColor: 'grey.200', borderRadius: 1 }}>
                                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 1, color: theme.palette.primary.main }}>
                                                    {siteName}:
                                                </Typography>
                                                <Box sx={{ 
                                                    backgroundColor: '#f5f5f5',
                                                    p: 2,
                                                    borderRadius: 1,
                                                    fontFamily: 'monospace',
                                                    fontSize: '0.9rem',
                                                    whiteSpace: 'pre-wrap',
                                                    wordBreak: 'break-all'
                                                }}>
                                                    {clusters.join(', ')}
                                                </Box>
                                                <Typography variant="caption" sx={{ display: 'block', mt: 1, color: 'text.secondary' }}>
                                                    Sequence length: {clusters.length}
                                                </Typography>
                                            </Box>
                                        ))}
                                    </Box>
                                </AccordionDetails>
                            </Accordion>
                        </Box>
                    )}
                    
                    {/* {renderDebugInfo()} */}
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
            <Dialog open={showAllModal} onClose={() => setShowAllModal(false)} maxWidth="xl" fullWidth>
                <DialogTitle sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    All Domains
                    <IconButton onClick={() => setShowAllModal(false)}>
                        <CloseIcon />
                    </IconButton>
                </DialogTitle>
                <DialogContent dividers>
                    <MuiGrid container spacing={2}>
                        {Object.entries(groupedUrls).map(([domain, domainUrls]) => (
                            <MuiGrid item xs={12} sm={6} md={4} lg={2.4} key={domain}>
                                <Card
                                    sx={{
                                        minWidth: 200,
                                        maxWidth: 400,
                                        borderRadius: 3,
                                        boxShadow: '0 4px 20px 0 rgba(0,0,0,0.08)',
                                        border: '1px solid',
                                        borderColor: 'grey.200',
                                        transition: 'transform 0.2s, box-shadow 0.2s',
                                        '&:hover': {
                                            transform: 'translateY(-4px) scale(1.03)',
                                            boxShadow: '0 8px 32px 0 rgba(0,0,0,0.16)',
                                            borderColor: 'primary.light',
                                        },
                                        backgroundColor: 'background.paper',
                                    }}
                                >
                                    <CardHeader
                                        title={domain}
                                        sx={{
                                            background: theme.palette.primary.main,
                                            fontWeight: 'bold',
                                            textAlign: 'center',
                                            borderTopLeftRadius: 12,
                                            borderTopRightRadius: 12,
                                            borderBottom: '1px solid',
                                            borderColor: 'grey.100',
                                            py: 1.5,
                                            px: 2,
                                            fontSize: '1.1rem',
                                            color: '#fff',
                                        }}
                                    />
                                    <Divider />
                                    <CardContent>
                                        <Box
                                            sx={{
                                                display: 'flex',
                                                flexWrap: 'wrap',
                                                gap: theme.spacing(1),
                                                justifyContent: 'center',
                                                maxHeight: 150,
                                                overflowY: 'auto',
                                                '&::-webkit-scrollbar-thumb': {
                                                    background: theme.palette.primary.main,
                                                    borderRadius: 8,
                                                },
                                            }}
                                        >
                                            {domainUrls.map((url, idx) => (
                                                <Chip
                                                    key={url}
                                                    label={url}
                                                    onDelete={() => handleDelete(url)}
                                                    color="primary"
                                                    sx={{
                                                        maxWidth: 250,
                                                        fontWeight: 500,
                                                        fontSize: '0.95em',
                                                        background: theme.palette.primary.main,
                                                        color: '#fff',
                                                    }}
                                                />
                                            ))}
                                        </Box>
                                    </CardContent>
                                </Card>
                            </MuiGrid>
                        ))}
                    </MuiGrid>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setShowAllModal(false)} color="primary" variant="contained">
                        Close
                    </Button>
                </DialogActions>
            </Dialog>
        </Grid>
    );
};

export default URLChipForm;