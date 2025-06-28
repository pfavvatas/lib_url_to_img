import React, { useState, useEffect } from 'react';
import { Box, TextField, Chip, FormControl, Button, useTheme, Snackbar, CircularProgress, Grid2 as Grid, TextareaAutosize, Accordion, AccordionSummary, AccordionDetails, Typography, IconButton, Tooltip, Card, CardContent, CardHeader, Switch, FormControlLabel, Fab, Collapse, Modal } from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import CloseIcon from '@mui/icons-material/Close';
import html2pdf from 'html2pdf.js';
import { interpolateViridis } from 'd3-scale-chromatic';

/*
🎨 CONSISTENT COLOR SCHEME:
- Primary sections (main content): primary.light / primary.main 
  - Generated Files, Site Similarity Analysis, Clustering Results
- Secondary sections (sub-content): grey.200 / grey.300
  - Level accordions, Processed Clusters, Domain Results
- Info sections (neutral): grey.100 / grey.200  
  - Timing Logs, Performance Metrics
- Success/Error states: success.light/main, error.light/main
  - Only for actual success/error conditions
- Data visualization: Keep semantic colors
  - Similarity matrix: success (green), warning (yellow), primary (blue)
*/

const URLChipForm = ({ darkMode, onThemeChange }) => {
    const [urls, setUrls] = useState([]);
    const [inputValue, setInputValue] = useState("");
    const [warning, setWarning] = useState("");
    const [success, setSuccess] = useState(""); // State for success message
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [filePaths, setFilePaths] = useState(null);
    const [error, setError] = useState(null); // State for error message and stack trace
    const [selectedLevels, setSelectedLevels] = useState([]);
    const [currentView, setCurrentView] = useState('home'); // State for current view
    const [clusterInput, setClusterInput] = useState(""); // State for cluster input
    const [isNewMode, setIsNewMode] = useState(false);
    const [abortController, setAbortController] = useState(null);
    
    // Custom experiments state
    const [experimentResults, setExperimentResults] = useState(null);
    const [experimentLoading, setExperimentLoading] = useState(false);
    
    // Results Archive state
    const [archiveExperiments, setArchiveExperiments] = useState([]);
    const [selectedExperiment, setSelectedExperiment] = useState(null);
    const [archiveLoading, setArchiveLoading] = useState(false);
    
    // Config Builder state
    const [customConfig, setCustomConfig] = useState({
        experiment_name: '',
        available_urls: [],
        modes: [0], // Fixed to mode 0 - process all URLs together
        levels: [1],
        url_combinations: [] // URLs per domain - no pre-selection, user must choose
    });
    const [configUrlInput, setConfigUrlInput] = useState('');
    
    // Image Modal state
    const [imageModalOpen, setImageModalOpen] = useState(false);
    const [selectedImage, setSelectedImage] = useState(null);
    
    // Scroll to top and card collapse state
    const [showScrollTop, setShowScrollTop] = useState(false);
    const [collapsedCards, setCollapsedCards] = useState(new Set());
    
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
        // Parse multiple URLs from input (handles newlines, spaces, quotes)
        const urlPattern = /https?:\/\/[^\s\n\r]+/g;
        const foundUrls = input.match(urlPattern) || [];
        
        // Also try splitting by whitespace and filtering, handle quoted URLs
        const quotedUrls = input.match(/"[^"]+"|\S+/g)?.map(url => url.replace(/(^"|"$)/g, '')) || [];
        const splitUrls = input.split(/[\s\n\r]+/).filter(url => url.trim().length > 0);
        const allUrls = [...new Set([...foundUrls, ...quotedUrls, ...splitUrls])]; // Remove duplicates
        
        const validUrls = allUrls.filter(url => isValidUrl(url.trim()));
        const invalidUrls = allUrls.filter(url => !isValidUrl(url.trim()));

        if (invalidUrls.length > 0) {
            setWarning(`Invalid URLs skipped: ${invalidUrls.slice(0, 3).join(', ')}${invalidUrls.length > 3 ? '...' : ''}`);
        }

        if (validUrls.length > 0) {
            // Remove duplicates from existing URLs
            const existingUrls = new Set(urls);
            const newUrls = validUrls.filter(url => !existingUrls.has(url.trim()));
            
            if (newUrls.length > 0) {
                setUrls([...urls, ...newUrls.map(url => url.trim())]);
                setSuccess(`Added ${newUrls.length} new URLs${validUrls.length > newUrls.length ? ` (${validUrls.length - newUrls.length} duplicates skipped)` : ''}`);
            } else {
                setWarning('All URLs are already added');
            }
            setInputValue('');
        } else if (allUrls.length > 0) {
            setWarning('No valid URLs found in the pasted text');
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
                
                // Play success notification sound
                playNotificationSound(true);

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
                // Play error notification sound
                playNotificationSound(false);
            }

        } catch (error) {
            if (error.name === 'AbortError') {
                setSuccess('Request cancelled');
            } else {
                console.error("Error:", error);
                setError({ message: error.message, stack: error.stack });
                // Play error notification sound
                playNotificationSound(false);
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

    // Function to copy all levels' similarity matrices and clustering summaries in formatted text
    const handleCopyAllLevelsSummary = (resultData = null) => {
        const dataToProcess = resultData || result;
        if (!dataToProcess) {
            setWarning('No results available to copy');
            return;
        }

        let formattedOutput = '';
        const processedLevels = new Set();

        // Helper function to extract domain name from URL
        const extractDomainKey = (url) => {
            try {
                const urlObj = new URL(url);
                let domain = urlObj.hostname.replace('www.', '');
                // Further simplify domain names (remove common suffixes for cleaner keys)
                domain = domain.replace(/\.(com|org|net|gov|edu)$/, '');
                return domain;
            } catch {
                // If not a valid URL, use the string as-is but clean it up
                return url.replace(/[^a-zA-Z0-9-]/g, '').toLowerCase();
            }
        };

        // Process Mode 0 results (all together)
        if (dataToProcess.processed_clusters) {
            dataToProcess.processed_clusters.forEach((processedCluster) => {
                if (processedCluster.processed_data?.site_similarity?.status === 'success') {
                    const level = processedCluster.level;
                    if (processedLevels.has(level)) return;
                    processedLevels.add(level);

                    const { matrix, sites } = processedCluster.processed_data.site_similarity.data;
                    
                    formattedOutput += `Level ${level}:\n`;
                    
                    // Create similarity matrix with domain keys
                    const domainMatrix = {};
                    sites.forEach((rowSite, rowIndex) => {
                        const rowKey = extractDomainKey(rowSite);
                        domainMatrix[rowKey] = {};
                        sites.forEach((colSite, colIndex) => {
                            const colKey = extractDomainKey(colSite);
                            domainMatrix[rowKey][colKey] = matrix[rowSite][colSite];
                        });
                    });

                    formattedOutput += JSON.stringify(domainMatrix, null, 1) + '\n\n';

                    // Find corresponding clustering result
                    const clusterResult = dataToProcess.clustering_results?.find(cr => cr.level === level);
                    if (clusterResult) {
                        const clusterInfo = getClusterInfo(clusterResult);
                        if (clusterInfo) {
                            const clusteringSummary = {
                                level: level,
                                message: clusterResult.message,
                                summary: {
                                    num_clusters: clusterInfo.num_clusters,
                                    dbcv_score: clusterInfo.dbcv_score,
                                    min_cluster_size: clusterInfo.min_cluster_size,
                                    cluster_selection_epsilon: clusterInfo.cluster_selection_epsilon,
                                    useful_attributes_count: clusterInfo.useful_attributes?.length || 0
                                },
                                archived_test_id: dataToProcess.test_metadata?.test_id,
                                timestamp: new Date().toISOString()
                            };
                            formattedOutput += JSON.stringify(clusteringSummary, null, 1) + '\n\n';
                        }
                    }
                }
            });
        }

        // Process Mode 1 results (domain-based)
        if (dataToProcess.domain_results) {
            dataToProcess.domain_results.forEach((domainResult) => {
                if (domainResult.processed_clusters) {
                    domainResult.processed_clusters.forEach((processedCluster) => {
                        if (processedCluster.processed_data?.site_similarity?.status === 'success') {
                            const level = processedCluster.level;
                            const levelDomainKey = `${domainResult.domain}-${level}`;
                            if (processedLevels.has(levelDomainKey)) return;
                            processedLevels.add(levelDomainKey);

                            const { matrix, sites } = processedCluster.processed_data.site_similarity.data;
                            
                            formattedOutput += `Level ${level} (${domainResult.domain}):\n`;
                            
                            // Create similarity matrix with domain keys
                            const domainMatrix = {};
                            sites.forEach((rowSite, rowIndex) => {
                                const rowKey = extractDomainKey(rowSite);
                                domainMatrix[rowKey] = {};
                                sites.forEach((colSite, colIndex) => {
                                    const colKey = extractDomainKey(colSite);
                                    domainMatrix[rowKey][colKey] = matrix[rowSite][colSite];
                                });
                            });

                            formattedOutput += JSON.stringify(domainMatrix, null, 1) + '\n\n';

                            // Find corresponding clustering result
                            const clusterResult = domainResult.clustering_results?.find(cr => cr.level === level);
                            if (clusterResult) {
                                const clusterInfo = getClusterInfo(clusterResult);
                                if (clusterInfo) {
                                    const clusteringSummary = {
                                        domain: domainResult.domain,
                                        level: level,
                                        message: clusterResult.message,
                                        summary: {
                                            num_clusters: clusterInfo.num_clusters,
                                            dbcv_score: clusterInfo.dbcv_score,
                                            min_cluster_size: clusterInfo.min_cluster_size,
                                            cluster_selection_epsilon: clusterInfo.cluster_selection_epsilon,
                                            useful_attributes_count: clusterInfo.useful_attributes?.length || 0
                                        },
                                        archived_test_id: dataToProcess.test_metadata?.test_id,
                                        timestamp: new Date().toISOString()
                                    };
                                    formattedOutput += JSON.stringify(clusteringSummary, null, 1) + '\n\n';
                                }
                            }
                        }
                    });
                }
            });
        }

        if (formattedOutput.trim()) {
            navigator.clipboard.writeText(formattedOutput.trim());
            const levelCount = processedLevels.size;
            setSuccess(`📋 All levels summary copied! (${levelCount} levels with similarity & clustering data)`);
        } else {
            setWarning('No similarity and clustering data found to copy');
        }
    };

    // Function to copy comprehensive results including similarity matrix and clustering analysis
    const handleCopyComprehensiveResults = (resultData = null) => {
        const dataToProcess = resultData || result;
        if (!dataToProcess) {
            setWarning('No results available to copy');
            return;
        }

        const comprehensiveData = {
            experiment_metadata: {
                timestamp: new Date().toISOString(),
                test_mode: dataToProcess.test_metadata?.mode || 'unknown',
                levels_processed: dataToProcess.test_metadata?.levels || [],
                urls_count: dataToProcess.test_metadata?.url_count || 0,
                urls: dataToProcess.test_metadata?.urls || [],
                duration: dataToProcess.test_metadata?.duration || 0
            },
            similarity_analysis: {},
            clustering_analysis: {},
            performance_metrics: dataToProcess.timing_logs?.performance_metrics || null
        };

        // Collect similarity matrices from all levels
        if (dataToProcess.processed_clusters) {
            dataToProcess.processed_clusters.forEach((processedCluster) => {
                if (processedCluster.processed_data?.site_similarity?.status === 'success') {
                    const levelKey = `level_${processedCluster.level}`;
                    comprehensiveData.similarity_analysis[levelKey] = {
                        level: processedCluster.level,
                        matrix: processedCluster.processed_data.site_similarity.data.matrix,
                        sites: processedCluster.processed_data.site_similarity.data.sites,
                        summary: processedCluster.processed_data.site_similarity.data.summary
                    };
                }
            });
        }

        // Collect similarity matrices from domain results (Mode 1)
        if (dataToProcess.domain_results) {
            dataToProcess.domain_results.forEach((domainResult) => {
                if (domainResult.processed_clusters) {
                    domainResult.processed_clusters.forEach((processedCluster) => {
                        if (processedCluster.processed_data?.site_similarity?.status === 'success') {
                            const levelKey = `${domainResult.domain}_level_${processedCluster.level}`;
                            comprehensiveData.similarity_analysis[levelKey] = {
                                domain: domainResult.domain,
                                level: processedCluster.level,
                                matrix: processedCluster.processed_data.site_similarity.data.matrix,
                                sites: processedCluster.processed_data.site_similarity.data.sites,
                                summary: processedCluster.processed_data.site_similarity.data.summary
                            };
                        }
                    });
                }
            });
        }

        // Collect clustering results
        if (dataToProcess.clustering_results) {
            dataToProcess.clustering_results.forEach((clusterResult) => {
                const levelKey = `level_${clusterResult.level}`;
                const clusterInfo = getClusterInfo(clusterResult);
                const clustersData = getClustersData(clusterResult);
                
                comprehensiveData.clustering_analysis[levelKey] = {
                    level: clusterResult.level,
                    status: clusterResult.status,
                    message: clusterResult.message,
                    cluster_info: clusterInfo,
                    clusters_data: clustersData,
                    is_lightweight: clustersData?.is_lightweight || false
                };
            });
        }

        // Collect clustering results from domain results (Mode 1)
        if (dataToProcess.domain_results) {
            dataToProcess.domain_results.forEach((domainResult) => {
                if (domainResult.clustering_results) {
                    domainResult.clustering_results.forEach((clusterResult) => {
                        const levelKey = `${domainResult.domain}_level_${clusterResult.level}`;
                        const clusterInfo = getClusterInfo(clusterResult);
                        const clustersData = getClustersData(clusterResult);
                        
                        comprehensiveData.clustering_analysis[levelKey] = {
                            domain: domainResult.domain,
                            level: clusterResult.level,
                            status: clusterResult.status,
                            message: clusterResult.message,
                            cluster_info: clusterInfo,
                            clusters_data: clustersData,
                            is_lightweight: clustersData?.is_lightweight || false
                        };
                    });
                }
            });
        }

        // Copy to clipboard
        const formattedData = JSON.stringify(comprehensiveData, null, 2);
        navigator.clipboard.writeText(formattedData);
        
        const totalLevels = Object.keys(comprehensiveData.similarity_analysis).length + Object.keys(comprehensiveData.clustering_analysis).length;
        setSuccess(`📋 Comprehensive results copied! (${totalLevels} analysis sets)`);
    };





    // Results Archive Functions
    const loadArchiveExperiments = async () => {
        setArchiveLoading(true);
        try {
            const response = await fetch("http://localhost:5000/experiments/results/list");
            const data = await response.json();
            if (data.status === "success") {
                setArchiveExperiments(data.experiments);
                setSuccess(`Loaded ${data.total_count} experiment results`);
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            setError({ message: `Failed to load experiment results: ${error.message}` });
        } finally {
            setArchiveLoading(false);
        }
    };

    // Function to load large data files for experiment results
    const loadLargeDataHtmlFiles = async (experimentId, testId) => {
        try {
            setLoading(true);
            const response = await fetch(`http://localhost:5000/experiments/results/${experimentId}/large-data`);
            const data = await response.json();
            
            if (data.status === 'success') {
                console.log('📁 Large data files:', data.files);
                setSuccess(`Found ${data.files.length} large data files (${data.total_size_mb.toFixed(1)} MB total)`);
                
                // Find HTML files data
                const htmlFilesData = data.files.find(f => f.type === 'html_files');
                if (htmlFilesData) {
                    const htmlResponse = await fetch(`http://localhost:5000/experiments/results/${experimentId}/large-data/${htmlFilesData.filename}`);
                    const htmlData = await htmlResponse.json();
                    
                    if (htmlData.status === 'success') {
                        console.log('📄 HTML files from large data:', htmlData.data);
                        setSuccess(`Loaded ${htmlData.data.length} HTML files from large data`);
                        return htmlData.data;
                    }
                }
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            console.error('❌ Error loading large data HTML files:', error);
            setError({ message: `Error loading large data: ${error.message}` });
        } finally {
            setLoading(false);
        }
        return [];
    };

    const loadLargeDataClusteringResults = async (experimentId, testId) => {
        try {
            setLoading(true);
            const response = await fetch(`http://localhost:5000/experiments/results/${experimentId}/large-data`);
            const data = await response.json();
            
            if (data.status === 'success') {
                console.log('📁 Large data files:', data.files);
                
                // Find clustering results data
                const clusteringData = data.files.find(f => f.type === 'clustering_results');
                if (clusteringData) {
                    const clusteringResponse = await fetch(`http://localhost:5000/experiments/results/${experimentId}/large-data/${clusteringData.filename}`);
                    const clusteringResult = await clusteringResponse.json();
                    
                    if (clusteringResult.status === 'success') {
                        console.log('🎯 Clustering results from large data:', clusteringResult.data);
                        setSuccess(`Loaded clustering results from large data (${clusteringData.size_mb.toFixed(1)} MB)`);
                        return clusteringResult.data;
                    }
                }
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            console.error('❌ Error loading large data clustering results:', error);
            setError({ message: `Error loading clustering data: ${error.message}` });
        } finally {
            setLoading(false);
        }
        return null;
    };



    const loadExperimentDetails = async (experimentId) => {
        setArchiveLoading(true);
        try {
            const response = await fetch(`http://localhost:5000/experiments/results/${experimentId}`);
            const data = await response.json();
            if (data.status === "success") {
                // Handle the new response structure where data is in experiment_data
                const experimentData = data.experiment_data;
                setSelectedExperiment(experimentData);
                setSuccess(`Loaded experiment: ${experimentData.experiment_info.name}`);
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            setError({ message: `Failed to load experiment details: ${error.message}` });
        } finally {
            setArchiveLoading(false);
        }
    };

    const handleGnuplotFileClick = async (experimentId, filename, action = 'download') => {
        try {
            if (action === 'download') {
                // Download the file
                const downloadUrl = `http://localhost:5000/experiments/results/${experimentId}/files/${filename}`;
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                setSuccess(`Downloaded ${filename}`);
            } else if (action === 'preview') {
                // Get file content for preview/copy
                const response = await fetch(`http://localhost:5000/experiments/results/${experimentId}/files/${filename}/content`);
                const data = await response.json();
                if (data.status === "success") {
                    // Copy content to clipboard
                    await navigator.clipboard.writeText(data.content);
                    setSuccess(`Copied ${filename} content to clipboard`);
                } else {
                    setError({ message: data.message });
                }
            }
        } catch (error) {
            setError({ message: `Failed to ${action} ${filename}: ${error.message}` });
        }
    };

    // Config Builder Functions
    const addConfigUrls = (input) => {
        // Parse multiple URLs from input (handles newlines, spaces, quotes)
        const urlPattern = /https?:\/\/[^\s\n\r]+/g;
        const foundUrls = input.match(urlPattern) || [];
        
        // Also try splitting by whitespace and filtering
        const splitUrls = input.split(/[\s\n\r]+/).filter(url => url.trim().length > 0);
        const allUrls = [...new Set([...foundUrls, ...splitUrls])]; // Remove duplicates
        
        const validUrls = allUrls.filter(url => isValidUrl(url.trim()));
        const invalidUrls = allUrls.filter(url => !isValidUrl(url.trim()));
        
        if (invalidUrls.length > 0) {
            setWarning(`Invalid URLs skipped: ${invalidUrls.slice(0, 3).join(', ')}${invalidUrls.length > 3 ? '...' : ''}`);
        }
        
        if (validUrls.length > 0) {
            // Remove duplicates from existing URLs
            const existingUrls = new Set(customConfig.available_urls);
            const newUrls = validUrls.filter(url => !existingUrls.has(url.trim()));
            
            if (newUrls.length > 0) {
                setCustomConfig(prev => ({
                    ...prev,
                    available_urls: [...prev.available_urls, ...newUrls.map(url => url.trim())]
                }));
                setSuccess(`Added ${newUrls.length} new URLs${validUrls.length > newUrls.length ? ` (${validUrls.length - newUrls.length} duplicates skipped)` : ''}`);
            } else {
                setWarning('All URLs are already added');
            }
            setConfigUrlInput('');
        } else if (allUrls.length > 0) {
            setWarning('No valid URLs found in the pasted text');
        }
    };
    
    const addConfigUrl = () => {
        if (configUrlInput.trim()) {
            addConfigUrls(configUrlInput.trim());
        } else {
            setWarning('Please enter a URL');
        }
    };
    
    const handleConfigUrlPaste = (e) => {
        e.preventDefault();
        const pastedText = e.clipboardData.getData('text');
        addConfigUrls(pastedText);
    };

    const removeConfigUrl = (indexToRemove) => {
        setCustomConfig(prev => ({
            ...prev,
            available_urls: prev.available_urls.filter((_, index) => index !== indexToRemove)
        }));
    };

    const runCustomExperiment = async () => {
        if (customConfig.available_urls.length === 0) {
            setWarning('Please add at least one URL');
            return;
        }
        if (customConfig.levels.length === 0) {
            setWarning('Please select at least one level');
            return;
        }

        setExperimentLoading(true);
        setError(null);

        try {
            // Generate test cases based on custom config with URLs per Domain logic
            const testCases = [];
            let testIndex = 1;

            // Group URLs by domain first
            const domainGroups = customConfig.available_urls.reduce((acc, url) => {
                try {
                    const domain = new URL(url).hostname;
                    if (!acc[domain]) acc[domain] = [];
                    acc[domain].push(url);
                    return acc;
                } catch {
                    if (!acc['invalid']) acc['invalid'] = [];
                    acc['invalid'].push(url);
                    return acc;
                }
            }, {});

            const domains = Object.keys(domainGroups);
            const minUrlsPerDomain = Math.min(...Object.values(domainGroups).map(urls => urls.length));

            // For each mode, create combinations for each level set and URLs per domain count
            for (const mode of customConfig.modes) {
                for (const urlsPerDomain of customConfig.url_combinations) {
                    // Check if we can get the requested URLs per domain from all domains
                    if (urlsPerDomain <= minUrlsPerDomain) {
                        // Calculate total URLs per test (urlsPerDomain × number of domains)
                        const totalUrlsPerTest = urlsPerDomain * domains.length;
                        
                        // Create multiple variations for this parameter set
                        const maxVariations = Math.min(5, minUrlsPerDomain - urlsPerDomain + 1);
                        
                        for (let variation = 0; variation < maxVariations; variation++) {
                            
                            // Select URLs from each domain for Mode 0 processing
                            const selectedUrls = [];
                            
                            domains.forEach(domain => {
                                const domainUrls = domainGroups[domain];
                                // Use variation to select different sets of URLs from each domain
                                const startIndex = variation % (domainUrls.length - urlsPerDomain + 1);
                                
                                for (let i = 0; i < urlsPerDomain; i++) {
                                    const index = (startIndex + i) % domainUrls.length;
                                    selectedUrls.push(domainUrls[index]);
                                }
                            });
                            
                            // Create test case with flat URL array for Mode 0 processing
                            const testCase = {
                                id: `exp_${testIndex.toString().padStart(3, '0')}_${mode}_L${customConfig.levels.join('_')}_D${domains.length}_U${urlsPerDomain}_V${variation + 1}`,
                                name: `Mode ${mode} - Levels ${customConfig.levels.join(',')} - ${urlsPerDomain} URLs/domain × ${domains.length} domains (Var ${variation + 1})`,
                                description: `Experiment using Mode ${mode}, levels ${customConfig.levels.join(',')}, ${urlsPerDomain} URLs per domain across ${domains.length} domains (${selectedUrls.length} total URLs, variation ${variation + 1})`,
                                mode: mode,
                                levels: customConfig.levels,
                                urls: selectedUrls, // Flat array of selected URLs (X URLs from each domain)
                                url_count: selectedUrls.length,
                                urls_per_domain: urlsPerDomain,
                                domain_count: domains.length,
                                domains: domains,
                                variation: variation + 1,
                                estimated_duration: selectedUrls.length * customConfig.levels.length * 0.5,
                                priority: 'experiment'
                            };
                            testCases.push(testCase);
                            testIndex++;
                        }
                        }
                }
            }

            // Run the experiment batch
            const response = await fetch("http://localhost:5000/experiments/run-batch", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    experiment_name: customConfig.experiment_name || 'Experiment',
                    selected_test_cases: testCases
                })
            });
            const data = await response.json();

            if (data.status === "success") {
                setExperimentResults(data.experiment_summary);
                setSuccess(`Experiment completed! ${data.experiment_summary.experiment_info.successful_tests} successful tests`);
                // Play success notification sound
                playNotificationSound(true);
                
                // Results will be displayed in the config view below the form
            } else {
                setError({ message: data.message, stack: data?.traceback });
                // Play error notification sound
                playNotificationSound(false);
            }
        } catch (error) {
            console.error("Error:", error);
            setError({ message: error.message, stack: error.stack });
            // Play error notification sound
            playNotificationSound(false);
        } finally {
            setExperimentLoading(false);
        }
    };



    // Load archive experiments when switching to results view
    useEffect(() => {
        if (currentView === 'results' && archiveExperiments.length === 0) {
            loadArchiveExperiments();
        }
    }, [currentView, archiveExperiments.length]);

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

    // Function to format duration in a readable way
    const formatDuration = (seconds) => {
        if (seconds < 1) {
            return `${(seconds * 1000).toFixed(2)}ms`;
        } else if (seconds < 60) {
            return `${seconds.toFixed(2)}s`;
        } else {
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            return `${minutes}m ${remainingSeconds.toFixed(2)}s`;
        }
    };

    // Function to create site labels
    const createSiteLabel = (index) => {
        return `site_${index + 1}`;
    };

    // Scroll to top functionality
    const handleScrollToTop = () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    };

    // Handle scroll events
    useEffect(() => {
        const handleScroll = () => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            setShowScrollTop(scrollTop > 300); // Show button after scrolling 300px
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Card collapse functionality
    const toggleCardCollapse = (cardId) => {
        const newCollapsedCards = new Set(collapsedCards);
        if (newCollapsedCards.has(cardId)) {
            // Card is expanded, remove from set to collapse it
            newCollapsedCards.delete(cardId);
        } else {
            // Card is collapsed, add to set to expand it
            newCollapsedCards.add(cardId);
        }
        setCollapsedCards(newCollapsedCards);
    };

    const isCardCollapsed = (cardId) => {  
        // Default to collapsed (true) if not in the set, expanded (false) if in the set
        return !collapsedCards.has(cardId);
    };

    // Image Modal Functions
    const handleImageClick = (image) => {
        setSelectedImage(image);
        setImageModalOpen(true);
    };

    const handleCloseImageModal = () => {
        setImageModalOpen(false);
        setSelectedImage(null);
    };

    // Function to generate PDF from similarity results
    const generatePDF = (siteSimilarity, level = null) => {
        if (!siteSimilarity || siteSimilarity.status !== 'success' || !siteSimilarity.data) return;

        const { data } = siteSimilarity;
        const { matrix, sites, summary } = data;
        
        // Create a temporary container for PDF content
        const pdfContent = document.createElement('div');
        pdfContent.style.fontFamily = 'Arial, sans-serif';
        pdfContent.style.padding = '20px';
        pdfContent.style.backgroundColor = 'white';
        pdfContent.style.color = 'black';

        // Add title
        const title = document.createElement('h1');
        title.style.textAlign = 'center';
        title.style.marginBottom = '20px';
        title.style.color = '#1976d2';
        title.innerHTML = level ? 
            `Site Similarity Analysis - Level ${level}` : 
            'Site Similarity Analysis';
        pdfContent.appendChild(title);

        // Add timestamp
        const timestamp = document.createElement('p');
        timestamp.style.textAlign = 'center';
        timestamp.style.fontSize = '12px';
        timestamp.style.color = '#666';
        timestamp.style.marginBottom = '30px';
        timestamp.innerHTML = `Generated on: ${new Date().toLocaleString()}`;
        pdfContent.appendChild(timestamp);

        // Add site reference
        const siteRefTitle = document.createElement('h2');
        siteRefTitle.innerHTML = 'Site Reference';
        siteRefTitle.style.borderBottom = '2px solid #1976d2';
        siteRefTitle.style.paddingBottom = '5px';
        siteRefTitle.style.marginBottom = '15px';
        pdfContent.appendChild(siteRefTitle);

        sites.forEach((site, index) => {
            const siteItem = document.createElement('div');
            siteItem.style.marginBottom = '8px';
            siteItem.style.padding = '8px';
            siteItem.style.border = '1px solid #ddd';
            siteItem.style.borderRadius = '4px';
            siteItem.innerHTML = `<strong style="color: #1976d2;">${createSiteLabel(index)}:</strong> ${site}`;
            pdfContent.appendChild(siteItem);
        });

        // Add summary statistics
        const summaryTitle = document.createElement('h2');
        summaryTitle.innerHTML = 'Summary Statistics';
        summaryTitle.style.borderBottom = '2px solid #1976d2';
        summaryTitle.style.paddingBottom = '5px';
        summaryTitle.style.marginTop = '30px';
        summaryTitle.style.marginBottom = '15px';
        pdfContent.appendChild(summaryTitle);

        const summaryGrid = document.createElement('div');
        summaryGrid.style.display = 'grid';
        summaryGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
        summaryGrid.style.gap = '15px';
        summaryGrid.style.marginBottom = '30px';

        const summaryItems = [
            { label: 'Total Sites', value: summary.total_sites },
            { label: 'Average Similarity', value: `${summary.average_similarity.toFixed(2)}%` },
            { label: 'Maximum Similarity', value: `${summary.max_similarity.toFixed(2)}%` },
            { label: 'Minimum Similarity', value: `${summary.min_similarity.toFixed(2)}%` }
        ];

        summaryItems.forEach(item => {
            const summaryItem = document.createElement('div');
            summaryItem.style.padding = '10px';
            summaryItem.style.border = '1px solid #ddd';
            summaryItem.style.borderRadius = '4px';
            summaryItem.style.textAlign = 'center';
            summaryItem.innerHTML = `
                <div style="font-size: 12px; color: #666; margin-bottom: 5px;">${item.label}</div>
                <div style="font-size: 18px; font-weight: bold; color: #1976d2;">${item.value}</div>
            `;
            summaryGrid.appendChild(summaryItem);
        });
        pdfContent.appendChild(summaryGrid);

        // Calculate actual min/max values from the similarity matrix (excluding diagonal)
        const allSimilarityValues = [];
        sites.forEach(rowSite => {
            sites.forEach(colSite => {
                if (rowSite !== colSite) { // Exclude diagonal (same site comparisons)
                    allSimilarityValues.push(matrix[rowSite][colSite]);
                }
            });
        });
        
        const actualMinSimilarity = Math.min(...allSimilarityValues);
        const actualMaxSimilarity = Math.max(...allSimilarityValues);

        // Add similarity matrix
        const matrixTitle = document.createElement('h2');
        matrixTitle.innerHTML = 'Cosine Similarity Matrix (%)';
        matrixTitle.style.borderBottom = '2px solid #1976d2';
        matrixTitle.style.paddingBottom = '5px';
        matrixTitle.style.marginBottom = '15px';
        pdfContent.appendChild(matrixTitle);

        // Add data range info
        const dataRangeInfo = document.createElement('p');
        dataRangeInfo.innerHTML = `<strong>Data Range:</strong> ${actualMinSimilarity.toFixed(2)}% - ${actualMaxSimilarity.toFixed(2)}%`;
        dataRangeInfo.style.fontSize = '12px';
        dataRangeInfo.style.marginBottom = '15px';
        dataRangeInfo.style.color = '#666';
        pdfContent.appendChild(dataRangeInfo);

        // Create table
        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';
        table.style.fontSize = '10px';
        table.style.marginBottom = '20px';

        // Table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        // Empty cell for top-left corner
        const emptyCell = document.createElement('th');
        emptyCell.style.padding = '8px';
        emptyCell.style.border = '1px solid #ddd';
        emptyCell.style.backgroundColor = '#f5f5f5';
        emptyCell.style.fontWeight = 'bold';
        emptyCell.innerHTML = '';
        headerRow.appendChild(emptyCell);

        // Column headers
        sites.forEach((site, index) => {
            const th = document.createElement('th');
            th.style.padding = '8px';
            th.style.border = '1px solid #ddd';
            th.style.backgroundColor = '#f5f5f5';
            th.style.fontWeight = 'bold';
            th.style.textAlign = 'center';
            th.style.fontSize = '9px';
            th.innerHTML = createSiteLabel(index);
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Table body
        const tbody = document.createElement('tbody');
        sites.forEach((rowSite, rowIndex) => {
            const tr = document.createElement('tr');
            
            // Row header
            const rowHeader = document.createElement('th');
            rowHeader.style.padding = '8px';
            rowHeader.style.border = '1px solid #ddd';
            rowHeader.style.backgroundColor = '#f5f5f5';
            rowHeader.style.fontWeight = 'bold';
            rowHeader.style.textAlign = 'center';
            rowHeader.style.fontSize = '9px';
            rowHeader.innerHTML = createSiteLabel(rowIndex);
            tr.appendChild(rowHeader);

            // Data cells
            sites.forEach((colSite, colIndex) => {
                const td = document.createElement('td');
                const similarity = matrix[rowSite][colSite];
                const isDiagonal = rowIndex === colIndex;

                td.style.padding = '8px';
                td.style.border = '1px solid #ddd';
                td.style.textAlign = 'center';
                td.style.fontSize = '9px';
                
                // Use viridis colormap with consistent range (min to max) for PDF
                const bgColor = isDiagonal 
                    ? getViridisColor(100, actualMinSimilarity, actualMaxSimilarity) // Diagonal uses full range
                    : getViridisColor(similarity, actualMinSimilarity, actualMaxSimilarity);
                const textColor = getContrastTextColor(bgColor);
                
                td.style.backgroundColor = bgColor;
                td.style.color = textColor;
                
                if (isDiagonal) {
                    td.style.fontWeight = 'bold';
                    td.innerHTML = similarity.toFixed(2) + ' ●';
                } else {
                    td.innerHTML = similarity.toFixed(2);
                }
                
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        pdfContent.appendChild(table);

        // Add viridis colormap legend
        const legendTitle = document.createElement('h3');
        legendTitle.innerHTML = 'Viridis Colormap Legend';
        legendTitle.style.marginTop = '20px';
        legendTitle.style.marginBottom = '10px';
        pdfContent.appendChild(legendTitle);

        // Create gradient bar for PDF using actual data range (min to max)
        const dataRange = actualMaxSimilarity - actualMinSimilarity;
        const gradientContainer = document.createElement('div');
        gradientContainer.style.marginBottom = '15px';
        
        const gradientBar = document.createElement('div');
        gradientBar.style.height = '30px';
        gradientBar.style.width = '300px';
        gradientBar.style.border = '1px solid #ccc';
        gradientBar.style.borderRadius = '4px';
        gradientBar.style.position = 'relative';
        gradientBar.style.background = `linear-gradient(to right, 
            ${getViridisColor(actualMinSimilarity, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.1, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.2, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.3, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.4, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.5, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.6, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.7, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.8, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMinSimilarity + dataRange * 0.9, actualMinSimilarity, actualMaxSimilarity)}, 
            ${getViridisColor(actualMaxSimilarity, actualMinSimilarity, actualMaxSimilarity)})`;
        
        // Add percentage labels based on actual data range (min to max)
        const labelsContainer = document.createElement('div');
        labelsContainer.style.display = 'flex';
        labelsContainer.style.justifyContent = 'space-between';
        labelsContainer.style.width = '300px';
        labelsContainer.style.marginTop = '5px';
        labelsContainer.style.fontSize = '10px';
        
        // Create labels for actual data range (min to max)
        const labelValues = [];
        for (let i = 0; i <= 4; i++) {
            const value = actualMinSimilarity + (dataRange * i / 4);
            labelValues.push(`${value.toFixed(1)}%`);
        }
        
        labelValues.forEach(label => {
            const labelSpan = document.createElement('span');
            labelSpan.innerHTML = label;
            labelSpan.style.fontSize = '10px';
            labelsContainer.appendChild(labelSpan);
        });
        
        gradientContainer.appendChild(gradientBar);
        gradientContainer.appendChild(labelsContainer);
        pdfContent.appendChild(gradientContainer);

        // Add explanation
        const explanation = document.createElement('div');
        explanation.style.fontSize = '10px';
        explanation.style.marginTop = '10px';
        explanation.innerHTML = `
            <div style="margin-bottom: 5px;"><strong>Similarity Scale:</strong> Colors represent cosine similarity percentages using the Viridis colormap</div>
            <div style="margin-bottom: 5px;"><strong>Color Range:</strong> ${actualMinSimilarity.toFixed(2)}% - ${actualMaxSimilarity.toFixed(2)}% (colormap spans your actual data range)</div>
            <div style="margin-bottom: 5px;">• Darker colors (purple/blue) = Lower similarity (closer to ${actualMinSimilarity.toFixed(1)}%)</div>
            <div style="margin-bottom: 5px;">• Medium colors (teal/green) = Medium similarity</div>
            <div style="margin-bottom: 5px;">• Brighter colors (yellow) = Higher similarity (closer to ${actualMaxSimilarity.toFixed(1)}%)</div>
            <div>• ● symbol indicates same site comparison (100% similarity)</div>
        `;
        pdfContent.appendChild(explanation);

        // Generate PDF
        const opt = {
            margin: 0.5,
            filename: level ? 
                `similarity-analysis-level-${level}-${new Date().toISOString().slice(0, 10)}.pdf` :
                `similarity-analysis-${new Date().toISOString().slice(0, 10)}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true },
            jsPDF: { unit: 'in', format: 'a4', orientation: 'landscape' }
        };

        html2pdf().set(opt).from(pdfContent).save().then(() => {
            setSuccess('PDF downloaded successfully!');
        }).catch((error) => {
            console.error('PDF generation error:', error);
            setError({ message: 'Failed to generate PDF', stack: error.toString() });
        });
    };

    // Function to convert similarity percentage to viridis color using official D3 colormap
    const getViridisColor = (value, minValue = 0, maxValue = 100) => {
        // Special case: 100% values should be white
        if (value === 100) {
            return '#ffffff';
        }
        
        // Normalize value based on actual data range
        const range = maxValue - minValue;
        const normalizedValue = range > 0 ? Math.max(0, Math.min(1, (value - minValue) / range)) : 0;
        
        // Use the official Viridis colormap from d3-scale-chromatic
        return interpolateViridis(normalizedValue);
    };

    // Function to determine text color based on background brightness
    const getContrastTextColor = (backgroundColor) => {
        // Extract RGB values from rgb() string
        const match = backgroundColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (!match) return '#000000';
        
        const [, r, g, b] = match.map(Number);
        
        // Calculate relative luminance
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        
        // Return white text for dark backgrounds, black for light backgrounds
        return luminance > 0.5 ? '#000000' : '#ffffff';
    };

    // Function to render site similarity results with comprehensive information
    const renderSiteSimilarityResults = (siteSimilarity, level = null, processedClusterData = null, titlePrefix = '') => {
        if (!siteSimilarity || siteSimilarity.status !== 'success' || !siteSimilarity.data) return null;

        const { data } = siteSimilarity;
        const { matrix, sites, summary } = data;

        return (
            <Accordion 
                sx={{ 
                    mb: theme.spacing(2),
                    '&:before': {
                        display: 'none',
                    },
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                    borderRadius: '8px !important',
                    overflow: 'hidden',
                    backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                }}
            >
                <AccordionSummary 
                    expandIcon={<ExpandMoreIcon />}
                    sx={{
                        backgroundColor: darkMode ? '#333' : 'primary.light',
                        color: darkMode ? '#ffffff' : 'inherit',
                        '&:hover': {
                            backgroundColor: darkMode ? '#404040' : 'primary.main',
                            color: darkMode ? '#ffffff' : 'white',
                        },
                        '& .MuiAccordionSummary-expandIconWrapper': {
                            color: 'inherit'
                        }
                    }}
                >
                    <Typography sx={{ 
                        fontWeight: 'bold',
                        color: darkMode ? '#ffffff' : 'inherit'
                    }}>
                        📊 Site Similarity Analysis {titlePrefix ? `${titlePrefix} ` : ''}Level {level} ({summary.total_sites} sites)
                    </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ 
                    p: 3,
                    backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                }}>
                    {/* Summary Statistics */}
                    <Box sx={{ 
                        mb: theme.spacing(3),
                        p: 2,
                        backgroundColor: darkMode ? '#2a2a2a' : 'background.paper',
                        borderRadius: 2,
                        border: '1px solid',
                        borderColor: darkMode ? '#555' : 'divider'
                    }}>
                        <Typography variant="h6" gutterBottom sx={{
                            color: darkMode ? '#ffffff' : 'inherit'
                        }}>📊 Summary Statistics</Typography>
                        <Box sx={{ 
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: 2
                        }}>
                            <Box>
                                <Typography variant="subtitle2" sx={{
                                    color: darkMode ? '#aaa' : 'text.secondary'
                                }}>Total Sites</Typography>
                                <Typography variant="h6" color="primary">{summary.total_sites}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" sx={{
                                    color: darkMode ? '#aaa' : 'text.secondary'
                                }}>Average Similarity</Typography>
                                <Typography variant="h6" color="primary">{summary.average_similarity.toFixed(2)}%</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" sx={{
                                    color: darkMode ? '#aaa' : 'text.secondary'
                                }}>Maximum Similarity</Typography>
                                <Typography variant="h6" color="primary">{summary.max_similarity.toFixed(2)}%</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" sx={{
                                    color: darkMode ? '#aaa' : 'text.secondary'
                                }}>Minimum Similarity</Typography>
                                <Typography variant="h6" color="primary">{summary.min_similarity.toFixed(2)}%</Typography>
                            </Box>
                        </Box>
                    </Box>

                    {/* Associated HTML Files */}
                    {processedClusterData && processedClusterData.html_files && processedClusterData.html_files.length > 0 && (
                        <Box sx={{ 
                            mb: theme.spacing(3),
                            p: 2,
                            backgroundColor: darkMode ? '#333' : 'grey.100',
                            borderRadius: 2,
                            border: '1px solid',
                            borderColor: darkMode ? '#555' : 'divider'
                        }}>
                            <Typography variant="h6" gutterBottom sx={{
                                color: darkMode ? '#ffffff' : 'inherit'
                            }}>📁 Associated HTML Files ({processedClusterData.html_files.length})</Typography>
                            <Grid container spacing={1}>
                                {processedClusterData.html_files.map((file, index) => (
                                    <Grid item xs={12} sm={6} md={4} key={index}>
                                        <Card sx={{ 
                                            cursor: 'pointer',
                                            transition: 'all 0.2s ease-in-out',
                                            backgroundColor: darkMode ? '#444' : 'background.paper',
                                            '&:hover': {
                                                transform: 'translateY(-1px)',
                                                boxShadow: darkMode 
                                                    ? '0 4px 8px rgba(0,0,0,0.4)' 
                                                    : '0 2px 4px rgba(0,0,0,0.1)'
                                            }
                                        }}
                                        onClick={() => {
                                            const fileUrl = `http://localhost:5000/output_html_files/${file.path}`;
                                            setSuccess(`Opening: ${file.title || file.filename}`);
                                            window.open(fileUrl, '_blank');
                                        }}
                                        >
                                            <CardContent sx={{ p: 1.5, '&:last-child': { pb: 1.5 } }}>
                                                <Typography 
                                                    variant="caption" 
                                                    sx={{ 
                                                        fontWeight: 'bold',
                                                        display: 'block',
                                                        mb: 0.5,
                                                        overflow: 'hidden',
                                                        textOverflow: 'ellipsis',
                                                        whiteSpace: 'nowrap',
                                                        color: darkMode ? '#ffffff' : 'inherit'
                                                    }}
                                                    title={file.title || file.filename}
                                                >
                                                    📄 {file.title || file.filename}
                                                </Typography>
                                                <Typography variant="caption" sx={{ 
                                                    color: darkMode ? '#aaa' : 'text.secondary',
                                                    fontSize: '0.6rem'
                                                }}>
                                                    {file.file_size_kb ? `${file.file_size_kb.toFixed(1)} KB` : ''}
                                                    {file.domain && ` • ${file.domain}`}
                                                </Typography>
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                ))}
                            </Grid>
                        </Box>
                    )}

                    {/* Timing Information */}
                    {processedClusterData && processedClusterData.timing_logs && (
                        <Box sx={{ 
                            mb: theme.spacing(3),
                            p: 2,
                            backgroundColor: darkMode ? '#333' : 'info.light',
                            borderRadius: 2,
                            border: '1px solid',
                            borderColor: darkMode ? '#555' : 'divider'
                        }}>
                            <Typography variant="h6" gutterBottom sx={{
                                color: darkMode ? '#ffffff' : 'inherit'
                            }}>⏱️ Processing Performance</Typography>
                            <Box sx={{ 
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                                gap: 2
                            }}>
                                <Box>
                                    <Typography variant="subtitle2" sx={{
                                        color: darkMode ? '#aaa' : 'text.secondary'
                                    }}>Total Duration</Typography>
                                    <Typography variant="h6" sx={{
                                        color: darkMode ? '#ffffff' : 'inherit'
                                    }}>{formatDuration(processedClusterData.timing_logs.total_duration)}</Typography>
                                </Box>
                                {processedClusterData.timing_logs.steps && processedClusterData.timing_logs.steps.site_similarity_analysis && (
                                    <Box>
                                        <Typography variant="subtitle2" sx={{
                                            color: darkMode ? '#aaa' : 'text.secondary'
                                        }}>Similarity Analysis</Typography>
                                        <Typography variant="h6" sx={{
                                            color: darkMode ? '#ffffff' : 'inherit'
                                        }}>{formatDuration(processedClusterData.timing_logs.steps.site_similarity_analysis.duration)}</Typography>
                                    </Box>
                                )}
                                {processedClusterData.timing_logs.steps && processedClusterData.timing_logs.steps.html_generation && (
                                    <Box>
                                        <Typography variant="subtitle2" sx={{
                                            color: darkMode ? '#aaa' : 'text.secondary'
                                        }}>HTML Generation</Typography>
                                        <Typography variant="h6" sx={{
                                            color: darkMode ? '#ffffff' : 'inherit'
                                        }}>{formatDuration(processedClusterData.timing_logs.steps.html_generation.duration)}</Typography>
                                    </Box>
                                )}
                                {processedClusterData.timing_logs.file_operations && (
                                    <Box>
                                        <Typography variant="subtitle2" sx={{
                                            color: darkMode ? '#aaa' : 'text.secondary'
                                        }}>Data Processing</Typography>
                                        <Typography variant="h6" sx={{
                                            color: darkMode ? '#ffffff' : 'inherit'
                                                                                      }}>
                                              {processedClusterData.timing_logs.file_operations.guid_processing ? 
                                                 `${processedClusterData.timing_logs.file_operations.guids_processed} GUIDs` :
                                                  'Completed'
                                              }
                                        </Typography>
                                    </Box>
                                )}
                            </Box>
                        </Box>
                    )}

                    {/* Similarity Matrix Table */}
                    {(() => {
                        // Calculate actual min/max values from the similarity matrix (excluding diagonal)
                        const allSimilarityValues = [];
                        sites.forEach(rowSite => {
                            sites.forEach(colSite => {
                                if (rowSite !== colSite) { // Exclude diagonal (same site comparisons)
                                    allSimilarityValues.push(matrix[rowSite][colSite]);
                                }
                            });
                        });
                        
                        const actualMinSimilarity = Math.min(...allSimilarityValues);
                        const actualMaxSimilarity = Math.max(...allSimilarityValues);
                        
                        return (
                            <Box sx={{ mb: theme.spacing(2) }}>
                                <Typography variant="h6" gutterBottom sx={{
                                    color: darkMode ? '#ffffff' : 'inherit'
                                }}>🔢 Cosine Similarity Matrix (%)</Typography>
                                <Typography variant="caption" sx={{ 
                                    display: 'block',
                                    mb: 1,
                                    color: darkMode ? '#aaa' : 'text.secondary'
                                }}>
                                    Data range: {actualMinSimilarity.toFixed(2)}% - {actualMaxSimilarity.toFixed(2)}%
                                </Typography>
                                <Box sx={{ 
                                    overflowX: 'auto',
                                    maxHeight: '500px',
                                    border: '1px solid',
                                    borderColor: darkMode ? '#555' : 'divider',
                                    borderRadius: 1
                                }}>
                                    <table style={{ 
                                        width: '100%', 
                                        borderCollapse: 'collapse',
                                        minWidth: 'auto',
                                        fontSize: '0.9rem'
                                    }}>
                                        <thead>
                                            <tr style={{ 
                                                backgroundColor: darkMode ? '#404040' : theme.palette.grey[100] 
                                            }}>
                                                <th style={{ 
                                                    padding: '12px', 
                                                    border: darkMode ? '1px solid #555' : '1px solid #ddd',
                                                    textAlign: 'left',
                                                    fontWeight: 'bold',
                                                    position: 'sticky',
                                                    top: 0,
                                                    backgroundColor: darkMode ? '#404040' : theme.palette.grey[100],
                                                    color: darkMode ? '#ffffff' : 'inherit',
                                                    zIndex: 1
                                                }}>
                                                    Site
                                                </th>
                                                {sites.map((site, index) => {
                                                    // Extract domain or truncate URL for display
                                                    const displayName = (() => {
                                                        try {
                                                            const url = new URL(site);
                                                            return url.hostname.replace('www.', '');
                                                        } catch {
                                                            return site.length > 15 ? site.substring(0, 15) + '...' : site;
                                                        }
                                                    })();
                                                    
                                                    return (
                                                        <th key={index} style={{ 
                                                            padding: '6px 8px', 
                                                            border: darkMode ? '1px solid #555' : '1px solid #ddd',
                                                            textAlign: 'center',
                                                            fontWeight: 'bold',
                                                            position: 'sticky',
                                                            top: 0,
                                                            backgroundColor: darkMode ? '#404040' : theme.palette.grey[100],
                                                            color: darkMode ? '#ffffff' : 'inherit',
                                                            zIndex: 1,
                                                            minWidth: '120px',
                                                            maxWidth: '150px',
                                                            fontSize: '0.8rem',
                                                            wordBreak: 'break-word',
                                                            lineHeight: '1.2'
                                                        }}>
                                                            <Tooltip title={site} arrow>
                                                                <span style={{ 
                                                                    fontWeight: 'bold', 
                                                                    color: theme.palette.primary.main,
                                                                    cursor: 'help'
                                                                }}>
                                                                    {displayName}
                                                                </span>
                                                            </Tooltip>
                                                        </th>
                                                    );
                                                })}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {sites.map((rowSite, rowIndex) => {
                                                // Extract domain or truncate URL for display
                                                const displayName = (() => {
                                                    try {
                                                        const url = new URL(rowSite);
                                                        return url.hostname.replace('www.', '');
                                                    } catch {
                                                        return rowSite.length > 15 ? rowSite.substring(0, 15) + '...' : rowSite;
                                                    }
                                                })();
                                                
                                                return (
                                                    <tr key={rowIndex}>
                                                        <td style={{ 
                                                            padding: '6px 8px', 
                                                            border: darkMode ? '1px solid #555' : '1px solid #ddd',
                                                            fontWeight: 'bold',
                                                            backgroundColor: darkMode ? '#333' : theme.palette.grey[50],
                                                            color: darkMode ? '#ffffff' : 'inherit',
                                                            position: 'sticky',
                                                            left: 0,
                                                            zIndex: 1,
                                                            minWidth: '120px',
                                                            maxWidth: '150px',
                                                            fontSize: '0.8rem',
                                                            textAlign: 'center',
                                                            wordBreak: 'break-word',
                                                            lineHeight: '1.2'
                                                        }}>
                                                            <Tooltip title={rowSite} arrow>
                                                                <span style={{ 
                                                                    fontWeight: 'bold', 
                                                                    color: theme.palette.primary.main,
                                                                    cursor: 'help'
                                                                }}>
                                                                    {displayName}
                                                                </span>
                                                            </Tooltip>
                                                                                                                 </td>
                                                         {sites.map((colSite, colIndex) => {
                                                            const similarity = matrix[rowSite][colSite];
                                                            const isDiagonal = rowIndex === colIndex;
                                                            
                                                                                                        // Use viridis colormap with consistent range (min to max)
                                            const bgColor = isDiagonal 
                                                ? getViridisColor(100, actualMinSimilarity, actualMaxSimilarity) // Diagonal uses full range
                                                : getViridisColor(similarity, actualMinSimilarity, actualMaxSimilarity);
                                                            const textColor = getContrastTextColor(bgColor);
                                                            
                                                            return (
                                                                <td key={colIndex} style={{ 
                                                                    padding: '8px', 
                                                                    border: darkMode ? '1px solid #555' : '1px solid #ddd',
                                                                    textAlign: 'center',
                                                                    fontSize: '0.85rem',
                                                                    minWidth: '60px',
                                                                    backgroundColor: bgColor,
                                                                    color: textColor,
                                                                    fontWeight: isDiagonal ? 'bold' : 'normal',
                                                                    position: 'relative'
                                                                }}>
                                                                    {similarity.toFixed(2)}
                                                                    {isDiagonal && (
                                                                        <span style={{
                                                                            position: 'absolute',
                                                                            top: '2px',
                                                                            right: '2px',
                                                                            fontSize: '0.6rem',
                                                                            opacity: 0.7
                                                                        }}>
                                                                            ●
                                                                        </span>
                                                                    )}
                                                                </td>
                                                            );
                                                        })}
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </Box>
                            </Box>
                        );
                    })()}



                    {/* Viridis Color Scale Legend */}
                    {(() => {
                        // Calculate actual min/max values from the similarity matrix (excluding diagonal)
                        const allSimilarityValues = [];
                        sites.forEach(rowSite => {
                            sites.forEach(colSite => {
                                if (rowSite !== colSite) { // Exclude diagonal (same site comparisons)
                                    allSimilarityValues.push(matrix[rowSite][colSite]);
                                }
                            });
                        });
                        
                        const actualMinSimilarity = Math.min(...allSimilarityValues);
                        const actualMaxSimilarity = Math.max(...allSimilarityValues);
                        const dataRange = actualMaxSimilarity - actualMinSimilarity;
                        
                        // Create tick marks based on actual data range
                        const createDataTicks = () => {
                            const ticks = [];
                            for (let i = 0; i <= 4; i++) {
                                const value = actualMinSimilarity + (dataRange * i / 4);
                                ticks.push({
                                    percentage: (i / 4) * 100,
                                    value: value,
                                    label: `${value.toFixed(1)}%`
                                });
                            }
                            return ticks;
                        };
                        
                        const dataTicks = createDataTicks();
                        
                        return (
                            <Box sx={{ 
                                mt: 1,
                                p: 1.5,
                                backgroundColor: darkMode ? '#2a2a2a' : 'grey.50',
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: darkMode ? '#555' : 'grey.300'
                            }}>
                                <Typography variant="subtitle2" sx={{ 
                                    fontWeight: 'bold', 
                                    mb: 1,
                                    color: darkMode ? '#ffffff' : 'inherit'
                                }}>
                                    Similarity Scale (Viridis Colormap):
                                </Typography>
                                
                                {/* Data Range Scale (Min to Max) */}
                                <Box sx={{ mb: 2 }}>
                                    <Typography variant="caption" sx={{ 
                                        fontSize: '0.7rem',
                                        color: darkMode ? '#aaa' : 'text.secondary',
                                        fontWeight: 'bold',
                                        mb: 0.5,
                                        display: 'block'
                                    }}>
                                        🌈 Viridis Scale for Your Data ({actualMinSimilarity.toFixed(1)}% - {actualMaxSimilarity.toFixed(1)}%):
                                    </Typography>
                                    <Box sx={{ 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        gap: 1,
                                        mb: 1 
                                    }}>
                                        <Typography variant="caption" sx={{ 
                                            fontSize: '0.75rem',
                                            color: darkMode ? '#aaa' : 'inherit',
                                            minWidth: '40px'
                                        }}>
                                            {actualMinSimilarity.toFixed(1)}%
                                        </Typography>
                                        <Box sx={{ 
                                            position: 'relative',
                                            height: 20,
                                            flex: 1,
                                            borderRadius: 1,
                                            border: darkMode ? '1px solid #555' : '1px solid #ccc',
                                            background: `linear-gradient(to right, 
                                                ${getViridisColor(actualMinSimilarity, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.1, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.2, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.3, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.4, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.5, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.6, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.7, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.8, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMinSimilarity + dataRange * 0.9, actualMinSimilarity, actualMaxSimilarity)}, 
                                                ${getViridisColor(actualMaxSimilarity, actualMinSimilarity, actualMaxSimilarity)})`
                                        }}>
                                            {/* Reference tick marks from min to max */}
                                            {(() => {
                                                const tickValues = [
                                                    actualMinSimilarity,
                                                    actualMinSimilarity + dataRange * 0.25,
                                                    actualMinSimilarity + dataRange * 0.5,
                                                    actualMinSimilarity + dataRange * 0.75,
                                                    actualMaxSimilarity
                                                ];
                                                return tickValues.map((value, index) => (
                                                    <Box
                                                        key={index}
                                                        sx={{
                                                            position: 'absolute',
                                                            left: `${(index / 4) * 100}%`,
                                                            top: 0,
                                                            bottom: 0,
                                                            width: '1px',
                                                            backgroundColor: 'rgba(0,0,0,0.4)',
                                                            '&:before': {
                                                                content: `"${value.toFixed(1)}%"`,
                                                                position: 'absolute',
                                                                bottom: '-18px',
                                                                left: '50%',
                                                                transform: 'translateX(-50%)',
                                                                fontSize: '0.65rem',
                                                                color: darkMode ? '#aaa' : 'text.secondary',
                                                                whiteSpace: 'nowrap',
                                                                fontWeight: value === actualMaxSimilarity ? 'bold' : 'normal'
                                                            }
                                                        }}
                                                    />
                                                ));
                                            })()}
                                        </Box>
                                        <Box sx={{ 
                                            display: 'flex', 
                                            alignItems: 'center', 
                                            gap: 0.5,
                                            minWidth: '60px'
                                        }}>
                                            <Typography variant="caption" sx={{ 
                                                fontSize: '0.75rem',
                                                color: darkMode ? '#aaa' : 'inherit'
                                            }}>
                                                {actualMaxSimilarity.toFixed(1)}%
                                            </Typography>
                                            <Box sx={{ 
                                                width: 16, 
                                                height: 16, 
                                                borderRadius: '50%',
                                                backgroundColor: getViridisColor(actualMaxSimilarity, actualMinSimilarity, actualMaxSimilarity),
                                                border: '2px solid',
                                                borderColor: darkMode ? '#fff' : '#000',
                                                boxShadow: '0 2px 4px rgba(0,0,0,0.3)'
                                            }} />
                                        </Box>
                                    </Box>
                                </Box>
                                
                                
                            </Box>
                        );
                    })()}

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
                        <Tooltip title="Copy similarity matrix to clipboard">
                            <IconButton 
                                size="small" 
                                onClick={() => handleCopyToClipboard(JSON.stringify(matrix, null, 2))}
                                sx={{ 
                                    backgroundColor: darkMode ? '#404040' : 'grey.100',
                                    color: darkMode ? '#ffffff' : 'inherit',
                                    '&:hover': { 
                                        backgroundColor: darkMode ? '#505050' : 'grey.200'
                                    }
                                }}
                            >
                                <ContentCopyIcon />
                            </IconButton>
                        </Tooltip>
                        <Tooltip title="Download PDF report">
                            <IconButton 
                                size="small" 
                                onClick={() => generatePDF(siteSimilarity, level)}
                                sx={{ 
                                    backgroundColor: 'error.light',
                                    color: 'error.contrastText',
                                    '&:hover': { backgroundColor: 'error.main' }
                                }}
                            >
                                <PictureAsPdfIcon />
                            </IconButton>
                        </Tooltip>
                    </Box>
                </AccordionDetails>
            </Accordion>
        );
    };

    // Helper function to get cluster info from either structure
    const getClusterInfo = (clusterResult) => {
        // Handle lightweight structure (from experiment optimization)
        if (clusterResult.cluster_summary) {
            return {
                num_clusters: clusterResult.cluster_summary.num_clusters,
                dbcv_score: clusterResult.cluster_summary.dbcv_score,
                min_cluster_size: clusterResult.cluster_summary.min_cluster_size,
                useful_attributes: Array(clusterResult.cluster_summary.useful_attributes_count).fill('attribute'),
                cluster_selection_epsilon: 0.1 // Default value for lightweight structure
            };
        }
        // Handle original structure
        else if (clusterResult.cluster_info) {
            return clusterResult.cluster_info;
        }
        return null;
    };

    // Helper function to get clusters data
    const getClustersData = (clusterResult) => {
        // For lightweight structure, clusters are stored in separate files
        if (clusterResult.clusters_file) {
            return {
                message: `Clusters data stored in separate file: ${clusterResult.clusters_file}`,
                cluster_count: clusterResult.cluster_count || 0,
                is_lightweight: true
            };
        }
        // For original structure, return the clusters array
        else if (clusterResult.clusters) {
            return clusterResult.clusters;
        }
        return null;
    };

    // Function to render timing logs
    const renderTimingLogs = (timingLogs) => {
        if (!timingLogs) return null;

        return (
            <Accordion 
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
                        backgroundColor: 'grey.100',
                        '&:hover': {
                            backgroundColor: 'grey.200',
                            color: 'text.primary',
                        },
                        '& .MuiAccordionSummary-expandIconWrapper': {
                            color: 'inherit'
                        }
                    }}
                >
                    <Typography sx={{ fontWeight: 'bold' }}>
                        ⏱️ Performance Metrics & Timing Logs
                    </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ p: 3 }}>
                    {/* Overall Performance Metrics */}
                    {timingLogs.performance_metrics && (
                        <Box sx={{ mb: theme.spacing(3) }}>
                            <Typography variant="h6" gutterBottom>📊 Overall Performance</Typography>
                            <Box sx={{ 
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                                gap: 2,
                                p: 2,
                                bgcolor: 'background.paper',
                                borderRadius: 2,
                                border: '1px solid',
                                borderColor: 'divider'
                            }}>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Total Processing Time</Typography>
                                    <Typography variant="h6" color="primary">
                                        {formatDuration(timingLogs.performance_metrics.total_processing_time)}
                                    </Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Average Time per URL</Typography>
                                    <Typography variant="h6" color="primary">
                                        {formatDuration(timingLogs.performance_metrics.average_time_per_url)}
                                    </Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Average Time per Level</Typography>
                                    <Typography variant="h6" color="primary">
                                        {formatDuration(timingLogs.performance_metrics.average_time_per_level)}
                                    </Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">URLs Processed</Typography>
                                    <Typography variant="h6" color="primary">
                                        {timingLogs.performance_metrics.urls_processed}
                                    </Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Levels Processed</Typography>
                                    <Typography variant="h6" color="primary">
                                        {timingLogs.performance_metrics.levels_processed}
                                    </Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">HTML Files Generated</Typography>
                                    <Typography variant="h6" color="primary">
                                        {timingLogs.performance_metrics.html_files_generated}
                                    </Typography>
                                </Box>
                                <Box>
                                    <Typography variant="subtitle2" color="text.secondary">Clusters Generated</Typography>
                                    <Typography variant="h6" color="primary">
                                        {timingLogs.performance_metrics.clusters_generated}
                                    </Typography>
                                </Box>
                            </Box>
                        </Box>
                    )}

                    {/* Detailed Step Timing */}
                    {timingLogs.steps && (
                        <Box sx={{ mb: theme.spacing(3) }}>
                            <Typography variant="h6" gutterBottom>🔧 Step-by-Step Timing</Typography>
                            {Object.entries(timingLogs.steps).map(([stepName, stepData]) => (
                                <Accordion 
                                    key={stepName}
                                    sx={{ 
                                        mb: theme.spacing(1),
                                        '&:before': { display: 'none' },
                                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                        borderRadius: '4px !important'
                                    }}
                                >
                                    <AccordionSummary 
                                        expandIcon={<ExpandMoreIcon />}
                                        sx={{
                                            backgroundColor: 'grey.50',
                                            '&:hover': { backgroundColor: 'grey.100' }
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                {stepData.description || stepName}
                                            </Typography>
                                            <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 'bold' }}>
                                                {formatDuration(stepData.duration)}
                                            </Typography>
                                        </Box>
                                    </AccordionSummary>
                                    <AccordionDetails sx={{ p: 2 }}>
                                        <Box sx={{ 
                                            display: 'grid',
                                            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                                            gap: 1,
                                            mb: 2
                                        }}>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">Duration</Typography>
                                                <Typography variant="body2">{formatDuration(stepData.duration)}</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">Start Time</Typography>
                                                <Typography variant="body2">{new Date(stepData.start_time * 1000).toLocaleTimeString()}</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">End Time</Typography>
                                                <Typography variant="body2">{new Date(stepData.end_time * 1000).toLocaleTimeString()}</Typography>
                                            </Box>
                                        </Box>
                                        
                                        {/* Additional step-specific data */}
                                        {stepData.urls_processed && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">URLs Processed: </Typography>
                                                <Typography variant="body2" component="span">{stepData.urls_processed}</Typography>
                                            </Box>
                                        )}
                                        {stepData.levels_processed && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">Levels Processed: </Typography>
                                                <Typography variant="body2" component="span">{stepData.levels_processed.join(', ')}</Typography>
                                            </Box>
                                        )}
                                        {stepData.data_reused && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">Data Reused: </Typography>
                                                <Typography variant="body2" component="span">✅ Yes</Typography>
                                            </Box>
                                        )}
                                        {stepData.clusters_generated && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">Clusters Generated: </Typography>
                                                <Typography variant="body2" component="span">{stepData.clusters_generated}</Typography>
                                            </Box>
                                        )}
                                        {stepData.dbcv_score && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">DBCV Score: </Typography>
                                                <Typography variant="body2" component="span">{stepData.dbcv_score.toFixed(3)}</Typography>
                                            </Box>
                                        )}
                                        {stepData.file_size_bytes && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">File Size: </Typography>
                                                <Typography variant="body2" component="span">
                                                    {stepData.file_size_mb ? `${stepData.file_size_mb.toFixed(2)} MB` : `${(stepData.file_size_bytes / 1024 / 1024).toFixed(2)} MB`}
                                                    {` (${stepData.file_size_bytes.toLocaleString()} bytes)`}
                                                </Typography>
                                            </Box>
                                        )}
                                        {stepData.computed_styles_file && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">Computed Styles File: </Typography>
                                                <Typography variant="body2" component="span">{stepData.computed_styles_file}</Typography>
                                            </Box>
                                        )}
                                        {stepData.useful_attributes_count && (
                                            <Box sx={{ mb: 1 }}>
                                                <Typography variant="caption" color="text.secondary">Useful Attributes Count: </Typography>
                                                <Typography variant="body2" component="span">{stepData.useful_attributes_count}</Typography>
                                            </Box>
                                        )}

                                        {/* Sub-steps */}
                                        {stepData.sub_steps && (
                                            <Box sx={{ mt: 2 }}>
                                                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                                    🔍 Sub-steps Details:
                                                </Typography>
                                                {Object.entries(stepData.sub_steps).map(([subStepName, subStepData]) => (
                                                    <Accordion 
                                                        key={subStepName}
                                                        sx={{ 
                                                            mb: 1,
                                                            '&:before': { display: 'none' },
                                                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                                            borderRadius: '4px !important',
                                                            bgcolor: 'background.default'
                                                        }}
                                                    >
                                                        <AccordionSummary 
                                                            expandIcon={<ExpandMoreIcon />}
                                                            sx={{
                                                                backgroundColor: 'grey.100',
                                                                minHeight: '40px',
                                                                '&:hover': { backgroundColor: 'grey.200' },
                                                                '& .MuiAccordionSummary-content': {
                                                                    margin: '8px 0'
                                                                }
                                                            }}
                                                        >
                                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                                                                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                                                    {subStepData.description || subStepName}
                                                                </Typography>
                                                                <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
                                                                    {formatDuration(subStepData.duration)}
                                                                </Typography>
                                                            </Box>
                                                        </AccordionSummary>
                                                        <AccordionDetails sx={{ p: 2, pt: 1 }}>
                                                            <Box sx={{ 
                                                                display: 'grid',
                                                                gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                                                                gap: 1,
                                                                mb: 1
                                                            }}>
                                                                <Box>
                                                                    <Typography variant="caption" color="text.secondary">Duration</Typography>
                                                                    <Typography variant="body2">{formatDuration(subStepData.duration)}</Typography>
                                                                </Box>
                                                                {subStepData.algorithm && (
                                                                    <Box>
                                                                        <Typography variant="caption" color="text.secondary">Algorithm</Typography>
                                                                        <Typography variant="body2">{subStepData.algorithm}</Typography>
                                                                    </Box>
                                                                )}
                                                                {subStepData.html_files_created && (
                                                                    <Box>
                                                                        <Typography variant="caption" color="text.secondary">HTML Files</Typography>
                                                                        <Typography variant="body2">{subStepData.html_files_created}</Typography>
                                                                    </Box>
                                                                )}
                                                                {subStepData.file_size_bytes && (
                                                                    <Box>
                                                                        <Typography variant="caption" color="text.secondary">File Size</Typography>
                                                                        <Typography variant="body2">
                                                                            {subStepData.file_size_mb ? `${subStepData.file_size_mb.toFixed(2)} MB` : `${(subStepData.file_size_bytes / 1024 / 1024).toFixed(2)} MB`}
                                                                        </Typography>
                                                                    </Box>
                                                                )}
                                                            </Box>
                                                            {subStepData.message && (
                                                                <Box sx={{ mt: 1 }}>
                                                                    <Typography variant="caption" color="text.secondary">Message: </Typography>
                                                                    <Typography variant="body2" component="span" 
                                                                        color={subStepData.success ? 'success.main' : 'text.primary'}>
                                                                        {subStepData.success ? '✅ ' : ''}{subStepData.message}
                                                                    </Typography>
                                                                </Box>
                                                            )}
                                                        </AccordionDetails>
                                                    </Accordion>
                                                ))}
                                            </Box>
                                        )}

                                        {/* Detailed timing information */}
                                        {stepData.detailed_timing && (
                                            <Box sx={{ mt: 2 }}>
                                                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                                    📊 Detailed Timing Breakdown:
                                                </Typography>
                                                {Object.entries(stepData.detailed_timing).map(([timingKey, timingData]) => (
                                                    <Box key={timingKey} sx={{ ml: 2, mb: 1 }}>
                                                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                                            {timingData.description || timingKey}:
                                                        </Typography>
                                                        <Box sx={{ ml: 1, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1 }}>
                                                            <Box>
                                                                <Typography variant="caption" color="text.secondary">Duration: </Typography>
                                                                <Typography variant="body2" component="span">{formatDuration(timingData.duration)}</Typography>
                                                            </Box>
                                                            {timingData.distinct_attributes && (
                                                                <Box>
                                                                    <Typography variant="caption" color="text.secondary">Attributes: </Typography>
                                                                    <Typography variant="body2" component="span">{timingData.distinct_attributes}</Typography>
                                                                </Box>
                                                            )}
                                                            {timingData.file_size_mb && (
                                                                <Box>
                                                                    <Typography variant="caption" color="text.secondary">Size: </Typography>
                                                                    <Typography variant="body2" component="span">{timingData.file_size_mb.toFixed(2)} MB</Typography>
                                                                </Box>
                                                            )}
                                                        </Box>
                                                    </Box>
                                                ))}
                                            </Box>
                                        )}

                                        {/* File operations details */}
                                        {stepData.file_operations && Object.keys(stepData.file_operations).length > 0 && (
                                            <Box sx={{ mt: 2 }}>
                                                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                                    📁 File Operations:
                                                </Typography>
                                                {Object.entries(stepData.file_operations).map(([opName, opData]) => (
                                                    <Box key={opName} sx={{ ml: 2, mb: 1 }}>
                                                        <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                                            {opName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                                                        </Typography>
                                                        <Box sx={{ ml: 1, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: 1 }}>
                                                            <Box>
                                                                <Typography variant="caption" color="text.secondary">Duration: </Typography>
                                                                <Typography variant="body2" component="span">{formatDuration(opData.duration)}</Typography>
                                                            </Box>
                                                            {opData.file_name && (
                                                                <Box>
                                                                    <Typography variant="caption" color="text.secondary">File: </Typography>
                                                                    <Typography variant="body2" component="span">{opData.file_name}</Typography>
                                                                </Box>
                                                            )}
                                                            {opData.file_size_mb && (
                                                                <Box>
                                                                    <Typography variant="caption" color="text.secondary">Size: </Typography>
                                                                    <Typography variant="body2" component="span">{opData.file_size_mb.toFixed(2)} MB</Typography>
                                                                </Box>
                                                            )}
                                                            {opData.processing_rate && (
                                                                <Box>
                                                                    <Typography variant="caption" color="text.secondary">Rate: </Typography>
                                                                    <Typography variant="body2" component="span">{opData.processing_rate.toFixed(0)}/sec</Typography>
                                                                </Box>
                                                            )}
                                                        </Box>
                                                    </Box>
                                                ))}
                                            </Box>
                                        )}

                                        {/* URL timing logs */}
                                        {stepData.url_timing_logs && Object.keys(stepData.url_timing_logs).length > 0 && (
                                            <Box sx={{ mt: 2 }}>
                                                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                                                    🌐 Per-URL Timing Details:
                                                </Typography>
                                                {Object.entries(stepData.url_timing_logs).map(([urlId, urlData]) => (
                                                    <Accordion 
                                                        key={urlId}
                                                        sx={{ 
                                                            mb: 1,
                                                            '&:before': { display: 'none' },
                                                            boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                                                            borderRadius: '4px !important'
                                                        }}
                                                    >
                                                        <AccordionSummary 
                                                            expandIcon={<ExpandMoreIcon />}
                                                            sx={{
                                                                backgroundColor: 'grey.100',
                                                                minHeight: '40px',
                                                                '&:hover': { backgroundColor: 'grey.200' }
                                                            }}
                                                        >
                                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', alignItems: 'center' }}>
                                                                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                                                                    🔗 URL: {urlData.url ? urlData.url.substring(0, 50) + '...' : urlId}
                                                                </Typography>
                                                                <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
                                                                    {formatDuration(urlData.total_duration)}
                                                                </Typography>
                                                            </Box>
                                                        </AccordionSummary>
                                                        <AccordionDetails sx={{ p: 2, pt: 1 }}>
                                                            {urlData.steps && Object.entries(urlData.steps).map(([stepName, stepDetail]) => (
                                                                <Box key={stepName} sx={{ mb: 1, ml: 1 }}>
                                                                    <Typography variant="caption" color="text.secondary">
                                                                        {stepDetail.description || stepName}:
                                                                    </Typography>
                                                                    <Typography variant="body2" component="span" sx={{ ml: 1 }}>
                                                                        {formatDuration(stepDetail.duration)}
                                                                    </Typography>
                                                                </Box>
                                                            ))}
                                                        </AccordionDetails>
                                                    </Accordion>
                                                ))}
                                            </Box>
                                        )}
                                    </AccordionDetails>
                                </Accordion>
                            ))}
                        </Box>
                    )}

                    {/* Cluster Info */}
                    {timingLogs.cluster_info && Object.keys(timingLogs.cluster_info).length > 0 && (
                        <Box sx={{ mb: theme.spacing(3) }}>
                            <Typography variant="h6" gutterBottom>🎯 Cluster Information</Typography>
                            {Object.entries(timingLogs.cluster_info).map(([levelKey, clusterInfo]) => (
                                <Accordion 
                                    key={levelKey}
                                    sx={{ 
                                        mb: theme.spacing(1),
                                        '&:before': { display: 'none' },
                                        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                        borderRadius: '4px !important'
                                    }}
                                >
                                    <AccordionSummary 
                                        expandIcon={<ExpandMoreIcon />}
                                        sx={{
                                            backgroundColor: 'grey.100',
                                            '&:hover': { backgroundColor: 'grey.200', color: 'text.primary' }
                                        }}
                                    >
                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                            📊 Level {clusterInfo.level || levelKey.replace('level_', '')} - {clusterInfo.num_clusters} Clusters
                                        </Typography>
                                    </AccordionSummary>
                                    <AccordionDetails sx={{ p: 2 }}>
                                        <Box sx={{ 
                                            display: 'grid',
                                            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                                            gap: 2
                                        }}>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">Number of Clusters</Typography>
                                                <Typography variant="h6">{clusterInfo.num_clusters}</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">DBCV Score</Typography>
                                                <Typography variant="h6">{clusterInfo.dbcv_score?.toFixed(3) || 'N/A'}</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">Min Cluster Size</Typography>
                                                <Typography variant="h6">{clusterInfo.min_cluster_size}</Typography>
                                            </Box>
                                            <Box>
                                                <Typography variant="caption" color="text.secondary">Epsilon</Typography>
                                                <Typography variant="h6">{clusterInfo.cluster_selection_epsilon}</Typography>
                                            </Box>
                                        </Box>
                                        {clusterInfo.useful_attributes && (
                                            <Box sx={{ mt: 2 }}>
                                                <Typography variant="subtitle2" gutterBottom>Useful Attributes:</Typography>
                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                                    {clusterInfo.useful_attributes.map((attr, i) => (
                                                        <Chip 
                                                            key={i} 
                                                            label={attr} 
                                                            size="small"
                                                            sx={{ 
                                                                bgcolor: 'primary.light',
                                                                color: 'primary.contrastText'
                                                            }}
                                                        />
                                                    ))}
                                                </Box>
                                            </Box>
                                        )}
                                    </AccordionDetails>
                                </Accordion>
                            ))}
                        </Box>
                    )}
                </AccordionDetails>
            </Accordion>
        );
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
        if (!result) return null;





        const renderUnifiedHtmlFilesSection = (resultData) => {
            // Remove this section since we'll use only the "📁 Associated HTML Files" section
            return null;
        };

        // Handle Mode 1 results (domain-based processing)
        if (result.domain_results) {
            return (
                <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1600px', mx: 'auto', px: 2 }}>
                    <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                        🌐 Domain-Based Processing Results
                    </Typography>

                    
                    {/* Site Similarity Results */}
                    <Accordion 
                        sx={{ 
                            mb: theme.spacing(2),
                            '&:before': { display: 'none', },
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            borderRadius: '8px !important',
                            backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                        }}
                    >
                        <AccordionSummary 
                            expandIcon={<ExpandMoreIcon />}
                            sx={{
                                backgroundColor: darkMode ? '#333' : 'primary.light',
                                color: darkMode ? '#ffffff' : 'inherit',
                                '&:hover': {
                                    backgroundColor: darkMode ? '#404040' : 'primary.main',
                                    color: darkMode ? '#ffffff' : 'white',
                                }
                            }}
                        >
                            <Typography sx={{ fontWeight: 'bold' }}>
                                🔍 Site Similarity Analysis
                            </Typography>
                        </AccordionSummary>
                        
                        <AccordionDetails sx={{ p: 3 }}>
                            {result.domain_results.map((domainResult, domainIndex) => (
                                domainResult.processed_clusters && domainResult.processed_clusters.map((processedCluster, clusterIndex) => (
                                    processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                    <div key={`domain-${domainIndex}-similarity-${clusterIndex}`} style={{ marginBottom: '24px' }}>
                                        <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                                            📊 {domainResult.domain} - Level {processedCluster.level}
                                        </Typography>
                                        {renderSiteSimilarityResults(
                                            processedCluster.processed_data.site_similarity, 
                                            processedCluster.level, 
                                            processedCluster.processed_data
                                        )}
                                    </div>
                                ))
                            ))}
                        </AccordionDetails>
                    </Accordion>

                    {/* Domain Results */}
                    {result.domain_results.map((domainResult, domainIndex) => (
                        <Accordion 
                            key={`domain-${domainIndex}`} 
                            sx={{ 
                                mb: theme.spacing(2),
                                '&:before': { display: 'none', },
                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                borderRadius: '8px !important',
                                backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                            }}
                        >
                            <AccordionSummary 
                                expandIcon={<ExpandMoreIcon />}
                                sx={{
                                    backgroundColor: domainResult.status === 'error' 
                                        ? 'error.light' 
                                        : (darkMode ? '#333' : 'primary.light'),
                                    color: darkMode ? '#ffffff' : 'inherit',
                                    '&:hover': {
                                        backgroundColor: domainResult.status === 'error' 
                                            ? 'error.main' 
                                            : (darkMode ? '#404040' : 'primary.main'),
                                        color: darkMode ? '#ffffff' : 'white',
                                    }
                                }}
                            >
                                <Typography sx={{ fontWeight: 'bold' }}>
                                    🌐 {domainResult.domain} ({domainResult.urls.length} URLs)
                                </Typography>
                            </AccordionSummary>
                            
                            <AccordionDetails sx={{ p: 3 }}>
                                {domainResult.status === 'error' ? (
                                    <Typography variant="body1" color="error">
                                        ❌ {domainResult.message}
                                    </Typography>
                                ) : (
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
                                                    overflow: 'hidden',
                                                    backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                                                }}
                                            >
                                                <AccordionSummary 
                                                    expandIcon={<ExpandMoreIcon />}
                                                    sx={{
                                                        backgroundColor: clusterResult.status === 'error' 
                                                            ? 'error.light' 
                                                            : (darkMode ? '#333' : 'primary.light'),
                                                        color: darkMode ? '#ffffff' : 'inherit',
                                                        '&:hover': {
                                                            backgroundColor: clusterResult.status === 'error' 
                                                                ? 'error.main' 
                                                                : (darkMode ? '#404040' : 'primary.main'),
                                                            color: darkMode ? '#ffffff' : 'white',
                                                        },
                                                        '& .MuiAccordionSummary-expandIconWrapper': {
                                                            color: 'inherit'
                                                        }
                                                    }}
                                                >
                                                    <Typography sx={{ fontWeight: 'bold' }}>
                                                        🎯 Level {clusterResult.level} Clustering
                                                        {clusterResult.status === 'error' && ' (Error)'}
                                                    </Typography>
                                                </AccordionSummary>
                                                
                                                <AccordionDetails sx={{ p: 3 }}>
                                                    {clusterResult.status === 'error' ? (
                                                        <Typography variant="body1" color="error">
                                                            ❌ {clusterResult.message}
                                                        </Typography>
                                                    ) : (
                                                        <>
                                                            {/* Cluster Info Section */}
                                                            {(() => {
                                                                const clusterInfo = getClusterInfo(clusterResult);
                                                                if (!clusterInfo) return null;
                                                                
                                                                return (
                                                                    <Box sx={{ mb: theme.spacing(2) }}>
                                                                        <Typography variant="h6" gutterBottom sx={{
                                                                            color: darkMode ? '#ffffff' : 'inherit'
                                                                        }}>
                                                                            📊 Cluster Information
                                                                        </Typography>
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
                                                                                    {clusterInfo.num_clusters}
                                                                                </Typography>

                                                                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                                                    DBCV Score:
                                                                                </Typography>
                                                                                <Typography variant="subtitle1">
                                                                                    {clusterInfo.dbcv_score?.toFixed(3) || 'N/A'}
                                                                                </Typography>

                                                                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                                                    Min Cluster Size:
                                                                                </Typography>
                                                                                <Typography variant="subtitle1">
                                                                                    {clusterInfo.min_cluster_size}
                                                                                </Typography>

                                                                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                                                    Epsilon:
                                                                                </Typography>
                                                                                <Typography variant="subtitle1">
                                                                                    {clusterInfo.cluster_selection_epsilon}
                                                                                </Typography>

                                                                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                                                    Useful Attributes:
                                                                                </Typography>
                                                                                <Typography variant="subtitle1">
                                                                                    {clusterInfo.useful_attributes?.length || 0}
                                                                                </Typography>
                                                                            </Box>
                                                                        </Box>
                                                                    </Box>
                                                                );
                                                            })()}

                                                            {/* Clusters Data Section */}
                                                            {(() => {
                                                                const clustersData = getClustersData(clusterResult);
                                                                if (!clustersData) return null;
                                                                
                                                                return (
                                                                    <Box sx={{ mb: theme.spacing(2) }}>
                                                                        <Typography variant="h6" gutterBottom sx={{
                                                                            color: darkMode ? '#ffffff' : 'inherit'
                                                                        }}>
                                                                            🎯 Clusters
                                                                        </Typography>
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
                                                                                value={clustersData.is_lightweight ? 
                                                                                    clustersData.message : 
                                                                                    JSON.stringify(clustersData, null, 1)
                                                                                }
                                                                                readOnly
                                                                            />
                                                                        </Box>
                                                                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1, gap: 1 }}>
                                                                            <Tooltip title="Copy clusters data to clipboard">
                                                                                <IconButton 
                                                                                    size="small" 
                                                                                    onClick={() => handleCopyToClipboard(
                                                                                        clustersData.is_lightweight ? 
                                                                                        clustersData.message : 
                                                                                        JSON.stringify(clustersData, null, 1)
                                                                                    )}
                                                                                    sx={{
                                                                                        backgroundColor: darkMode ? '#404040' : 'grey.100',
                                                                                        color: darkMode ? '#ffffff' : 'inherit',
                                                                                        '&:hover': { 
                                                                                            backgroundColor: darkMode ? '#505050' : 'grey.200'
                                                                                        }
                                                                                    }}
                                                                                >
                                                                                    <ContentCopyIcon />
                                                                                </IconButton>
                                                                            </Tooltip>
                                                                            <Tooltip title="Copy complete clustering analysis for this domain level">
                                                                                <Button
                                                                                    variant="outlined"
                                                                                    size="small"
                                                                                    onClick={() => {
                                                                                        const clusterInfo = getClusterInfo(clusterResult);
                                                                                        const completeAnalysis = {
                                                                                            domain: domainResult.domain,
                                                                                            level: clusterResult.level,
                                                                                            status: clusterResult.status,
                                                                                            message: clusterResult.message,
                                                                                            cluster_info: clusterInfo,
                                                                                            clusters_data: clustersData,
                                                                                            is_lightweight: clustersData?.is_lightweight || false,
                                                                                            timestamp: new Date().toISOString()
                                                                                        };
                                                                                        handleCopyToClipboard(JSON.stringify(completeAnalysis, null, 2));
                                                                                        setSuccess(`📋 ${domainResult.domain} Level ${clusterResult.level} clustering analysis copied!`);
                                                                                    }}
                                                                                    sx={{
                                                                                        fontSize: '0.75rem',
                                                                                        ...(darkMode && {
                                                                                            borderColor: '#555',
                                                                                            color: '#fff',
                                                                                            '&:hover': {
                                                                                                borderColor: '#777',
                                                                                                backgroundColor: 'rgba(255,255,255,0.1)'
                                                                                            }
                                                                                        })
                                                                                    }}
                                                                                >
                                                                                    📊 Copy Domain Analysis
                                                                                </Button>
                                                                            </Tooltip>
                                                                            {clustersData.is_lightweight && (
                                                                                <Tooltip title="Load full clustering data from separate file">
                                                                                    <Button
                                                                                        variant="outlined"
                                                                                        size="small"
                                                                                        onClick={async () => {
                                                                                            const testId = result.test_metadata?.test_id;
                                                                                            if (testId && selectedExperiment?.id) {
                                                                                                const fullData = await loadLargeDataClusteringResults(selectedExperiment.id, testId);
                                                                                                if (fullData) {
                                                                                                    // Find the specific cluster result and update it
                                                                                                    const clusterIndex = result.clustering_results.findIndex(cr => cr.level === clusterResult.level);
                                                                                                    if (clusterIndex !== -1) {
                                                                                                        // Update the result with full data
                                                                                                        const updatedResult = { ...result };
                                                                                                        updatedResult.clustering_results[clusterIndex] = fullData[clusterIndex];
                                                                                                        setResult(updatedResult);
                                                                                                        setSuccess('Full clustering data loaded successfully!');
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }}
                                                                                        sx={{
                                                                                            fontSize: '0.75rem',
                                                                                            ...(darkMode && {
                                                                                                borderColor: '#555',
                                                                                                color: '#fff',
                                                                                                '&:hover': {
                                                                                                    borderColor: '#777',
                                                                                                    backgroundColor: 'rgba(255,255,255,0.1)'
                                                                                                }
                                                                                            })
                                                                                        }}
                                                                                    >
                                                                                        📥 Load Full Data
                                                                                    </Button>
                                                                                </Tooltip>
                                                                            )}
                                                                        </Box>
                                                                    </Box>
                                                                );
                                                            })()}
                                                        </>
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
                                                    '&:before': { display: 'none', },
                                                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                                    borderRadius: '8px !important',
                                                    backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                                                }}
                                            >
                                                <AccordionSummary 
                                                    expandIcon={<ExpandMoreIcon />}
                                                    sx={{
                                                        backgroundColor: darkMode ? '#333' : 'grey.200',
                                                        color: darkMode ? '#ffffff' : 'inherit',
                                                        '&:hover': {
                                                            backgroundColor: darkMode ? '#404040' : 'grey.300',
                                                            color: darkMode ? '#ffffff' : 'text.primary',
                                                        }
                                                    }}
                                                >
                                                    <Typography sx={{ fontWeight: 'bold' }}>
                                                        ⚙️ Processed Cluster Level {processedCluster.level}
                                                    </Typography>
                                                </AccordionSummary>
                                                
                                                <AccordionDetails sx={{ p: 3 }}>
                                                    {processedCluster.processed_data && processedCluster.processed_data.sites && (
                                                        <Box sx={{ mb: theme.spacing(2) }}>
                                                            <Typography variant="h6" gutterBottom sx={{
                                                                color: darkMode ? '#ffffff' : 'inherit'
                                                            }}>
                                                                📊 Sites Data
                                                            </Typography>
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
                                                    )}

                                                    {/* Timing Logs Section for Processed Clusters */}
                                                    {processedCluster.timing_logs && renderTimingLogs(processedCluster.timing_logs)}
                                                </AccordionDetails>
                                            </Accordion>
                                        ))}
                                    </>
                                )}
                            </AccordionDetails>
                        </Accordion>
                    ))}

                    {/* Timing Logs Section for Regular Results */}
                    {result.timing_logs && renderTimingLogs(result.timing_logs)}


                </Box>
            );
        }

        // Original results rendering (mode 0)
        return (
            <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1600px', mx: 'auto', px: 2 }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                    🧮 Clustering Results
                </Typography>

                
                {/* Site Similarity Results by Level */}
                {result.processed_clusters && result.processed_clusters.map((processedCluster, clusterIndex) => (
                    processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                    <div key={`similarity-${clusterIndex}`}>
                        {renderSiteSimilarityResults(
                            processedCluster.processed_data.site_similarity, 
                            processedCluster.level, 
                            processedCluster.processed_data
                        )}
                    </div>
                ))}

                
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
                            overflow: 'hidden',
                            backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                        }}
                    >
                        <AccordionSummary 
                            expandIcon={<ExpandMoreIcon />}
                            sx={{
                                backgroundColor: clusterResult.status === 'error' 
                                    ? 'error.light' 
                                    : (darkMode ? '#333' : 'primary.light'),
                                color: darkMode ? '#ffffff' : 'inherit',
                                '&:hover': {
                                    backgroundColor: clusterResult.status === 'error' 
                                        ? 'error.main' 
                                        : (darkMode ? '#404040' : 'primary.main'),
                                    color: darkMode ? '#ffffff' : 'white',
                                },
                                '& .MuiAccordionSummary-expandIconWrapper': {
                                    color: 'inherit'
                                }
                            }}
                        >
                            <Typography sx={{ fontWeight: 'bold' }}>
                                🎯 Level {clusterResult.level} Clustering
                                {clusterResult.status === 'error' && ' (Error)'}
                            </Typography>
                        </AccordionSummary>
                        
                        <AccordionDetails sx={{ p: 3 }}>
                            {clusterResult.status === 'error' ? (
                                <Typography variant="body1" color="error">
                                    ❌ {clusterResult.message}
                                </Typography>
                            ) : (
                                <>
                                    {/* Cluster Info Section */}
                                    {(() => {
                                        const clusterInfo = getClusterInfo(clusterResult);
                                        if (!clusterInfo) return null;
                                        
                                        return (
                                            <Box sx={{ mb: theme.spacing(2) }}>
                                                <Typography variant="h6" gutterBottom sx={{
                                                    color: darkMode ? '#ffffff' : 'inherit'
                                                }}>
                                                    📊 Cluster Information
                                                </Typography>
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
                                                            {clusterInfo.num_clusters}
                                                        </Typography>

                                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                            DBCV Score:
                                                        </Typography>
                                                        <Typography variant="subtitle1">
                                                            {clusterInfo.dbcv_score?.toFixed(3) || 'N/A'}
                                                        </Typography>

                                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                            Min Cluster Size:
                                                        </Typography>
                                                        <Typography variant="subtitle1">
                                                            {clusterInfo.min_cluster_size}
                                                        </Typography>

                                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                            Epsilon:
                                                        </Typography>
                                                        <Typography variant="subtitle1">
                                                            {clusterInfo.cluster_selection_epsilon}
                                                        </Typography>

                                                        <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                                            Useful Attributes:
                                                        </Typography>
                                                        <Typography variant="subtitle1">
                                                            {clusterInfo.useful_attributes?.length || 0}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                            </Box>
                                        );
                                    })()}

                                    {/* Clusters Data Section */}
                                    {(() => {
                                        const clustersData = getClustersData(clusterResult);
                                        if (!clustersData) return null;
                                        
                                        return (
                                            <Box sx={{ mb: theme.spacing(2) }}>
                                                <Typography variant="h6" gutterBottom sx={{
                                                    color: darkMode ? '#ffffff' : 'inherit'
                                                }}>
                                                    🎯 Clusters
                                                </Typography>
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
                                                        value={clustersData.is_lightweight ? 
                                                            clustersData.message : 
                                                            JSON.stringify(clustersData, null, 1)
                                                        }
                                                        readOnly
                                                    />
                                                </Box>
                                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 1, gap: 1 }}>
                                                    <Tooltip title="Copy clusters data to clipboard">
                                                        <IconButton 
                                                            size="small" 
                                                            onClick={() => handleCopyToClipboard(
                                                                clustersData.is_lightweight ? 
                                                                clustersData.message : 
                                                                JSON.stringify(clustersData, null, 1)
                                                            )}
                                                            sx={{
                                                                backgroundColor: darkMode ? '#404040' : 'grey.100',
                                                                color: darkMode ? '#ffffff' : 'inherit',
                                                                '&:hover': { 
                                                                    backgroundColor: darkMode ? '#505050' : 'grey.200'
                                                                }
                                                            }}
                                                        >
                                                            <ContentCopyIcon />
                                                        </IconButton>
                                                    </Tooltip>
                                                    <Tooltip title="Copy complete clustering analysis for this level">
                                                        <Button
                                                            variant="outlined"
                                                            size="small"
                                                            onClick={() => {
                                                                const clusterInfo = getClusterInfo(clusterResult);
                                                                const completeAnalysis = {
                                                                    level: clusterResult.level,
                                                                    status: clusterResult.status,
                                                                    message: clusterResult.message,
                                                                    cluster_info: clusterInfo,
                                                                    clusters_data: clustersData,
                                                                    is_lightweight: clustersData?.is_lightweight || false,
                                                                    timestamp: new Date().toISOString()
                                                                };
                                                                handleCopyToClipboard(JSON.stringify(completeAnalysis, null, 2));
                                                                setSuccess(`📋 Level ${clusterResult.level} clustering analysis copied!`);
                                                            }}
                                                            sx={{
                                                                fontSize: '0.75rem',
                                                                ...(darkMode && {
                                                                    borderColor: '#555',
                                                                    color: '#fff',
                                                                    '&:hover': {
                                                                        borderColor: '#777',
                                                                        backgroundColor: 'rgba(255,255,255,0.1)'
                                                                    }
                                                                })
                                                            }}
                                                        >
                                                            📊 Copy Analysis
                                                        </Button>
                                                    </Tooltip>
                                                    {clustersData.is_lightweight && (
                                                        <Tooltip title="Load full clustering data from separate file">
                                                            <Button
                                                                variant="outlined"
                                                                size="small"
                                                                onClick={async () => {
                                                                    const testId = result.test_metadata?.test_id;
                                                                    if (testId && selectedExperiment?.id) {
                                                                        const fullData = await loadLargeDataClusteringResults(selectedExperiment.id, testId);
                                                                        if (fullData) {
                                                                            // Find the specific cluster result and update it
                                                                            const clusterIndex = result.clustering_results.findIndex(cr => cr.level === clusterResult.level);
                                                                            if (clusterIndex !== -1) {
                                                                                // Update the result with full data
                                                                                const updatedResult = { ...result };
                                                                                updatedResult.clustering_results[clusterIndex] = fullData[clusterIndex];
                                                                                setResult(updatedResult);
                                                                                setSuccess('Full clustering data loaded successfully!');
                                                                            }
                                                                        }
                                                                    }
                                                                }}
                                                                sx={{
                                                                    fontSize: '0.75rem',
                                                                    ...(darkMode && {
                                                                        borderColor: '#555',
                                                                        color: '#fff',
                                                                        '&:hover': {
                                                                            borderColor: '#777',
                                                                            backgroundColor: 'rgba(255,255,255,0.1)'
                                                                        }
                                                                    })
                                                                }}
                                                            >
                                                                📥 Load Full Data
                                                            </Button>
                                                        </Tooltip>
                                                    )}
                                                </Box>
                                            </Box>
                                        );
                                    })()}
                                </>
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
                            '&:before': { display: 'none', },
                            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                            borderRadius: '8px !important',
                            backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                        }}
                    >
                        <AccordionSummary 
                            expandIcon={<ExpandMoreIcon />}
                            sx={{
                                backgroundColor: darkMode ? '#333' : 'grey.200',
                                color: darkMode ? '#ffffff' : 'inherit',
                                '&:hover': {
                                    backgroundColor: darkMode ? '#404040' : 'grey.300',
                                    color: darkMode ? '#ffffff' : 'text.primary',
                                },
                                '& .MuiAccordionSummary-expandIconWrapper': {
                                    color: 'inherit'
                                }
                            }}
                        >
                            <Typography sx={{ fontWeight: 'bold' }}>
                                ⚙️ Processed Cluster Level {processedCluster.level}
                            </Typography>
                        </AccordionSummary>
                        
                        <AccordionDetails sx={{ p: 3 }}>
                            {processedCluster.processed_data && processedCluster.processed_data.sites && (
                                <Box sx={{ mb: theme.spacing(2) }}>
                                    <Typography variant="h6" gutterBottom sx={{
                                        color: darkMode ? '#ffffff' : 'inherit'
                                    }}>
                                        📊 Sites Data
                                    </Typography>
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
                            )}

                            {/* Timing Logs Section for Processed Clusters */}
                            {processedCluster.timing_logs && renderTimingLogs(processedCluster.timing_logs)}
                        </AccordionDetails>
                    </Accordion>
                ))}

                {/* Timing Logs Section for Regular Results */}
                {result.timing_logs && renderTimingLogs(result.timing_logs)}


            </Box>
        );
    };

    const renderContent = () => {
        switch (currentView) {
            case 'home':
                return (
                    <FormControl fullWidth>
                        <Box sx={{ maxWidth: '1400px', mx: 'auto', px: 3 }}>
                            <TextField
                                label="Paste your URLs"
                                placeholder="Paste URLs and press Enter (supports multiple URLs)"
                                value={inputValue}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyDown}
                                onPaste={handlePaste}
                                fullWidth
                                variant="outlined"
                                multiline
                                maxRows={4}
                                helperText="💡 Paste multiple URLs separated by newlines or spaces"
                                sx={{
                                    ...(darkMode && {
                                        '& .MuiOutlinedInput-root': {
                                            backgroundColor: '#2a2a2a',
                                            '& fieldset': {
                                                borderColor: '#555',
                                            },
                                            '&:hover fieldset': {
                                                borderColor: '#777',
                                            },
                                            '&.Mui-focused fieldset': {
                                                borderColor: '#1976d2',
                                            },
                                        },
                                        '& .MuiInputLabel-root': {
                                            color: '#ccc',
                                        },
                                        '& .MuiFormHelperText-root': {
                                            color: '#aaa',
                                        },
                                        '& .MuiOutlinedInput-input': {
                                            color: '#fff',
                                        }
                                    })
                                }}
                            />
                        </Box>
                        <Box sx={{ position: 'relative', maxWidth: '1400px', mx: 'auto', px: 3, mt: theme.spacing(2), display: 'flex', justifyContent: 'center' }}>
                            <Box sx={{ 
                                position: 'absolute', 
                                top: '-10px', 
                                left: '23px', 
                                backgroundColor: darkMode ? '#121212' : 'white', 
                                color: darkMode ? '#ffffff' : 'inherit',
                                padding: '0 5px', 
                                fontWeight: 'bold', 
                                zIndex: 10 
                            }}>📊 Levels</Box>
                            <Box sx={{ 
                                border: '1px solid', 
                                borderColor: darkMode ? '#555' : 'grey.400', 
                                borderRadius: '8px', 
                                padding: theme.spacing(2), 
                                display: 'flex', 
                                flexWrap: 'wrap', 
                                justifyContent: 'center', 
                                gap: theme.spacing(1), 
                                width: '100%',
                                backgroundColor: darkMode ? '#1e1e1e' : 'transparent'
                            }}>
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
                        <Box sx={{ maxWidth: '1400px', mx: 'auto', px: 3, mt: theme.spacing(2), display: 'flex', justifyContent: 'center' }}>
                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={isNewMode}
                                        onChange={(e) => setIsNewMode(e.target.checked)}
                                        color="primary"
                                    />
                                }
                                label={isNewMode ? "🌐 Process by Domain" : "📦 Process All Together"}
                            />
                        </Box>

                        {/* URL Cards */}
                        <Box sx={{ 
                            maxWidth: '1400px', 
                            mx: 'auto',
                            px: 3,
                            mt: theme.spacing(2),
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                            gap: 3
                        }}>
                            {sortedDomains.map(domain => (
                                <Card key={domain} sx={{ 
                                    height: '100%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    transition: 'transform 0.2s, box-shadow 0.2s',
                                    '&:hover': {
                                        transform: 'translateY(-4px)',
                                        boxShadow: darkMode ? '0 8px 16px rgba(0,0,0,0.3)' : '0 8px 16px rgba(0,0,0,0.1)',
                                    },
                                    boxShadow: darkMode ? '0 4px 8px rgba(0,0,0,0.2)' : '0 4px 8px rgba(0,0,0,0.05)',
                                    borderRadius: 2,
                                    border: '1px solid',
                                    borderColor: darkMode ? '#555' : 'divider',
                                    bgcolor: darkMode ? '#2a2a2a' : 'background.paper',
                                    color: darkMode ? '#ffffff' : 'inherit'
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
                                            bgcolor: darkMode ? '#1976d2' : 'primary.main',
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
                                        ⏹️ Cancel
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
                                        ▶️ Run
                                    </Button>
                                    <Button
                                        variant="contained"
                                        color="secondary"
                                        onClick={handleClear}
                                        sx={{ borderRadius: '20px' }}
                                        disabled={urls.length === 0}
                                    >
                                        🗑️ Clear
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
                    <Box sx={{ width: '100%', maxWidth: '1400px', mx: 'auto', px: 3 }}>
                        <textarea
                            rows={10}
                            placeholder="Paste your cluster results here"
                            style={{ 
                                width: '100%', 
                                padding: '15px', 
                                boxSizing: 'border-box', 
                                minHeight: '300px', 
                                fontSize: '14px', 
                                fontFamily: 'monospace', 
                                border: darkMode ? '2px solid #555' : '2px solid #ddd', 
                                borderRadius: '8px',
                                backgroundColor: darkMode ? '#2a2a2a' : 'white',
                                color: darkMode ? '#ffffff' : 'inherit'
                            }}
                            value={clusterInput}
                            onChange={(e) => setClusterInput(e.target.value)}
                        />
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: theme.spacing(3) }}>
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleClusterRun}
                                sx={{ borderRadius: '20px', px: 4, py: 1.5 }}
                                disabled={clusterInput.trim() === ''}
                            >
                                ▶️ Run Clustering
                            </Button>
                        </Box>
                    </Box>
                );
            case 'config':
                return (
                    <Box sx={{ width: '100%', maxWidth: '1600px', mx: 'auto', px: 3, py: 2 }}>
                        <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
                            ⚙️ Experiment Configuration Builder
                        </Typography>



                        {/* 1. Basic Configuration */}
                        <Card sx={{ mb: 3, backgroundColor: darkMode ? '#2a2a2a' : 'background.paper' }}>
                            <CardHeader 
                                title="1️⃣ Basic Configuration"
                                sx={{
                                    backgroundColor: darkMode ? '#333' : 'primary.light',
                                    color: darkMode ? '#ffffff' : 'white'
                                }}
                            />
                            <CardContent sx={{ p: 3 }}>
                                <TextField
                                    fullWidth
                                    label="Experiment Name"
                                    value={customConfig.experiment_name}
                                    onChange={(e) => setCustomConfig(prev => ({ ...prev, experiment_name: e.target.value }))}
                                    placeholder="e.g., Website Similarity Analysis - Thesis 2024"
                                    sx={{
                                        mb: 2,
                                        ...(darkMode && {
                                            '& .MuiOutlinedInput-root': {
                                                backgroundColor: '#333',
                                                '& fieldset': { borderColor: '#555' },
                                                '&:hover fieldset': { borderColor: '#777' },
                                                '&.Mui-focused fieldset': { borderColor: '#1976d2' },
                                            },
                                            '& .MuiInputLabel-root': { color: '#ccc' },
                                            '& .MuiOutlinedInput-input': { color: '#fff' }
                                        })
                                    }}
                                />
                            </CardContent>
                        </Card>

                        {/* 2. URL Management */}
                        <Card sx={{ mb: 3, backgroundColor: darkMode ? '#2a2a2a' : 'background.paper' }}>
                            <CardHeader 
                                title="2️⃣ URL Management"
                                subheader={`${customConfig.available_urls.length} URLs added across ${
                                    customConfig.available_urls.length > 0 
                                        ? [...new Set(customConfig.available_urls.map(url => {
                                            try { return new URL(url).hostname; } catch { return 'invalid'; }
                                        }))].length 
                                        : 0
                                } domains`}
                                sx={{
                                    backgroundColor: darkMode ? '#333' : 'secondary.light',
                                    color: darkMode ? '#ffffff' : 'white',
                                    '& .MuiCardHeader-subheader': {
                                        color: darkMode ? '#aaa' : 'rgba(255,255,255,0.8)'
                                    }
                                }}
                            />
                            <CardContent sx={{ p: 3 }}>
                                {/* URL Input */}
                                <Box sx={{ mb: 3 }}>
                                    <Typography variant="h6" gutterBottom sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                        🌐 Add URLs
                                    </Typography>
                                    <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                                        <TextField
                                            fullWidth
                                            label="Add URL(s)"
                                            value={configUrlInput}
                                            onChange={(e) => setConfigUrlInput(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && addConfigUrl()}
                                            onPaste={handleConfigUrlPaste}
                                            placeholder="https://example.com (or paste multiple URLs)"
                                            multiline
                                            maxRows={4}
                                            helperText="💡 Paste multiple URLs separated by newlines or spaces"
                                            sx={{
                                                ...(darkMode && {
                                                    '& .MuiOutlinedInput-root': {
                                                        backgroundColor: '#333',
                                                        '& fieldset': { borderColor: '#555' },
                                                        '&:hover fieldset': { borderColor: '#777' },
                                                        '&.Mui-focused fieldset': { borderColor: '#1976d2' },
                                                    },
                                                    '& .MuiInputLabel-root': { color: '#ccc' },
                                                    '& .MuiFormHelperText-root': { color: '#aaa' },
                                                    '& .MuiOutlinedInput-input': { color: '#fff' }
                                                })
                                            }}
                                        />
                                        <Button 
                                            variant="contained" 
                                            onClick={addConfigUrl}
                                            sx={{ minWidth: '100px', height: 'fit-content', mt: 1 }}
                                        >
                                            Add
                                        </Button>
                                    </Box>
                                </Box>

                                {/* URL Display by Domain */}
                                {customConfig.available_urls.length > 0 && (
                                    <Box>
                                        <Typography variant="h6" gutterBottom sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                            📁 URLs by Domain
                                        </Typography>
                                        {(() => {
                                            const domainGroups = customConfig.available_urls.reduce((acc, url, index) => {
                                                try {
                                                    const domain = new URL(url).hostname;
                                                    if (!acc[domain]) acc[domain] = [];
                                                    acc[domain].push({ url, index });
                                                    return acc;
                                                } catch {
                                                    if (!acc['invalid']) acc['invalid'] = [];
                                                    acc['invalid'].push({ url, index });
                                                    return acc;
                                                }
                                            }, {});
                                            
                                            return Object.entries(domainGroups).map(([domain, urlsData]) => (
                                                <Accordion key={domain} sx={{ mb: 1, backgroundColor: darkMode ? '#333' : 'grey.50' }}>
                                                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                                        <Typography sx={{ fontWeight: 'bold', color: darkMode ? '#ffffff' : 'inherit' }}>
                                                            🌐 {domain} ({urlsData.length} URLs)
                                                        </Typography>
                                                    </AccordionSummary>
                                                    <AccordionDetails>
                                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                                            {urlsData.map(({ url, index }) => (
                                                                <Chip
                                                                    key={index}
                                                                    label={url}
                                                                    onDelete={() => removeConfigUrl(index)}
                                                                    color="primary"
                                                                    sx={{ maxWidth: '300px' }}
                                                                />
                                                            ))}
                                                        </Box>
                                                    </AccordionDetails>
                                                </Accordion>
                                            ));
                                        })()}
                                    </Box>
                                )}
                            </CardContent>
                        </Card>

                        {/* 3. Experiment Configuration */}
                        <Card sx={{ mb: 3, backgroundColor: darkMode ? '#2a2a2a' : 'background.paper' }}>
                            <CardHeader 
                                title="3️⃣ Experiment Parameters"
                                sx={{
                                    backgroundColor: darkMode ? '#333' : 'success.light',
                                    color: darkMode ? '#ffffff' : 'white'
                                }}
                            />
                            <CardContent sx={{ p: 3 }}>
                                <Grid container spacing={4}>
                                    {/* DOM Levels */}
                                    <Grid item xs={12}>
                                        <Typography variant="h6" gutterBottom sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                            📊 DOM Levels
                                        </Typography>
                                        <Box sx={{ 
                                            p: 2, 
                                            border: '1px solid', 
                                            borderColor: darkMode ? '#555' : 'divider', 
                                            borderRadius: 2,
                                            backgroundColor: darkMode ? '#333' : 'grey.50'
                                        }}>
                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                                {Array.from({ length: 10 }, (_, i) => i + 1).map(level => (
                                                    <Chip
                                                        key={level}
                                                        label={level}
                                                        onClick={() => {
                                                            const newLevels = customConfig.levels.includes(level)
                                                                ? customConfig.levels.filter(l => l !== level)
                                                                : [...customConfig.levels, level].sort((a, b) => a - b);
                                                            setCustomConfig(prev => ({ ...prev, levels: newLevels }));
                                                        }}
                                                        color={customConfig.levels.includes(level) ? 'primary' : 'default'}
                                                        sx={{ 
                                                            minWidth: '40px',
                                                            ...(darkMode && !customConfig.levels.includes(level) && {
                                                                backgroundColor: '#555',
                                                                color: '#ccc',
                                                                '&:hover': {
                                                                    backgroundColor: '#666'
                                                                }
                                                            })
                                                        }}
                                                    />
                                                ))}
                                            </Box>
                                            <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>
                                                Selected levels: {customConfig.levels.join(', ') || 'None'}
                                            </Typography>
                                        </Box>
                                    </Grid>

                                    {/* URLs per Domain */}
                                    <Grid item xs={12}>
                                        <Typography variant="h6" gutterBottom sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                            🔢 URLs per Domain Configuration
                                        </Typography>
                                        
                                        <Box sx={{ 
                                            p: 2, 
                                            border: '1px solid', 
                                            borderColor: darkMode ? '#555' : 'divider', 
                                            borderRadius: 2,
                                            backgroundColor: darkMode ? '#333' : 'grey.50'
                                        }}>
                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                                {Array.from({ length: 10 }, (_, i) => i + 1).map(count => {
                                                    // Calculate minimum URLs per domain from available URLs
                                                    const domainGroups = customConfig.available_urls.reduce((acc, url) => {
                                                        try {
                                                            const domain = new URL(url).hostname;
                                                            if (!acc[domain]) acc[domain] = [];
                                                            acc[domain].push(url);
                                                            return acc;
                                                        } catch {
                                                            return acc;
                                                        }
                                                    }, {});
                                                    
                                                    const minUrlsPerDomain = Object.keys(domainGroups).length > 0 
                                                        ? Math.min(...Object.values(domainGroups).map(urls => urls.length))
                                                        : 0;
                                                    
                                                    return (
                                                        <Chip
                                                            key={count}
                                                            label={count}
                                                            onClick={() => {
                                                                const newCombinations = customConfig.url_combinations.includes(count)
                                                                    ? customConfig.url_combinations.filter(c => c !== count)
                                                                    : [...customConfig.url_combinations, count].sort((a, b) => a - b);
                                                                setCustomConfig(prev => ({ ...prev, url_combinations: newCombinations }));
                                                            }}
                                                            color={customConfig.url_combinations.includes(count) ? 'primary' : 'default'}
                                                            disabled={count > minUrlsPerDomain}
                                                            sx={{
                                                                minWidth: '40px',
                                                                ...(darkMode && !customConfig.url_combinations.includes(count) && !count > minUrlsPerDomain && {
                                                                    backgroundColor: '#555',
                                                                    color: '#ccc',
                                                                    '&:hover': {
                                                                        backgroundColor: '#666'
                                                                    }
                                                                })
                                                            }}
                                                        />
                                                    );
                                                })}
                                            </Box>
                                            <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>
                                                Selected: {customConfig.url_combinations.join(', ') || 'None'} URLs per domain (from each domain)
                                            </Typography>
                                        </Box>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>

                        {/* Launch Experiment Button */}
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, mb: 3 }}>
                            <Button
                                variant="contained"
                                color="primary"
                                size="large"
                                onClick={runCustomExperiment}
                                disabled={
                                    experimentLoading || 
                                    customConfig.available_urls.length === 0 || 
                                    customConfig.levels.length === 0 ||
                                    customConfig.url_combinations.length === 0
                                }
                                sx={{ 
                                    borderRadius: '25px',
                                    px: 6,
                                    py: 2,
                                    fontSize: '1.2rem',
                                    fontWeight: 'bold',
                                    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                                    '&:hover': {
                                        transform: 'translateY(-2px)',
                                        boxShadow: '0 6px 20px rgba(0,0,0,0.3)'
                                    },
                                    transition: 'all 0.3s ease-in-out'
                                }}
                            >
                                {experimentLoading ? (
                                    <>
                                        <CircularProgress size={24} sx={{ mr: 2, color: 'white' }} />
                                        Running Experiment...
                                    </>
                                ) : (
                                    <>
                                        🚀 Launch Experiment
                                    </>
                                )}
                            </Button>
                        </Box>

                        {/* Experiment Results Display */}
                        {experimentResults && (
                            <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1600px', mx: 'auto', px: 2 }}>
                                {/* Experiment Summary */}
                                <Card sx={{ mb: 3 }}>
                                    <CardHeader title="📊 Experiment Summary" />
                                    <CardContent>
                                        <Grid container spacing={3}>
                                            <Grid item xs={12} md={6}>
                                                <Typography variant="h6" gutterBottom>📈 Performance Overview</Typography>
                                                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Total Tests</Typography>
                                                        <Typography variant="h6">{experimentResults.experiment_info.total_tests}</Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Success Rate</Typography>
                                                        <Typography variant="h6" color="success.main">
                                                            {experimentResults.experiment_info.success_rate.toFixed(1)}%
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Successful</Typography>
                                                        <Typography variant="h6" color="success.main">
                                                            {experimentResults.experiment_info.successful_tests}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Failed</Typography>
                                                        <Typography variant="h6" color="error.main">
                                                            {experimentResults.experiment_info.failed_tests}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Duration</Typography>
                                                        <Typography variant="h6">
                                                            {formatDuration(experimentResults.experiment_info.duration)}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                            </Grid>
                                        </Grid>
                                    </CardContent>
                                </Card>

                                {/* Process each result */}
                                {experimentResults.results && experimentResults.results.map((result, index) => {
                                    const cardId = `config-result-${index}`;
                                    const collapsed = isCardCollapsed(cardId);
                                    
                                    return result.status === 'success' && (
                                        <Card key={index} sx={{ 
                                            mb: 4, 
                                            border: '2px solid',
                                            borderColor: 'success.light',
                                            borderRadius: 3,
                                            overflow: 'hidden',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                            backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                                        }}>
                                            <CardHeader 
                                                title={
                                                    <Typography variant="h5" sx={{ 
                                                        fontWeight: 'bold',
                                                        color: 'white',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: 1
                                                    }}>
                                                        🧮 Test: {result.test_metadata?.test_name || `Test ${index + 1}`}
                                                    </Typography>
                                                }
                                                subheader={
                                                    <Typography variant="subtitle1" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                                                        ID: {result.test_metadata?.test_id} | Duration: {formatDuration(result.test_metadata?.duration || 0)}
                                                    </Typography>
                                                }
                                                action={
                                                    <Tooltip title={collapsed ? "Expand card" : "Collapse card"}>
                                                        <IconButton
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                toggleCardCollapse(cardId);
                                                            }}
                                                            sx={{
                                                                color: 'white',
                                                                '&:hover': {
                                                                    backgroundColor: 'rgba(255,255,255,0.1)'
                                                                }
                                                            }}
                                                        >
                                                            {collapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
                                                        </IconButton>
                                                    </Tooltip>
                                                }
                                                onClick={() => toggleCardCollapse(cardId)}
                                                sx={{
                                                    backgroundColor: 'success.main',
                                                    color: 'white',
                                                    py: 2,
                                                    cursor: 'pointer',
                                                    '&:hover': {
                                                        backgroundColor: 'success.dark'
                                                    }
                                                }}
                                            />
                                            <Collapse in={!collapsed} timeout="auto" unmountOnExit>
                                                                                            <CardContent sx={{ 
                                                p: 3,
                                                backgroundColor: darkMode ? '#2a2a2a' : 'background.paper',
                                                color: darkMode ? '#ffffff' : 'inherit'
                                            }}>
                                                                                                        {/* Render archived experiment results directly without using global result state */}
                                                    {(() => {
                                                        // Use the archived result data directly
                                                        const archivedResult = result;
                                                        
                                                        // Render using the same logic as renderResults() but with archived data
                                                        if (!archivedResult) return null;

                                                        return (
                                                            <Box sx={{ width: '100%', mt: theme.spacing(2), maxWidth: '1600px', mx: 'auto', px: 2 }}>
                                                                {/* Mode 0: Show standard clustering results */}
                                                                {archivedResult.test_metadata?.mode === 0 && archivedResult.processed_clusters && archivedResult.processed_clusters.map((processedCluster, clusterIndex) => (
                                                                    processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                                                    <div key={`similarity-${clusterIndex}`}>
                                                                        {renderSiteSimilarityResults(
                                                                            processedCluster.processed_data.site_similarity, 
                                                                            processedCluster.level, 
                                                                            processedCluster.processed_data
                                                                        )}
                                                                    </div>
                                                                ))}

                                                                {/* Mode 1: Show domain-based results */}
                                                                {archivedResult.test_metadata?.mode === 1 && archivedResult.domain_results && archivedResult.domain_results.map((domainResult, domainIndex) => (
                                                                    <div key={`domain-${domainIndex}`}>
                                                                        {/* Domain header */}
                                                                        <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 'bold', color: 'secondary.main' }}>
                                                                            🌐 Domain: {domainResult.domain}
                                                                        </Typography>
                                                                        
                                                                        {/* Domain URLs */}
                                                                        <Box sx={{ mb: 2 }}>
                                                                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                                                URLs in this domain:
                                                                            </Typography>
                                                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                                                                {domainResult.urls && domainResult.urls.map((url, urlIndex) => (
                                                                                    <Chip key={urlIndex} label={url} size="small" color="secondary" />
                                                                                ))}
                                                                            </Box>
                                                                        </Box>

                                                                        {/* Show similarity results directly if available */}
                                                                        {domainResult.processed_clusters && domainResult.processed_clusters.map((processedCluster, clusterIndex) => (
                                                                            processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                                                            <div key={`domain-${domainIndex}-similarity-${clusterIndex}`}>
                                                                                {renderSiteSimilarityResults(
                                                                                    processedCluster.processed_data.site_similarity, 
                                                                                    processedCluster.level, 
                                                                                    processedCluster.processed_data,
                                                                                    `${domainResult.domain} -`
                                                                                )}
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                ))}
                                                            </Box>
                                                        );
                                                    })()}
                                                </CardContent>
                                            </Collapse>
                                        </Card>
                                    );
                                })}
                            </Box>
                        )}
                    </Box>
                );
            case 'results':
                return (
                    <Box sx={{ width: '100%', maxWidth: '1600px', mx: 'auto', px: 3, py: 2 }}>
                        <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
                            📊 Results Archive - Previous Experiments
                        </Typography>

                        {/* Archive Controls */}
                        <Card sx={{ 
                            mb: 3,
                            backgroundColor: darkMode ? '#2a2a2a' : 'background.paper',
                            color: darkMode ? '#ffffff' : 'inherit'
                        }}>
                            <CardHeader 
                                title="🗂️ Experiment Archive Controls"
                                sx={{
                                    backgroundColor: darkMode ? '#333' : 'transparent',
                                    color: darkMode ? '#ffffff' : 'inherit'
                                }}
                            />
                            <CardContent sx={{ p: 3 }}>
                                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
                                    <Button 
                                        variant="outlined" 
                                        onClick={loadArchiveExperiments}
                                        disabled={archiveLoading}
                                        sx={{ 
                                            borderRadius: '20px',
                                            ...(darkMode && {
                                                borderColor: '#555',
                                                color: '#fff',
                                                '&:hover': {
                                                    borderColor: '#777',
                                                    backgroundColor: 'rgba(255,255,255,0.1)'
                                                }
                                            })
                                        }}
                                    >
                                        {archiveLoading ? (
                                            <>
                                                <CircularProgress size={16} sx={{ mr: 1 }} />
                                                Loading...
                                            </>
                                        ) : (
                                            '🔄 Refresh Archive'
                                        )}
                                    </Button>

                                    {selectedExperiment && (
                                        <Button 
                                            variant="outlined" 
                                            onClick={() => setSelectedExperiment(null)}
                                            sx={{ 
                                                borderRadius: '20px',
                                                ...(darkMode && {
                                                    borderColor: '#555',
                                                    color: '#fff',
                                                    '&:hover': {
                                                        borderColor: '#777',
                                                        backgroundColor: 'rgba(255,255,255,0.1)'
                                                    }
                                                })
                                            }}
                                        >
                                            ✖️ Clear Selection
                                        </Button>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>

                        {/* Experiment List - Always visible when experiments are available */}
                        {archiveExperiments.length > 0 && (
                            <Card sx={{ 
                                mb: 3,
                                backgroundColor: darkMode ? '#2a2a2a' : 'background.paper',
                                color: darkMode ? '#ffffff' : 'inherit'
                            }}>
                                <CardHeader 
                                    title={
                                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                            <Typography variant="h6">
                                                📚 Available Experiments ({archiveExperiments.length})
                                            </Typography>
                                            {selectedExperiment && (
                                                <Typography variant="caption" sx={{
                                                    color: darkMode ? '#4CAF50' : 'success.main',
                                                    fontWeight: 'bold',
                                                    backgroundColor: darkMode ? 'rgba(76, 175, 80, 0.1)' : 'rgba(76, 175, 80, 0.1)',
                                                    px: 1.5,
                                                    py: 0.5,
                                                    borderRadius: '12px',
                                                    border: '1px solid',
                                                    borderColor: darkMode ? '#4CAF50' : 'success.main'
                                                }}>
                                                    ✓ Selected: {selectedExperiment.experiment_info.name}
                                                </Typography>
                                            )}
                                        </Box>
                                    }
                                    sx={{
                                        backgroundColor: darkMode ? '#333' : 'transparent',
                                        color: darkMode ? '#ffffff' : 'inherit'
                                    }}
                                />
                                <CardContent sx={{ maxHeight: '500px', overflow: 'auto' }}>
                                    <Grid container spacing={3}>
                                        {archiveExperiments.map((experiment, index) => {
                                            const isSelected = selectedExperiment?.id === experiment.id;
                                            return (
                                                <Grid item xs={12} sm={6} md={4} key={experiment.id}>
                                                    <Card 
                                                        sx={{ 
                                                            cursor: 'pointer',
                                                            transition: 'all 0.3s ease-in-out',
                                                            backgroundColor: isSelected 
                                                                ? (darkMode ? '#1976d2' : 'primary.light')
                                                                : (darkMode ? '#333' : 'background.paper'),
                                                            color: isSelected 
                                                                ? 'white'
                                                                : (darkMode ? '#ffffff' : 'inherit'),
                                                            transform: isSelected ? 'scale(1.02)' : 'scale(1)',
                                                            '&:hover': {
                                                                transform: isSelected ? 'scale(1.03)' : 'translateY(-2px)',
                                                                boxShadow: isSelected
                                                                    ? '0 8px 24px rgba(25, 118, 210, 0.4)'
                                                                    : (darkMode 
                                                                        ? '0 4px 12px rgba(0,0,0,0.4)' 
                                                                        : '0 4px 12px rgba(0,0,0,0.15)'),
                                                                backgroundColor: isSelected
                                                                    ? (darkMode ? '#1565c0' : 'primary.main')
                                                                    : (darkMode ? '#404040' : 'grey.50')
                                                            },
                                                            border: '2px solid',
                                                            borderColor: isSelected 
                                                                ? (darkMode ? '#42a5f5' : 'primary.main')
                                                                : (darkMode ? '#555' : 'divider'),
                                                            boxShadow: isSelected 
                                                                ? '0 4px 16px rgba(25, 118, 210, 0.3)'
                                                                : '0 2px 4px rgba(0,0,0,0.1)',
                                                            position: 'relative',
                                                            '&::before': isSelected ? {
                                                                content: '""',
                                                                position: 'absolute',
                                                                top: 8,
                                                                right: 8,
                                                                width: 24,
                                                                height: 24,
                                                                backgroundColor: 'white',
                                                                borderRadius: '50%',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                                zIndex: 1
                                                            } : {}
                                                        }}
                                                        onClick={() => loadExperimentDetails(experiment.id)}
                                                    >
                                                        {isSelected && (
                                                            <Box sx={{
                                                                position: 'absolute',
                                                                top: 8,
                                                                right: 8,
                                                                width: 24,
                                                                height: 24,
                                                                backgroundColor: 'white',
                                                                borderRadius: '50%',
                                                                display: 'flex',
                                                                alignItems: 'center',
                                                                justifyContent: 'center',
                                                                zIndex: 1,
                                                                color: 'primary.main',
                                                                fontSize: '16px',
                                                                fontWeight: 'bold'
                                                            }}>
                                                                ✓
                                                            </Box>
                                                        )}
                                                        <CardContent sx={{ p: 2 }}>
                                                            <Typography variant="h6" sx={{ 
                                                                fontWeight: 'bold', 
                                                                mb: 1, 
                                                                fontSize: '1rem',
                                                                color: isSelected ? 'white' : (darkMode ? '#ffffff' : 'inherit')
                                                            }}>
                                                                {experiment.name}
                                                            </Typography>
                                                            <Typography variant="caption" sx={{ 
                                                                display: 'block', 
                                                                mb: 1,
                                                                color: isSelected ? 'rgba(255,255,255,0.8)' : (darkMode ? '#aaa' : 'text.secondary')
                                                            }}>
                                                                {experiment.timestamp}
                                                            </Typography>
                                                            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
                                                                <Box>
                                                                    <Typography variant="caption" sx={{ 
                                                                        color: isSelected ? 'rgba(255,255,255,0.8)' : (darkMode ? '#aaa' : 'text.secondary')
                                                                    }}>Tests</Typography>
                                                                    <Typography variant="subtitle2" sx={{
                                                                        color: isSelected ? 'white' : (darkMode ? '#ffffff' : 'inherit')
                                                                    }}>{experiment.total_tests}</Typography>
                                                                </Box>
                                                                <Box>
                                                                    <Typography variant="caption" sx={{ 
                                                                        color: isSelected ? 'rgba(255,255,255,0.8)' : (darkMode ? '#aaa' : 'text.secondary')
                                                                    }}>Success Rate</Typography>
                                                                    <Typography variant="subtitle2" sx={{
                                                                        color: isSelected ? '#81C784' : 'success.main',
                                                                        fontWeight: isSelected ? 'bold' : 'normal'
                                                                    }}>
                                                                        {experiment.success_rate.toFixed(1)}%
                                                                    </Typography>
                                                                </Box>
                                                            </Box>
                                                            <Typography variant="caption" sx={{ 
                                                                color: isSelected ? 'rgba(255,255,255,0.8)' : (darkMode ? '#aaa' : 'text.secondary')
                                                            }}>
                                                                Duration: {formatDuration(experiment.duration)}
                                                            </Typography>
                                                        </CardContent>
                                                    </Card>
                                                </Grid>
                                            );
                                        })}
                                    </Grid>
                                </CardContent>
                            </Card>
                        )}

                        {/* Selected Experiment Details */}
                        {selectedExperiment && (
                            <Box sx={{ width: '100%', mt: theme.spacing(2), maxWidth: '1600px', mx: 'auto', px: 2 }}>
                                {/* Experiment Summary */}
                                <Card sx={{ 
                                    mb: 3,
                                    backgroundColor: darkMode ? '#2a2a2a' : 'background.paper',
                                    color: darkMode ? '#ffffff' : 'inherit'
                                }}>
                                    <CardHeader 
                                        title={`📊 ${selectedExperiment.experiment_info.name}`}
                                        subheader={`Experiment ID: ${selectedExperiment.id}`}
                                        sx={{
                                            backgroundColor: darkMode ? '#333' : 'transparent',
                                            color: darkMode ? '#ffffff' : 'inherit',
                                            '& .MuiCardHeader-subheader': {
                                                color: darkMode ? '#aaa' : 'text.secondary'
                                            }
                                        }}
                                    />
                                    <CardContent>
                                        <Grid container spacing={3}>
                                            <Grid item xs={12}>
                                                <Typography variant="h6" gutterBottom sx={{
                                                    color: darkMode ? '#ffffff' : 'inherit'
                                                }}>📈 Performance Summary</Typography>
                                                <Box sx={{ 
                                                    display: 'grid', 
                                                    gridTemplateColumns: 'repeat(5, 1fr)', 
                                                    gap: 2,
                                                    width: '100%',
                                                    '@media (max-width: 768px)': {
                                                        gridTemplateColumns: 'repeat(3, 1fr)'
                                                    },
                                                    '@media (max-width: 480px)': {
                                                        gridTemplateColumns: 'repeat(2, 1fr)'
                                                    }
                                                }}>
                                                    <Box>
                                                        <Typography variant="caption" sx={{
                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                        }}>Total Tests</Typography>
                                                        <Typography variant="h6" sx={{
                                                            color: darkMode ? '#ffffff' : 'inherit'
                                                        }}>{selectedExperiment.experiment_info.total_tests}</Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{
                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                        }}>Success Rate</Typography>
                                                        <Typography variant="h6" color="success.main">
                                                            {selectedExperiment.experiment_info.success_rate.toFixed(1)}%
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{
                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                        }}>Successful</Typography>
                                                        <Typography variant="h6" color="success.main">
                                                            {selectedExperiment.experiment_info.successful_tests}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{
                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                        }}>Failed</Typography>
                                                        <Typography variant="h6" color="error.main">
                                                            {selectedExperiment.experiment_info.failed_tests}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" sx={{
                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                        }}>Duration</Typography>
                                                        <Typography variant="h6" sx={{
                                                            color: darkMode ? '#ffffff' : 'inherit'
                                                        }}>
                                                            {formatDuration(selectedExperiment.experiment_info.duration)}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                            </Grid>
                                            <Grid item xs={12}>
                                                <Typography variant="h6" gutterBottom sx={{
                                                    color: darkMode ? '#ffffff' : 'inherit'
                                                }}>📁 Generated Files & Analysis</Typography>
                                                
                                                {/* Generated Images */}
                                                {selectedExperiment.generated_images && selectedExperiment.generated_images.length > 0 && (
                                                    <Box sx={{ mt: 2 }}>
                                                            <Typography variant="subtitle2" sx={{ 
                                                                fontWeight: 'bold', 
                                                                mb: 1,
                                                                color: darkMode ? '#ffffff' : 'inherit'
                                                            }}>
                                                                🖼️ Generated Charts ({selectedExperiment.generated_images.filter(img => img.size_kb > 0).length})
                                                            </Typography>
                                                            <Grid container spacing={1}>
                                                                {selectedExperiment.generated_images.filter(img => img.size_kb > 0 && img.format === 'PNG').map((image, index) => (
                                                                    <Grid item xs={12} sm={6} md={4} key={index}>
                                                                        <Card sx={{ 
                                                                            cursor: 'pointer',
                                                                            transition: 'all 0.2s',
                                                                            backgroundColor: darkMode ? '#333' : 'background.paper',
                                                                            color: darkMode ? '#ffffff' : 'inherit',
                                                                            '&:hover': {
                                                                                transform: 'translateY(-2px)',
                                                                                boxShadow: darkMode 
                                                                                    ? '0 4px 8px rgba(0,0,0,0.4)' 
                                                                                    : '0 4px 8px rgba(0,0,0,0.15)',
                                                                                backgroundColor: darkMode ? '#404040' : undefined
                                                                            }
                                                                        }}>
                                                                            <CardContent sx={{ p: 1.5 }}>
                                                                                {/* Image Preview for PNG files */}
                                                                                <Box sx={{ mb: 1, textAlign: 'center' }}>
                                                                                    <img 
                                                                                        src={`http://localhost:5000/experiments/results/${selectedExperiment.id}/images/${image.filename}`}
                                                                                        alt={image.chart_type}
                                                                                        style={{ 
                                                                                            maxWidth: '100%', 
                                                                                            maxHeight: '80px',
                                                                                            objectFit: 'contain',
                                                                                            border: darkMode ? '1px solid #555' : '1px solid #ddd',
                                                                                            borderRadius: '4px',
                                                                                            cursor: 'pointer'
                                                                                        }}
                                                                                        onClick={() => {
                                                                                            const imageWithUrl = {
                                                                                                ...image,
                                                                                                url: `http://localhost:5000/experiments/results/${selectedExperiment.id}/images/${image.filename}`
                                                                                            };
                                                                                            handleImageClick(imageWithUrl);
                                                                                        }}
                                                                                        onError={(e) => {
                                                                                            e.target.style.display = 'none';
                                                                                        }}
                                                                                    />
                                                                                </Box>
                                                                                <Typography variant="caption" sx={{ 
                                                                                    fontWeight: 'bold', 
                                                                                    display: 'block',
                                                                                    mb: 0.5,
                                                                                    color: darkMode ? '#ffffff' : 'inherit'
                                                                                }}>
                                                                                    {image.chart_type}
                                                                                </Typography>
                                                                                <Typography variant="caption" sx={{ 
                                                                                    color: darkMode ? '#aaa' : 'text.secondary',
                                                                                    fontSize: '0.7rem'
                                                                                }}>
                                                                                    {image.format} • {image.size_kb.toFixed(1)} KB
                                                                                </Typography>
                                                                                <Button
                                                                                    variant="text"
                                                                                    size="small"
                                                                                    fullWidth
                                                                                    sx={{ mt: 0.5, fontSize: '0.7rem' }}
                                                                                    onClick={() => {
                                                                                        const imageWithUrl = {
                                                                                            ...image,
                                                                                            url: `http://localhost:5000/experiments/results/${selectedExperiment.id}/images/${image.filename}`
                                                                                        };
                                                                                        handleImageClick(imageWithUrl);
                                                                                    }}
                                                                                >
                                                                                    🔍 View
                                                                                </Button>
                                                                            </CardContent>
                                                                        </Card>
                                                                    </Grid>
                                                                ))}
                                                            </Grid>
                                                        </Box>
                                                    )}
                                            </Grid>
                                        </Grid>
                                    </CardContent>
                                </Card>

                                {/* Display results using the same format as experiment results with better separation */}
                                {selectedExperiment.results && selectedExperiment.results.map((result, index) => {
                                    const cardId = `archive-result-${selectedExperiment.id}-${index}`;
                                    const collapsed = isCardCollapsed(cardId);
                                    

                                    
                                    return result.status === 'success' && (
                                        <Card key={index} sx={{ 
                                            mb: 4, 
                                            border: '2px solid',
                                            borderColor: result.test_metadata?.mode === 0 ? 'primary.light' : 'secondary.light',
                                            borderRadius: 3,
                                            overflow: 'hidden',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                            backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                                        }}>
                                            <CardHeader 
                                                title={
                                                    <Typography variant="h5" sx={{ 
                                                        fontWeight: 'bold',
                                                        color: 'white',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        gap: 1
                                                    }}>
                                                        {result.test_metadata?.mode === 0 ? '🧮' : '🌐'} Test: {result.test_metadata?.test_name || `Test ${index + 1}`}
                                                    </Typography>
                                                }
                                                subheader={
                                                    <Typography variant="subtitle1" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                                                        ID: {result.test_metadata?.test_id} | Mode: {result.test_metadata?.mode === 0 ? '0 (All Together)' : '1 (Domain-based)'} | Duration: {formatDuration(result.test_metadata?.duration || 0)}
                                                    </Typography>
                                                }
                                                action={
                                                    <Tooltip title={collapsed ? "Expand card" : "Collapse card"}>
                                                        <IconButton
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                toggleCardCollapse(cardId);
                                                            }}
                                                            sx={{
                                                                color: 'white',
                                                                '&:hover': {
                                                                    backgroundColor: 'rgba(255,255,255,0.1)'
                                                                }
                                                            }}
                                                        >
                                                            {collapsed ? <ExpandMoreIcon /> : <ExpandLessIcon />}
                                                        </IconButton>
                                                    </Tooltip>
                                                }
                                                onClick={() => toggleCardCollapse(cardId)}
                                                sx={{
                                                    backgroundColor: result.test_metadata?.mode === 0 ? 'primary.main' : 'secondary.main',
                                                    color: 'white',
                                                    py: 2,
                                                    cursor: 'pointer',
                                                    '&:hover': {
                                                        backgroundColor: result.test_metadata?.mode === 0 ? 'primary.dark' : 'secondary.dark'
                                                    }
                                                }}
                                            />
                                            <Collapse in={!collapsed} timeout="auto" unmountOnExit>
                                                <CardContent sx={{ 
                                                    p: 3,
                                                    backgroundColor: darkMode ? '#2a2a2a' : 'background.paper',
                                                    color: darkMode ? '#ffffff' : 'inherit'
                                                }}>
                                                    {/* Performance Metrics Summary for Archive Results */}
                                                    {result.timing_logs && result.timing_logs.performance_metrics && (
                                                        <Accordion 
                                                            sx={{ 
                                                                mb: theme.spacing(2),
                                                                '&:before': { display: 'none' },
                                                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                                                borderRadius: '8px !important',
                                                                overflow: 'hidden',
                                                                backgroundColor: darkMode ? '#333' : 'info.light'
                                                            }}
                                                        >
                                                            <AccordionSummary 
                                                                expandIcon={<ExpandMoreIcon />}
                                                                sx={{
                                                                    backgroundColor: darkMode ? '#404040' : 'info.main',
                                                                    color: 'white',
                                                                    '&:hover': { backgroundColor: darkMode ? '#505050' : 'info.dark' }
                                                                }}
                                                            >
                                                                <Typography sx={{ fontWeight: 'bold' }}>
                                                                    ⚡ Performance Metrics & Cache Efficiency
                                                                </Typography>
                                                            </AccordionSummary>
                                                            <AccordionDetails sx={{ p: 2, backgroundColor: darkMode ? '#2a2a2a' : 'background.paper' }}>
                                                                <Grid container spacing={2}>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>Total Time</Typography>
                                                                        <Typography variant="h6" color="primary" sx={{ color: darkMode ? '#64B5F6' : 'primary.main' }}>
                                                                            {formatDuration(result.timing_logs.performance_metrics.total_processing_time)}
                                                                        </Typography>
                                                                    </Grid>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>Cache Efficiency</Typography>
                                                                        <Typography variant="h6" color="success.main">
                                                                            {result.timing_logs.performance_metrics.cache_efficiency_percent?.toFixed(1)}%
                                                                        </Typography>
                                                                    </Grid>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>URLs Processed</Typography>
                                                                        <Typography variant="h6" sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                                                            {result.timing_logs.performance_metrics.urls_processed}
                                                                        </Typography>
                                                                    </Grid>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>From Cache</Typography>
                                                                        <Typography variant="h6" color="success.main">
                                                                            {result.timing_logs.performance_metrics.urls_from_cache}
                                                                        </Typography>
                                                                    </Grid>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>HTML Files</Typography>
                                                                        <Typography variant="h6" sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                                                            {result.timing_logs.performance_metrics.html_files_generated}
                                                                        </Typography>
                                                                    </Grid>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>Clusters</Typography>
                                                                        <Typography variant="h6" sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                                                            {result.timing_logs.performance_metrics.clusters_generated}
                                                                        </Typography>
                                                                    </Grid>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>Avg Time/URL</Typography>
                                                                        <Typography variant="h6" sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                                                            {formatDuration(result.timing_logs.performance_metrics.average_time_per_url)}
                                                                        </Typography>
                                                                    </Grid>
                                                                    <Grid item xs={6} sm={4} md={3}>
                                                                        <Typography variant="caption" sx={{ color: darkMode ? '#aaa' : 'text.secondary' }}>Avg Time/Level</Typography>
                                                                        <Typography variant="h6" sx={{ color: darkMode ? '#ffffff' : 'inherit' }}>
                                                                            {formatDuration(result.timing_logs.performance_metrics.average_time_per_level)}
                                                                        </Typography>
                                                                    </Grid>
                                                                </Grid>
                                                                {result.timing_logs.performance_metrics.cache_savings && (
                                                                    <Box sx={{ mt: 2, p: 1.5, backgroundColor: darkMode ? '#1e4620' : 'success.light', borderRadius: 1 }}>
                                                                        <Typography variant="body2" sx={{ color: darkMode ? '#81C784' : 'success.dark', fontWeight: 'bold' }}>
                                                                            💾 {result.timing_logs.performance_metrics.cache_savings}
                                                                </Typography>
                                                            </Box>
                                                        )}
                                                            </AccordionDetails>
                                                        </Accordion>
                                                    )}

                                                    {/* Complete Timing Logs for Archive Results */}
                                                    {result.timing_logs && renderTimingLogs(result.timing_logs)}
                                                    
                                                    {/* Domain-specific Timing Logs for Mode 1 */}
                                                    {result.domain_results && result.domain_results.map((domainResult, domainIndex) => (
                                                        domainResult.timing_logs && (
                                                            <Box key={`domain-timing-${domainIndex}`} sx={{ mt: 2 }}>
                                                                <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                                                                    🌐 {domainResult.domain} - Detailed Timing Logs
                                                                </Typography>
                                                                {renderTimingLogs(domainResult.timing_logs)}
                                                            </Box>
                                                        )
                                                    ))}

                                                    {/* Mode 0: Show standard clustering results */}
                                                    {result.test_metadata?.mode === 0 && result.processed_clusters && result.processed_clusters.map((processedCluster, clusterIndex) => (
                                                        processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                                        <div key={`similarity-${clusterIndex}`}>
                                                            {renderSiteSimilarityResults(
                                                                processedCluster.processed_data.site_similarity, 
                                                                processedCluster.level, 
                                                                processedCluster.processed_data
                                                            )}
                                                        </div>
                                                    ))}

                                                    {/* Mode 1: Show domain-based results */}
                                                    {result.test_metadata?.mode === 1 && result.domain_results && result.domain_results.map((domainResult, domainIndex) => (
                                                        <div key={`domain-${domainIndex}`}>
                                                            {/* Domain header */}
                                                            <Typography variant="h6" sx={{ mt: 3, mb: 2, fontWeight: 'bold', color: 'secondary.main' }}>
                                                                🌐 Domain: {domainResult.domain}
                                                            </Typography>
                                                            
                                                            {/* Domain URLs */}
                                                            <Box sx={{ mb: 2 }}>
                                                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                                    URLs in this domain:
                                                                </Typography>
                                                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                                                    {domainResult.urls && domainResult.urls.map((url, urlIndex) => (
                                                                        <Chip key={urlIndex} label={url} size="small" color="secondary" />
                                                                    ))}
                                                                </Box>
                                                            </Box>

                                                            {/* Show similarity results directly if available */}
                                                            {domainResult.processed_clusters && domainResult.processed_clusters.map((processedCluster, clusterIndex) => (
                                                                processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                                                <div key={`domain-${domainIndex}-similarity-${clusterIndex}`}>
                                                                                                                                {renderSiteSimilarityResults(
                                                                processedCluster.processed_data.site_similarity, 
                                                                processedCluster.level, 
                                                                processedCluster.processed_data,
                                                                `${domainResult.domain} -`
                                                            )}
                                                                </div>
                                                            ))}
                                                        </div>
                                                    ))}

                                                    {/* Clustering Results Summary - Mode 0 only */}
                                                    {result.test_metadata?.mode === 0 && result.clustering_results && result.clustering_results.map((clusterResult, clusterIndex) => (
                                                        <Accordion 
                                                            key={`cluster-${clusterIndex}`} 
                                                            sx={{ 
                                                                mb: theme.spacing(1),
                                                                '&:before': { display: 'none' },
                                                                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                                                borderRadius: '4px !important',
                                                                backgroundColor: darkMode ? '#333' : 'background.paper'
                                                            }}
                                                        >
                                                            <AccordionSummary 
                                                                expandIcon={<ExpandMoreIcon />}
                                                                sx={{
                                                                    backgroundColor: clusterResult.status === 'error' 
                                                                        ? 'error.light' 
                                                                        : (darkMode ? '#404040' : 'grey.100'),
                                                                    color: darkMode ? '#ffffff' : 'inherit',
                                                                    '&:hover': {
                                                                        backgroundColor: clusterResult.status === 'error' 
                                                                            ? 'error.main' 
                                                                            : (darkMode ? '#505050' : 'grey.200'),
                                                                    }
                                                                }}
                                                            >
                                                                <Typography sx={{ 
                                                                    fontWeight: 'bold', 
                                                                    fontSize: '0.9rem',
                                                                    color: darkMode ? '#ffffff' : 'inherit'
                                                                }}>
                                                                    🧮 Level {clusterResult.level} - {clusterResult.status === 'error' ? '❌' : '✅'} {clusterResult.message}
                                                                </Typography>
                                                            </AccordionSummary>
                                                            <AccordionDetails sx={{ 
                                                                p: 2,
                                                                backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                                                            }}>
                                                                {clusterResult.status === 'error' ? (
                                                                    <Typography variant="body2" color="error">
                                                                        {clusterResult.message}
                                                                    </Typography>
                                                                ) : (
                                                                    (() => {
                                                                        const clusterInfo = getClusterInfo(clusterResult);
                                                                        if (!clusterInfo) return null;
                                                                        
                                                                        return (
                                                                            <Box>
                                                                                <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1 }}>
                                                                                    <Box>
                                                                                        <Typography variant="caption" sx={{
                                                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                                                        }}>Clusters</Typography>
                                                                                        <Typography variant="subtitle2" sx={{
                                                                                            color: darkMode ? '#ffffff' : 'inherit'
                                                                                        }}>{clusterInfo.num_clusters}</Typography>
                                                                                    </Box>
                                                                                    <Box>
                                                                                        <Typography variant="caption" sx={{
                                                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                                                        }}>DBCV Score</Typography>
                                                                                        <Typography variant="subtitle2" sx={{
                                                                                            color: darkMode ? '#ffffff' : 'inherit'
                                                                                        }}>{clusterInfo.dbcv_score?.toFixed(3)}</Typography>
                                                                                    </Box>
                                                                                    <Box>
                                                                                        <Typography variant="caption" sx={{
                                                                                            color: darkMode ? '#aaa' : 'text.secondary'
                                                                                        }}>Attributes</Typography>
                                                                                        <Typography variant="subtitle2" sx={{
                                                                                            color: darkMode ? '#ffffff' : 'inherit'
                                                                                        }}>{clusterInfo.useful_attributes?.length || 0}</Typography>
                                                                                    </Box>
                                                                                </Box>
                                                                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                                                                                    <Tooltip title="Copy archived clustering summary">
                                                                                        <Button
                                                                                            variant="outlined"
                                                                                            size="small"
                                                                                            onClick={() => {
                                                                                                const archivedClusteringSummary = {
                                                                                                    level: clusterResult.level,
                                                                                                    status: clusterResult.status,
                                                                                                    message: clusterResult.message,
                                                                                                    summary: {
                                                                                                        num_clusters: clusterInfo.num_clusters,
                                                                                                        dbcv_score: clusterInfo.dbcv_score,
                                                                                                        min_cluster_size: clusterInfo.min_cluster_size,
                                                                                                        cluster_selection_epsilon: clusterInfo.cluster_selection_epsilon,
                                                                                                        useful_attributes_count: clusterInfo.useful_attributes?.length || 0
                                                                                                    },
                                                                                                    archived_test_id: result.test_metadata?.test_id,
                                                                                                    timestamp: new Date().toISOString()
                                                                                                };
                                                                                                handleCopyToClipboard(JSON.stringify(archivedClusteringSummary, null, 2));
                                                                                                setSuccess(`📋 Archived Level ${clusterResult.level} clustering summary copied!`);
                                                                                            }}
                                                                                            sx={{
                                                                                                fontSize: '0.75rem',
                                                                                                px: 2,
                                                                                                ...(darkMode && {
                                                                                                    borderColor: '#555',
                                                                                                    color: '#fff',
                                                                                                    '&:hover': {
                                                                                                        borderColor: '#777',
                                                                                                        backgroundColor: 'rgba(255,255,255,0.1)'
                                                                                                    }
                                                                                                })
                                                                                            }}
                                                                                        >
                                                                                            📋 Copy Summary
                                                                                        </Button>
                                                                                    </Tooltip>
                                                                                </Box>
                                                                            </Box>
                                                                        );
                                                                    })()
                                                                )}
                                                            </AccordionDetails>
                                                        </Accordion>
                                                    ))}

                                                    {/* Clustering Results Summary - Mode 1 only */}
                                                    {result.test_metadata?.mode === 1 && result.domain_results && result.domain_results.map((domainResult, domainIndex) => (
                                                        domainResult.clustering_results && domainResult.clustering_results.map((clusterResult, clusterIndex) => (
                                                            <Accordion 
                                                                key={`domain-${domainIndex}-cluster-${clusterIndex}`} 
                                                                sx={{ 
                                                                    mb: theme.spacing(1),
                                                                    '&:before': { display: 'none' },
                                                                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                                                                    borderRadius: '4px !important',
                                                                    backgroundColor: darkMode ? '#333' : 'background.paper'
                                                                }}
                                                            >
                                                                <AccordionSummary 
                                                                    expandIcon={<ExpandMoreIcon />}
                                                                    sx={{
                                                                        backgroundColor: clusterResult.status === 'error' 
                                                                            ? 'error.light' 
                                                                            : (darkMode ? '#404040' : 'grey.100'),
                                                                        color: darkMode ? '#ffffff' : 'inherit',
                                                                        '&:hover': {
                                                                            backgroundColor: clusterResult.status === 'error' 
                                                                                ? 'error.main' 
                                                                                : (darkMode ? '#505050' : 'grey.200')
                                                                        }
                                                                    }}
                                                                >
                                                                    <Typography sx={{ 
                                                                        fontWeight: 'bold', 
                                                                        fontSize: '0.9rem',
                                                                        color: darkMode ? '#ffffff' : 'inherit'
                                                                    }}>
                                                                        🧮 {domainResult.domain} - Level {clusterResult.level} - {clusterResult.status === 'error' ? '❌' : '✅'} {clusterResult.message}
                                                                    </Typography>
                                                                </AccordionSummary>
                                                                <AccordionDetails sx={{ 
                                                                    p: 2,
                                                                    backgroundColor: darkMode ? '#2a2a2a' : 'background.paper'
                                                                }}>
                                                                    {clusterResult.status === 'error' ? (
                                                                        <Typography variant="body2" color="error">
                                                                            {clusterResult.message}
                                                                        </Typography>
                                                                    ) : (
                                                                        (() => {
                                                                            const clusterInfo = getClusterInfo(clusterResult);
                                                                            if (!clusterInfo) return null;
                                                                            
                                                                            return (
                                                                                <Box>
                                                                                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1 }}>
                                                                                        <Box>
                                                                                            <Typography variant="caption" color="text.secondary">Clusters</Typography>
                                                                                            <Typography variant="subtitle2" sx={{
                                                                                                color: darkMode ? '#ffffff' : 'inherit'
                                                                                            }}>{clusterInfo.num_clusters}</Typography>
                                                                                        </Box>
                                                                                        <Box>
                                                                                            <Typography variant="caption" color="text.secondary">DBCV Score</Typography>
                                                                                            <Typography variant="subtitle2" sx={{
                                                                                                color: darkMode ? '#ffffff' : 'inherit'
                                                                                            }}>{clusterInfo.dbcv_score?.toFixed(3)}</Typography>
                                                                                        </Box>
                                                                                        <Box>
                                                                                            <Typography variant="caption" color="text.secondary">Attributes</Typography>
                                                                                            <Typography variant="subtitle2" sx={{
                                                                                                color: darkMode ? '#ffffff' : 'inherit'
                                                                                            }}>{clusterInfo.useful_attributes?.length || 0}</Typography>
                                                                                        </Box>
                                                                                    </Box>
                                                                                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                                                                                        <Tooltip title="Copy domain clustering summary">
                                                                                            <Button
                                                                                                variant="outlined"
                                                                                                size="small"
                                                                                                onClick={() => {
                                                                                                    const domainClusteringSummary = {
                                                                                                        domain: domainResult.domain,
                                                                                                        level: clusterResult.level,
                                                                                                        status: clusterResult.status,
                                                                                                        message: clusterResult.message,
                                                                                                        summary: {
                                                                                                            num_clusters: clusterInfo.num_clusters,
                                                                                                            dbcv_score: clusterInfo.dbcv_score,
                                                                                                            min_cluster_size: clusterInfo.min_cluster_size,
                                                                                                            cluster_selection_epsilon: clusterInfo.cluster_selection_epsilon,
                                                                                                            useful_attributes_count: clusterInfo.useful_attributes?.length || 0
                                                                                                        },
                                                                                                        timestamp: new Date().toISOString()
                                                                                                    };
                                                                                                    handleCopyToClipboard(JSON.stringify(domainClusteringSummary, null, 2));
                                                                                                    setSuccess(`📋 Level ${clusterResult.level} clustering summary copied!`);
                                                                                                }}
                                                                                                sx={{
                                                                                                    fontSize: '0.75rem',
                                                                                                    px: 2,
                                                                                                    ...(darkMode && {
                                                                                                        borderColor: '#555',
                                                                                                        color: '#fff',
                                                                                                        '&:hover': {
                                                                                                            borderColor: '#777',
                                                                                                            backgroundColor: 'rgba(255,255,255,0.1)'
                                                                                                        }
                                                                                                    })
                                                                                                }}
                                                                                            >
                                                                                                📋 Copy Summary
                                                                                            </Button>
                                                                                        </Tooltip>
                                                                                    </Box>
                                                                                </Box>
                                                                            );
                                                                        })()
                                                                    )}
                                                                </AccordionDetails>
                                                            </Accordion>
                                                        ))
                                                    ))}

                                                    {/* Export Buttons */}
                                                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
                                                        <Button
                                                            variant="outlined"
                                                            size="small"
                                                            onClick={() => {
                                                                // Pass the specific archived result data
                                                                handleCopyComprehensiveResults(result);
                                                            }}
                                                        >
                                                            📊 Copy Test Results
                                                        </Button>
                                                        <Button
                                                            variant="outlined"
                                                            size="small"
                                                            onClick={() => {
                                                                // Pass the specific archived result data
                                                                handleCopyAllLevelsSummary(result);
                                                            }}
                                                        >
                                                            📋 Copy Levels Summary
                                                        </Button>
                                                    </Box>
                                                </CardContent>
                                            </Collapse>
                                        </Card>
                                    );
                                })}
                            </Box>
                        )}

                        {/* Loading State */}
                        {archiveLoading && (
                            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 4 }}>
                                <CircularProgress />
                                <Typography sx={{ ml: 2 }}>Loading experiment results...</Typography>
                            </Box>
                        )}

                        {/* Empty State */}
                        {!archiveLoading && archiveExperiments.length === 0 && (
                            <Card sx={{ 
                                textAlign: 'center', 
                                py: 4,
                                backgroundColor: darkMode ? '#2a2a2a' : 'background.paper',
                                color: darkMode ? '#ffffff' : 'inherit'
                            }}>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom sx={{
                                        color: darkMode ? '#aaa' : 'text.secondary'
                                    }}>
                                        📭 No experiments found
                                    </Typography>
                                    <Typography variant="body2" sx={{
                                        color: darkMode ? '#aaa' : 'text.secondary'
                                    }}>
                                        Run some experiments first to see results here.
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}
                    </Box>
                );
            default:
                return <div>Home</div>;
        }
    };

    // Function to play notification sound
    const playNotificationSound = (isSuccess = true) => {
        try {
            // Create audio context
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create oscillator for beep sound
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            // Connect nodes
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Configure sound
            if (isSuccess) {
                // Success sound: two ascending beeps
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                
                // Start and stop
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
                
                // Add second beep
                setTimeout(() => {
                    const oscillator2 = audioContext.createOscillator();
                    const gainNode2 = audioContext.createGain();
                    oscillator2.connect(gainNode2);
                    gainNode2.connect(audioContext.destination);
                    
                    oscillator2.frequency.setValueAtTime(1200, audioContext.currentTime);
                    gainNode2.gain.setValueAtTime(0.1, audioContext.currentTime);
                    gainNode2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
                    
                    oscillator2.start(audioContext.currentTime);
                    oscillator2.stop(audioContext.currentTime + 0.2);
                }, 150);
            } else {
                // Error sound: lower frequency descending beep
                oscillator.frequency.setValueAtTime(400, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(200, audioContext.currentTime + 0.2);
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
                
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.4);
            }
        } catch (error) {
            console.warn('Could not play notification sound:', error);
        }
    };

    return (
        <Grid
            container
            direction="column"
            justifyContent="flex-start"
            alignItems="stretch"
            spacing={2}
            sx={{
                paddingTop: theme.spacing(1),
                paddingLeft: theme.spacing(1),
                paddingRight: theme.spacing(1),
                boxSizing: 'border-box',
                bgcolor: darkMode ? '#121212' : 'background.default',
                minHeight: '100vh',
                transition: 'background-color 0.3s ease',
                width: '100%',
                color: darkMode ? '#ffffff' : 'inherit'
            }}
        >
            {/* Fixed Top Navigation Bar */}
            <Box sx={{ 
                position: 'fixed',
                top: 0,
                left: 0,
                right: 0,
                zIndex: 1000,
                backgroundColor: darkMode ? '#1a1a1a' : 'background.paper',
                borderBottom: '1px solid',
                borderColor: darkMode ? '#333' : 'divider',
                boxShadow: darkMode ? '0 2px 8px rgba(0,0,0,0.5)' : '0 2px 4px rgba(0,0,0,0.1)',
                py: 1.5,
                px: 3
            }}>
                <Box sx={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    width: '100%',
                    maxWidth: '1600px',
                    mx: 'auto'
                }}>
                    {/* Left: Site Title */}
                    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', minWidth: '200px' }}>
                        <Typography 
                            variant="h5" 
                            onClick={() => setCurrentView('home')}
                            sx={{ 
                                fontWeight: 'bold',
                                background: darkMode 
                                    ? 'linear-gradient(45deg, #64B5F6 30%, #42A5F5 90%)'
                                    : 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                                backgroundClip: 'text',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                fontSize: { xs: '1.2rem', sm: '1.5rem' },
                                cursor: 'pointer',
                                transition: 'all 0.2s ease-in-out',
                                lineHeight: 1,
                                '&:hover': {
                                    transform: 'scale(1.05)',
                                    opacity: 0.8
                                }
                            }}
                        >
                            S⁴D
                        </Typography>
                        <Typography 
                            variant="caption"
                            onClick={() => setCurrentView('home')}
                            sx={{ 
                                fontSize: { xs: '0.6rem', sm: '0.7rem' },
                                color: darkMode ? '#aaa' : 'text.secondary',
                                cursor: 'pointer',
                                mt: -0.5,
                                lineHeight: 1,
                                transition: 'all 0.2s ease-in-out',
                                '&:hover': {
                                    opacity: 0.8
                                }
                            }}
                        >
                            Style and Structure Similarity for Site Domains
                        </Typography>
                    </Box>
                    
                    {/* Center: Navigation Buttons */}
                    <Box sx={{ display: 'flex', gap: theme.spacing(1), flexWrap: 'wrap', justifyContent: 'center' }}>
                        <Button 
                            variant={currentView === 'home' ? 'contained' : 'outlined'} 
                            onClick={() => setCurrentView('home')}
                            sx={{ 
                                minWidth: '100px', 
                                fontSize: '0.875rem',
                                ...(darkMode && currentView !== 'home' && {
                                    borderColor: '#555',
                                    color: '#fff',
                                    '&:hover': {
                                        borderColor: '#777',
                                        backgroundColor: 'rgba(255,255,255,0.1)'
                                    }
                                })
                            }}
                            size="small"
                        >
                            🏠 Home
                        </Button>

                        <Button 
                            variant={currentView === 'config' ? 'contained' : 'outlined'} 
                            onClick={() => setCurrentView('config')}
                            sx={{ 
                                minWidth: '170px', 
                                fontSize: '0.875rem',
                                ...(darkMode && currentView !== 'config' && {
                                    borderColor: '#555',
                                    color: '#fff',
                                    '&:hover': {
                                        borderColor: '#777',
                                        backgroundColor: 'rgba(255,255,255,0.1)'
                                    }
                                })
                            }}
                            size="small"
                        >
                            ⚙️ Experiments
                        </Button>
                        <Button 
                            variant={currentView === 'results' ? 'contained' : 'outlined'} 
                            onClick={() => setCurrentView('results')}
                            sx={{ 
                                minWidth: '150px', 
                                fontSize: '0.875rem',
                                ...(darkMode && currentView !== 'results' && {
                                    borderColor: '#555',
                                    color: '#fff',
                                    '&:hover': {
                                        borderColor: '#777',
                                        backgroundColor: 'rgba(255,255,255,0.1)'
                                    }
                                })
                            }}
                            size="small"
                        >
                            📊 Results Archive
                        </Button>
                    </Box>
                    
                    {/* Right: GitHub Link and Dark Mode Toggle */}
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: '200px', justifyContent: 'flex-end' }}>
                        <Tooltip title="View on GitHub">
                            <IconButton
                                component="a"
                                href="https://github.com/your-username/lib_url_to_img"
                                target="_blank"
                                rel="noopener noreferrer"
                                sx={{
                                    color: darkMode ? '#fff' : 'text.primary',
                                    '&:hover': {
                                        color: darkMode ? '#64B5F6' : 'primary.main',
                                        transform: 'scale(1.1)',
                                        backgroundColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.04)'
                                    },
                                    transition: 'all 0.2s ease-in-out'
                                }}
                            >
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                                </svg>
                            </IconButton>
                        </Tooltip>
                        
                        <Tooltip title="Toggle dark mode">
                            <IconButton
                                onClick={onThemeChange}
                                sx={{
                                    color: darkMode ? '#fff' : 'text.primary',
                                    '&:hover': {
                                        color: darkMode ? '#FFD54F' : 'primary.main',
                                        transform: 'rotate(180deg)',
                                        backgroundColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.04)'
                                    },
                                    transition: 'all 0.3s ease-in-out'
                                }}
                            >
                                {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
                            </IconButton>
                        </Tooltip>
                    </Box>
                </Box>
            </Box>
            
            {/* Spacer for fixed navigation */}
            <Box sx={{ height: '80px' }} />
            {renderContent()}
            {result && (
                <Grid
                    item
                    xs={12}
                    sx={{
                        mt: theme.spacing(2),
                        width: '100%',
                        px: theme.spacing(2),
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
                    sx={{
                        mt: theme.spacing(2),
                        width: '100%',
                        mx: 'auto',
                        maxWidth: '1400px',
                        px: theme.spacing(3),
                        py: theme.spacing(3),
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

            {/* Scroll to Top Button */}
            {showScrollTop && (
                <Fab
                    color="primary"
                    size="small"
                    onClick={handleScrollToTop}
                    sx={{
                        position: 'fixed',
                        bottom: 24,
                        right: 24,
                        zIndex: 999,
                        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                        '&:hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 6px 16px rgba(0,0,0,0.2)'
                        },
                        transition: 'all 0.3s ease-in-out'
                    }}
                    aria-label="scroll to top"
                >
                    <Tooltip title="Scroll to top">
                        <KeyboardArrowUpIcon />
                    </Tooltip>
                </Fab>
            )}

            {/* Image Modal */}
            <Modal
                open={imageModalOpen}
                onClose={handleCloseImageModal}
                aria-labelledby="image-modal-title"
                aria-describedby="image-modal-description"
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: 2
                }}
            >
                <Box sx={{
                    position: 'relative',
                    maxWidth: '90vw',
                    maxHeight: '90vh',
                    bgcolor: darkMode ? '#1a1a1a' : 'background.paper',
                    borderRadius: 2,
                    boxShadow: 24,
                    overflow: 'hidden',
                    display: 'flex',
                    flexDirection: 'column'
                }}>
                    {/* Modal Header */}
                    <Box sx={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        p: 2,
                        borderBottom: '1px solid',
                        borderColor: darkMode ? '#333' : 'divider',
                        backgroundColor: darkMode ? '#2a2a2a' : 'grey.50'
                    }}>
                        <Typography 
                            id="image-modal-title" 
                            variant="h6" 
                            component="h2"
                            sx={{ 
                                fontWeight: 'bold',
                                color: darkMode ? '#ffffff' : 'inherit',
                                flex: 1,
                                mr: 2
                            }}
                        >
                            📊 {selectedImage?.chart_type || 'Generated Chart'}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                            <Typography variant="caption" sx={{
                                color: darkMode ? '#aaa' : 'text.secondary',
                                fontSize: '0.75rem'
                            }}>
                                {selectedImage?.format} • {selectedImage?.size_kb?.toFixed(1)} KB
                            </Typography>
                            <IconButton
                                onClick={handleCloseImageModal}
                                sx={{
                                    color: darkMode ? '#fff' : 'text.primary',
                                    '&:hover': {
                                        backgroundColor: darkMode ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.04)'
                                    }
                                }}
                            >
                                <CloseIcon />
                            </IconButton>
                        </Box>
                    </Box>

                    {/* Modal Content - Image */}
                    <Box sx={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        p: 2,
                        backgroundColor: darkMode ? '#1a1a1a' : 'background.paper',
                        maxHeight: 'calc(90vh - 100px)',
                        overflow: 'auto'
                    }}>
                        {selectedImage && (
                            <img
                                src={selectedImage.url}
                                alt={selectedImage.chart_type}
                                style={{
                                    maxWidth: '100%',
                                    maxHeight: '100%',
                                    objectFit: 'contain',
                                    borderRadius: '4px',
                                    boxShadow: darkMode 
                                        ? '0 8px 32px rgba(0,0,0,0.5)' 
                                        : '0 8px 32px rgba(0,0,0,0.1)'
                                }}
                                onError={(e) => {
                                    console.error('Image failed to load:', selectedImage.url);
                                    e.target.style.display = 'none';
                                }}
                            />
                        )}
                    </Box>

                    {/* Modal Footer */}
                    <Box sx={{
                        display: 'flex',
                        justifyContent: 'center',
                        gap: 2,
                        p: 2,
                        borderTop: '1px solid',
                        borderColor: darkMode ? '#333' : 'divider',
                        backgroundColor: darkMode ? '#2a2a2a' : 'grey.50'
                    }}>
                        <Button
                            variant="outlined"
                            startIcon={<PictureAsPdfIcon />}
                            onClick={() => {
                                if (selectedImage?.url) {
                                    window.open(selectedImage.url, '_blank');
                                }
                            }}
                            sx={{
                                ...(darkMode && {
                                    borderColor: '#555',
                                    color: '#fff',
                                    '&:hover': {
                                        borderColor: '#777',
                                        backgroundColor: 'rgba(255,255,255,0.1)'
                                    }
                                })
                            }}
                        >
                            Open in New Tab
                        </Button>
                        <Button
                            variant="contained"
                            onClick={handleCloseImageModal}
                        >
                            Close
                        </Button>
                    </Box>
                </Box>
            </Modal>
        </Grid>
    );
};

export default URLChipForm;