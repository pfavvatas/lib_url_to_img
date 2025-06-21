import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Chip, FormControl, Button, useTheme, Snackbar, CircularProgress, Grid2 as Grid, TextareaAutosize, Accordion, AccordionSummary, AccordionDetails, Typography, IconButton, Tooltip, Card, CardContent, CardHeader, Switch, FormControlLabel, Fab, Collapse } from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import DeleteIcon from '@mui/icons-material/Delete';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import html2pdf from 'html2pdf.js';

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
    const [showResults, setShowResults] = useState(false); // Add this new state
    const [isNewMode, setIsNewMode] = useState(false);
    const [abortController, setAbortController] = useState(null);
    const similarityRef = useRef(null);
    
    // Experiments state
    const [experimentTestCases, setExperimentTestCases] = useState([]);
    const [selectedTestCases, setSelectedTestCases] = useState([]);
    const [experimentConfig, setExperimentConfig] = useState(null);
    const [experimentLoading, setExperimentLoading] = useState(false);
    const [experimentResults, setExperimentResults] = useState(null);
    const [experimentName, setExperimentName] = useState('');
    const [experimentFilters, setExperimentFilters] = useState({});
    const [gnuplotGuide, setGnuplotGuide] = useState(null);
    const [showGnuplotGuide, setShowGnuplotGuide] = useState(false);
    
    // Results Archive state
    const [archiveExperiments, setArchiveExperiments] = useState([]);
    const [selectedExperiment, setSelectedExperiment] = useState(null);
    const [archiveLoading, setArchiveLoading] = useState(false);
    
    // Config Builder state
    const [customConfig, setCustomConfig] = useState({
        experiment_name: '',
        available_urls: [],
        modes: [0, 1],
        levels: [1],
        url_combinations: [2, 3],
        max_combinations: 25
    });
    const [configUrlInput, setConfigUrlInput] = useState('');
    
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

    // Experiment Management Functions
    const loadExperimentConfig = async () => {
        try {
            const response = await fetch("http://localhost:5000/experiments/config");
            const data = await response.json();
            if (data.status === "success") {
                setExperimentConfig(data.config);
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            setError({ message: `Failed to load experiment config: ${error.message}` });
        }
    };

    const loadTestCases = async () => {
        setExperimentLoading(true);
        try {
            const response = await fetch("http://localhost:5000/experiments/test-cases");
            const data = await response.json();
            if (data.status === "success") {
                setExperimentTestCases(data.test_cases);
                setSuccess(`Loaded ${data.total_count} test cases`);
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            setError({ message: `Failed to load test cases: ${error.message}` });
        } finally {
            setExperimentLoading(false);
        }
    };

    const filterTestCases = async (filters) => {
        setExperimentLoading(true);
        try {
            const response = await fetch("http://localhost:5000/experiments/filter-test-cases", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ filters })
            });
            const data = await response.json();
            if (data.status === "success") {
                setExperimentTestCases(data.test_cases);
                setSuccess(`Filtered to ${data.total_count} test cases (from ${data.original_count})`);
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            setError({ message: `Failed to filter test cases: ${error.message}` });
        } finally {
            setExperimentLoading(false);
        }
    };

    const runExperimentBatch = async () => {
        if (selectedTestCases.length === 0) {
            setWarning("Please select at least one test case to run");
            return;
        }

        setExperimentLoading(true);
        setError(null);

        try {
            const response = await fetch("http://localhost:5000/experiments/run-batch", {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    experiment_name: experimentName || 'Thesis Experiment',
                    selected_test_cases: selectedTestCases
                })
            });
            const data = await response.json();

            if (data.status === "success") {
                setExperimentResults(data.experiment_summary);
                setSuccess(`Experiment completed! ${data.experiment_summary.experiment_info.successful_tests} successful tests`);
                // Play success notification sound
                playNotificationSound(true);
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

    const handleTestCaseSelection = (testCase, isSelected) => {
        if (isSelected) {
            setSelectedTestCases([...selectedTestCases, testCase]);
        } else {
            setSelectedTestCases(selectedTestCases.filter(tc => tc.id !== testCase.id));
        }
    };

    const handleSelectAllTestCases = (selectAll) => {
        if (selectAll) {
            setSelectedTestCases([...experimentTestCases]);
        } else {
            setSelectedTestCases([]);
        }
    };

    const loadGnuplotGuide = async () => {
        try {
            const response = await fetch("http://localhost:5000/experiments/gnuplot-guide");
            const data = await response.json();
            if (data.status === "success") {
                setGnuplotGuide(data.guide);
                setShowGnuplotGuide(true);
            } else {
                setError({ message: data.message });
            }
        } catch (error) {
            setError({ message: `Failed to load gnuplot guide: ${error.message}` });
        }
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

    const loadExperimentDetails = async (experimentId) => {
        setArchiveLoading(true);
        try {
            const response = await fetch(`http://localhost:5000/experiments/results/${experimentId}`);
            const data = await response.json();
            if (data.status === "success") {
                setSelectedExperiment(data.experiment_data);
                setSuccess(`Loaded experiment: ${data.experiment_data.experiment_info.name}`);
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
            // Generate test cases based on custom config
            const testCases = [];
            let testIndex = 1;

            for (const mode of customConfig.modes) {
                for (const urlCount of customConfig.url_combinations) {
                    if (urlCount <= customConfig.available_urls.length) {
                        // Create a test case
                        const selectedUrls = customConfig.available_urls.slice(0, urlCount);
                        const testCase = {
                            id: `custom_${testIndex.toString().padStart(3, '0')}_${mode}_L${customConfig.levels.join('_')}_U${urlCount}`,
                            name: `Custom Mode ${mode} - Levels ${customConfig.levels.join(',')} - ${urlCount} URLs`,
                            description: `Custom test using Mode ${mode}, levels ${customConfig.levels.join(',')}, ${urlCount} URLs`,
                            mode: mode,
                            levels: customConfig.levels,
                            urls: selectedUrls,
                            url_count: urlCount,
                            estimated_duration: urlCount * customConfig.levels.length * 0.5,
                            priority: 'custom'
                        };
                        testCases.push(testCase);
                        testIndex++;

                        if (testCases.length >= customConfig.max_combinations) {
                            break;
                        }
                    }
                }
                if (testCases.length >= customConfig.max_combinations) {
                    break;
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
                    experiment_name: customConfig.experiment_name || 'Custom Experiment',
                    selected_test_cases: testCases
                })
            });
            const data = await response.json();

            if (data.status === "success") {
                setExperimentResults(data.experiment_summary);
                setSuccess(`Custom experiment completed! ${data.experiment_summary.experiment_info.successful_tests} successful tests`);
                // Play success notification sound
                playNotificationSound(true);
                
                // Switch to experiments view to see results
                setCurrentView('experiments');
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

    // Load experiment config on component mount
    useEffect(() => {
        if (currentView === 'experiments' && !experimentConfig) {
            loadExperimentConfig();
        }
    }, [currentView, experimentConfig]);

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

        // Add similarity matrix
        const matrixTitle = document.createElement('h2');
        matrixTitle.innerHTML = 'Cosine Similarity Matrix (%)';
        matrixTitle.style.borderBottom = '2px solid #1976d2';
        matrixTitle.style.paddingBottom = '5px';
        matrixTitle.style.marginBottom = '15px';
        pdfContent.appendChild(matrixTitle);

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
                const isHighSimilarity = similarity > 80;
                const isMediumSimilarity = similarity > 50;
                const isDiagonal = rowIndex === colIndex;

                td.style.padding = '8px';
                td.style.border = '1px solid #ddd';
                td.style.textAlign = 'center';
                td.style.fontSize = '9px';
                
                if (isDiagonal) {
                    td.style.backgroundColor = '#e3f2fd';
                    td.style.fontWeight = 'bold';
                } else if (isHighSimilarity) {
                    td.style.backgroundColor = '#e8f5e8';
                } else if (isMediumSimilarity) {
                    td.style.backgroundColor = '#fff3e0';
                }

                td.innerHTML = similarity.toFixed(2);
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        pdfContent.appendChild(table);

        // Add legend
        const legendTitle = document.createElement('h3');
        legendTitle.innerHTML = 'Color Legend';
        legendTitle.style.marginTop = '20px';
        legendTitle.style.marginBottom = '10px';
        pdfContent.appendChild(legendTitle);

        const legend = document.createElement('div');
        legend.style.display = 'flex';
        legend.style.flexWrap = 'wrap';
        legend.style.gap = '15px';
        legend.style.fontSize = '10px';

        const legendItems = [
            { color: '#e3f2fd', label: 'Same Site (100%)' },
            { color: '#e8f5e8', label: 'High Similarity (>80%)' },
            { color: '#fff3e0', label: 'Medium Similarity (>50%)' },
            { color: 'white', label: 'Low Similarity (≤50%)' }
        ];

        legendItems.forEach(item => {
            const legendItem = document.createElement('div');
            legendItem.style.display = 'flex';
            legendItem.style.alignItems = 'center';
            legendItem.style.gap = '5px';
            legendItem.innerHTML = `
                <div style="width: 15px; height: 15px; background-color: ${item.color}; border: 1px solid #ccc;"></div>
                <span>${item.label}</span>
            `;
            legend.appendChild(legendItem);
        });
        pdfContent.appendChild(legend);

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

    // Function to render site similarity results
    const renderSiteSimilarityResults = (siteSimilarity, level = null) => {
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
                        📊 Cosine Similarity Matrix ({summary.total_sites} sites)
                    </Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ p: 3 }}>
                    {/* Summary Statistics */}
                    <Box sx={{ 
                        mb: theme.spacing(3),
                        p: 2,
                        backgroundColor: 'background.paper',
                        borderRadius: 2,
                        border: '1px solid',
                        borderColor: 'divider'
                    }}>
                        <Typography variant="h6" gutterBottom>📊 Summary Statistics</Typography>
                        <Box sx={{ 
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                            gap: 2
                        }}>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Total Sites</Typography>
                                <Typography variant="h6" color="primary">{summary.total_sites}</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Average Similarity</Typography>
                                <Typography variant="h6" color="primary">{summary.average_similarity.toFixed(2)}%</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Maximum Similarity</Typography>
                                <Typography variant="h6" color="primary">{summary.max_similarity.toFixed(2)}%</Typography>
                            </Box>
                            <Box>
                                <Typography variant="subtitle2" color="text.secondary">Minimum Similarity</Typography>
                                <Typography variant="h6" color="primary">{summary.min_similarity.toFixed(2)}%</Typography>
                            </Box>
                        </Box>
                    </Box>

                    {/* Similarity Matrix Table */}
                    <Box sx={{ mb: theme.spacing(2) }}>
                        <Typography variant="h6" gutterBottom>🔢 Cosine Similarity Matrix (%)</Typography>
                        <Box sx={{ 
                            overflowX: 'auto',
                            maxHeight: '500px',
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1
                        }}>
                            <table style={{ 
                                width: '100%', 
                                borderCollapse: 'collapse',
                                minWidth: 'auto',
                                fontSize: '0.9rem'
                            }}>
                                <thead>
                                    <tr style={{ backgroundColor: theme.palette.grey[100] }}>
                                        <th style={{ 
                                            padding: '12px', 
                                            border: '1px solid #ddd',
                                            textAlign: 'left',
                                            fontWeight: 'bold',
                                            position: 'sticky',
                                            top: 0,
                                            backgroundColor: theme.palette.grey[100],
                                            zIndex: 1
                                        }}>
                                            Site
                                        </th>
                                        {sites.map((site, index) => (
                                            <th key={index} style={{ 
                                                padding: '8px 12px', 
                                                border: '1px solid #ddd',
                                                textAlign: 'center',
                                                fontWeight: 'bold',
                                                position: 'sticky',
                                                top: 0,
                                                backgroundColor: theme.palette.grey[100],
                                                zIndex: 1,
                                                minWidth: '80px',
                                                maxWidth: '100px',
                                                fontSize: '0.9rem'
                                            }}>
                                                <Tooltip title={site} arrow>
                                                    <span style={{ 
                                                        fontWeight: 'bold', 
                                                        color: theme.palette.primary.main 
                                                    }}>
                                                        {createSiteLabel(index)}
                                                    </span>
                                                </Tooltip>
                                            </th>
                                        ))}
                                    </tr>
                                </thead>
                                <tbody>
                                    {sites.map((rowSite, rowIndex) => (
                                        <tr key={rowIndex}>
                                            <td style={{ 
                                                padding: '8px 12px', 
                                                border: '1px solid #ddd',
                                                fontWeight: 'bold',
                                                backgroundColor: theme.palette.grey[50],
                                                position: 'sticky',
                                                left: 0,
                                                zIndex: 1,
                                                minWidth: '80px',
                                                maxWidth: '100px',
                                                fontSize: '0.9rem',
                                                textAlign: 'center'
                                            }}>
                                                <Tooltip title={rowSite} arrow>
                                                    <span style={{ 
                                                        fontWeight: 'bold', 
                                                        color: theme.palette.primary.main 
                                                    }}>
                                                        {createSiteLabel(rowIndex)}
                                                    </span>
                                                </Tooltip>
                                            </td>
                                            {sites.map((colSite, colIndex) => {
                                                const similarity = matrix[rowSite][colSite];
                                                const isHighSimilarity = similarity > 80;
                                                const isMediumSimilarity = similarity > 50;
                                                const isDiagonal = rowIndex === colIndex;
                                                
                                                return (
                                                    <td key={colIndex} style={{ 
                                                        padding: '8px', 
                                                        border: '1px solid #ddd',
                                                        textAlign: 'center',
                                                        fontSize: '0.85rem',
                                                        minWidth: '60px',
                                                        backgroundColor: isDiagonal 
                                                            ? theme.palette.primary.light 
                                                            : isHighSimilarity 
                                                                ? theme.palette.success.light 
                                                                : isMediumSimilarity 
                                                                    ? theme.palette.warning.light 
                                                                    : 'white',
                                                        color: isDiagonal 
                                                            ? theme.palette.primary.contrastText 
                                                            : isHighSimilarity 
                                                                ? theme.palette.success.contrastText 
                                                                : isMediumSimilarity 
                                                                    ? theme.palette.warning.contrastText 
                                                                    : 'inherit',
                                                        fontWeight: isDiagonal ? 'bold' : 'normal'
                                                    }}>
                                                        {similarity.toFixed(2)}
                                                    </td>
                                                );
                                            })}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </Box>
                    </Box>

                    {/* Site Reference - Compact */}
                    <Box sx={{ 
                        mt: 2,
                        p: 1.5,
                        backgroundColor: 'grey.50',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'grey.300'
                    }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                            Site Labels:
                        </Typography>
                        <Box sx={{ 
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 0.5,
                            maxHeight: '150px',
                            overflowY: 'auto'
                        }}>
                            {sites.map((site, index) => (
                                <Box key={index} sx={{ 
                                    display: 'flex', 
                                    alignItems: 'flex-start', 
                                    gap: 1,
                                    py: 0.5,
                                    px: 0.5,
                                    border: '1px solid',
                                    borderColor: 'grey.200',
                                    borderRadius: 0.5,
                                    backgroundColor: 'white'
                                }}>
                                    <Typography variant="caption" sx={{ 
                                        fontWeight: 'bold', 
                                        color: 'primary.main',
                                        minWidth: '50px',
                                        mt: 0.25
                                    }}>
                                        {createSiteLabel(index)}:
                                    </Typography>
                                    <Tooltip title={site} arrow placement="top">
                                        <Typography variant="caption" sx={{ 
                                            color: 'text.secondary',
                                            flex: 1,
                                            fontSize: '0.7rem',
                                            lineHeight: 1.3,
                                            wordBreak: 'break-all',
                                            cursor: 'help'
                                        }}>
                                            {site}
                                        </Typography>
                                    </Tooltip>
                                </Box>
                            ))}
                        </Box>
                    </Box>

                    {/* Color Legend */}
                    <Box sx={{ 
                        display: 'flex', 
                        flexWrap: 'wrap', 
                        gap: 2, 
                        mt: 1,
                        p: 1.5,
                        backgroundColor: 'grey.50',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'grey.300'
                    }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mr: 1 }}>Colors:</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Box sx={{ 
                                width: 16, 
                                height: 16, 
                                backgroundColor: theme.palette.primary.light,
                                border: '1px solid #ccc'
                            }} />
                            <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>Same Site</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Box sx={{ 
                                width: 16, 
                                height: 16, 
                                backgroundColor: theme.palette.success.light,
                                border: '1px solid #ccc'
                            }} />
                            <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>High (&gt;80%)</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Box sx={{ 
                                width: 16, 
                                height: 16, 
                                backgroundColor: theme.palette.warning.light,
                                border: '1px solid #ccc'
                            }} />
                            <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>Medium (&gt;50%)</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <Box sx={{ 
                                width: 16, 
                                height: 16, 
                                backgroundColor: 'white',
                                border: '1px solid #ccc'
                            }} />
                            <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>Low (≤50%)</Typography>
                        </Box>
                    </Box>

                    {/* Action Buttons */}
                    <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
                        <Tooltip title="Copy similarity matrix to clipboard">
                            <IconButton 
                                size="small" 
                                onClick={() => handleCopyToClipboard(JSON.stringify(matrix, null, 2))}
                                sx={{ 
                                    backgroundColor: 'grey.100',
                                    '&:hover': { backgroundColor: 'grey.200' }
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
        console.log("Current result state:", result);
        if (!result) return null;

        // Helper function to collect all HTML files from any result structure
        const collectAllHtmlFiles = (resultData) => {
            let allFiles = [];
            
            console.log("🔍 DEBUG: collectAllHtmlFiles input:", resultData);
            
            if (resultData.html_files) {
                console.log("📁 Found top-level html_files:", resultData.html_files.length);
                allFiles = allFiles.concat(resultData.html_files);
            }
            
            if (resultData.domain_results) {
                console.log("🌐 Found domain_results:", resultData.domain_results.length);
                resultData.domain_results.forEach((domainResult, index) => {
                    console.log(`📊 Domain ${index + 1} (${domainResult.domain}):`, domainResult.html_files?.length || 0, "files");
                    if (domainResult.html_files) {
                        domainResult.html_files.forEach(file => {
                            console.log(`  - File domain: ${file.domain}, clean_domain: ${file.clean_domain}, filename: ${file.filename}`);
                        });
                        allFiles = allFiles.concat(domainResult.html_files);
                    }
                });
            }
            
            // Remove duplicates based on filename (backend bug workaround)
            const uniqueFiles = allFiles.filter((file, index, self) => 
                index === self.findIndex(f => f.filename === file.filename)
            );
            
            console.log("📁 Total collected files:", allFiles.length);
            console.log("📁 After deduplication:", uniqueFiles.length);
            console.log("📊 Files by domain:", uniqueFiles.reduce((acc, file) => {
                const domain = file.domain || file.clean_domain || 'unknown';
                acc[domain] = (acc[domain] || 0) + 1;
                return acc;
            }, {}));
            
            // Show warning if we detected duplicates (backend bug)
            if (allFiles.length > uniqueFiles.length) {
                console.warn("🚨 BACKEND BUG DETECTED: Duplicate files found and removed", {
                    total: allFiles.length,
                    unique: uniqueFiles.length,
                    duplicates: allFiles.length - uniqueFiles.length
                });
                setWarning(`⚠️ Backend issue detected: ${allFiles.length - uniqueFiles.length} duplicate files removed. Domain processing may have incorrect metadata.`);
            }
            
            return uniqueFiles;
        };

        // Render unified HTML files section
        const renderUnifiedHtmlFilesSection = (resultData) => {
            const allHtmlFiles = collectAllHtmlFiles(resultData);
            
            if (allHtmlFiles.length === 0) return null;

            // Group files by level
            const filesByLevel = allHtmlFiles.reduce((acc, file) => {
                const level = file.level || 'unknown';
                if (!acc[level]) acc[level] = [];
                acc[level].push(file);
                return acc;
            }, {});

            // Sort levels numerically
            const sortedLevels = Object.keys(filesByLevel).sort((a, b) => {
                if (a === 'unknown') return 1;
                if (b === 'unknown') return -1;
                return parseInt(a) - parseInt(b);
            });

            return (
                <Accordion 
                    defaultExpanded={true}
                    sx={{ 
                        mb: theme.spacing(3),
                        '&:before': {
                            display: 'none',
                        },
                        boxShadow: '0 4px 8px rgba(0,0,0,0.15)',
                        borderRadius: '12px !important',
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
                        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                            📁 Generated Files ({allHtmlFiles.length} files)
                        </Typography>
                    </AccordionSummary>
                    <AccordionDetails sx={{ p: 3 }}>
                        {sortedLevels.map(level => (
                            <Accordion 
                                key={level}
                                sx={{ 
                                    mb: 2,
                                    '&:before': { display: 'none' },
                                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                    borderRadius: '8px !important',
                                    overflow: 'hidden'
                                }}
                            >
                                <AccordionSummary 
                                    expandIcon={<ExpandMoreIcon />}
                                    sx={{
                                        backgroundColor: 'grey.200',
                                        '&:hover': {
                                            backgroundColor: 'grey.300',
                                            color: 'text.primary',
                                        },
                                        '& .MuiAccordionSummary-expandIconWrapper': {
                                            color: 'inherit'
                                        }
                                    }}
                                >
                                    <Typography sx={{ fontWeight: 'bold' }}>
                                        📊 Level {level} ({filesByLevel[level].length} files)
                                    </Typography>
                                </AccordionSummary>
                                <AccordionDetails sx={{ p: 3 }}>
                                    {(() => {
                                        // Group files by domain within each level
                                        // FIXED: Use the correct domain from API structure to handle backend bug
                                        const filesByDomain = {};
                                        
                                        filesByLevel[level].forEach(file => {
                                            // Try to get the correct domain from the file's metadata
                                            let correctDomain = file.domain || file.clean_domain || 'unknown';
                                            
                                            // If we have domain_results, try to find the correct domain by matching HTML files
                                            if (result.domain_results) {
                                                for (const domainResult of result.domain_results) {
                                                    if (domainResult.html_files && domainResult.html_files.some(f => f.filename === file.filename)) {
                                                        correctDomain = domainResult.domain.replace('www.', '');
                                                        break;
                                                    }
                                                }
                                            }
                                            
                                            if (!filesByDomain[correctDomain]) filesByDomain[correctDomain] = [];
                                            filesByDomain[correctDomain].push({...file, corrected_domain: correctDomain});
                                        });

                                        return Object.entries(filesByDomain).map(([domain, domainFiles]) => (
                                            <Box key={domain} sx={{ mb: 3 }}>
                                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mb: 2, color: 'primary.main' }}>
                                                    🌐 {domain} ({domainFiles.length} files)
                                                </Typography>
                                                <Grid container spacing={2}>
                                                    {domainFiles.map((file, index) => (
                                                        <Grid item xs={12} sm={6} md={4} key={index}>
                                                            <Card 
                                                                sx={{ 
                                                                    cursor: 'pointer',
                                                                    transition: 'all 0.2s ease-in-out',
                                                                    '&:hover': {
                                                                        transform: 'translateY(-2px)',
                                                                        boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
                                                                    }
                                                                }}
                                                                onClick={() => window.open(`http://localhost:5000/${file.path}`, '_blank')}
                                                            >
                                                                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                                                    <Typography 
                                                                        variant="subtitle2" 
                                                                        sx={{ 
                                                                            fontWeight: 'bold',
                                                                            mb: 1,
                                                                            overflow: 'hidden',
                                                                            textOverflow: 'ellipsis',
                                                                            whiteSpace: 'nowrap'
                                                                        }}
                                                                        title={file.title || file.filename}
                                                                    >
                                                                        {file.title || file.filename}
                                                                    </Typography>
                                                                    <Typography 
                                                                        variant="caption" 
                                                                        color="text.secondary"
                                                                        sx={{ 
                                                                            display: 'block',
                                                                            mb: 1,
                                                                            overflow: 'hidden',
                                                                            textOverflow: 'ellipsis',
                                                                            whiteSpace: 'nowrap'
                                                                        }}
                                                                        title={file.url}
                                                                    >
                                                                        {file.url}
                                                                    </Typography>
                                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                                        <Typography variant="caption" color="text.secondary">
                                                                            📄 {file.url_identifier || file.short_id}
                                                                        </Typography>
                                                                        <Typography variant="caption" color="text.secondary">
                                                                            {file.file_size_kb ? `💾 ${file.file_size_kb.toFixed(1)} KB` : ''}
                                                                        </Typography>
                                                                    </Box>
                                                                </CardContent>
                                                            </Card>
                                                        </Grid>
                                                    ))}
                                                </Grid>
                                            </Box>
                                        ));
                                    })()}
                                </AccordionDetails>
                            </Accordion>
                        ))}
                    </AccordionDetails>
                </Accordion>
            );
        };

        // Handle domain-based results (mode 1)
        if (result.domain_results) {
            return (
                <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1200px', mx: 'auto' }}>
                    <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                        🌐 Domain-Based Processing Results (Mode 1)
                    </Typography>
                    

                    
                    {/* Unified HTML Files Section */}
                    {renderUnifiedHtmlFilesSection(result)}
                    
                    {/* Combined Site Similarity Results for All Domains */}
                    {result.domain_results && result.domain_results.some(dr => dr.processed_clusters && dr.processed_clusters.some(pc => pc.processed_data && pc.processed_data.site_similarity)) && (
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
                                    🔍 Site Similarity Analysis by Domain
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
                                            {renderSiteSimilarityResults(processedCluster.processed_data.site_similarity, processedCluster.level)}
                                        </div>
                                    ))
                                ))}
                            </AccordionDetails>
                        </Accordion>
                    )}
                    
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
                                    backgroundColor: domainResult.status === 'success' ? 'grey.200' : 'error.light',
                                    '&:hover': {
                                        backgroundColor: domainResult.status === 'success' ? 'grey.300' : 'error.main',
                                        color: domainResult.status === 'success' ? 'text.primary' : 'white',
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
                                        <Grid container spacing={2}>
                                            {domainResult.html_files.map((file, index) => (
                                                <Grid item xs={12} sm={6} md={4} key={index}>
                                                    <Card 
                                                        sx={{ 
                                                            cursor: 'pointer',
                                                            transition: 'all 0.2s ease-in-out',
                                                            '&:hover': {
                                                                transform: 'translateY(-2px)',
                                                                boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
                                                            }
                                                        }}
                                                        onClick={() => window.open(`http://localhost:5000/${file.path}`, '_blank')}
                                                    >
                                                        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                                                            <Typography 
                                                                variant="subtitle2" 
                                                                sx={{ 
                                                                    fontWeight: 'bold',
                                                                    mb: 1,
                                                                    overflow: 'hidden',
                                                                    textOverflow: 'ellipsis',
                                                                    whiteSpace: 'nowrap'
                                                                }}
                                                                title={file.title || file.filename}
                                                            >
                                                                {file.title || file.filename}
                                                            </Typography>
                                                            <Typography 
                                                                variant="caption" 
                                                                color="text.secondary"
                                                                sx={{ 
                                                                    display: 'block',
                                                                    mb: 1,
                                                                    overflow: 'hidden',
                                                                    textOverflow: 'ellipsis',
                                                                    whiteSpace: 'nowrap'
                                                                }}
                                                                title={file.url}
                                                            >
                                                                {file.url}
                                                            </Typography>
                                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                                <Typography variant="caption" color="text.secondary">
                                                                    📄 {file.url_identifier || file.short_id}
                                                                </Typography>
                                                                <Typography variant="caption" color="text.secondary">
                                                                    {file.file_size_kb ? `💾 ${file.file_size_kb.toFixed(1)} KB` : ''}
                                                                </Typography>
                                                            </Box>
                                                        </CardContent>
                                                    </Card>
                                                </Grid>
                                            ))}
                                        </Grid>
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
                                                        backgroundColor: 'grey.200',
                                                        '&:hover': {
                                                            backgroundColor: 'grey.300',
                                                            color: 'text.primary',
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
                    
                    {/* Timing Logs Section for Domain Results */}
                    {result.timing_logs && renderTimingLogs(result.timing_logs)}
                </Box>
            );
        }

        // Original results rendering (mode 0)
        return (
            <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1200px', mx: 'auto' }}>
                <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
                    🧮 Clustering Results
                </Typography>
                
                {/* Unified HTML Files Section */}
                {renderUnifiedHtmlFilesSection(result)}
                
                {/* Site Similarity Results by Level */}
                {result.processed_clusters && result.processed_clusters.map((processedCluster, clusterIndex) => (
                    processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                    <div key={`similarity-${clusterIndex}`}>
                        <Typography variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
                            🔍 Site Similarity Analysis - Level {processedCluster.level}
                        </Typography>
                        {renderSiteSimilarityResults(processedCluster.processed_data.site_similarity, processedCluster.level)}
                    </div>
                ))}
                
                {/* Original HTML Files Section - keeping for backup */}
                {false && result.html_files && result.html_files.length > 0 && (
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
                                🧮 Level {clusterResult.level} - {clusterResult.status === 'error' ? '❌' : '✅'} {clusterResult.message}
                            </Typography>
                        </AccordionSummary>
                        <AccordionDetails sx={{ p: 3 }}>
                            {/* Show error message if status is error */}
                            {clusterResult.status === 'error' && (
                                <Box sx={{ mb: theme.spacing(2) }}>
                                    <Typography variant="h6" gutterBottom color="error">
                                        ❌ Error in Level {clusterResult.level}
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
                                    <Typography variant="h6" gutterBottom>
                                        Cluster Info
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
                                    <Typography variant="h6" gutterBottom>
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
                                backgroundColor: 'grey.200',
                                '&:hover': {
                                    backgroundColor: 'grey.300',
                                    color: 'text.primary',
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
                        <Box sx={{ margin: '0 30%' }}>
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
                            />
                        </Box>
                        <Box sx={{ position: 'relative', margin: '0 30%', mt: theme.spacing(2), display: 'flex', justifyContent: 'center' }}>
                            <Box sx={{ position: 'absolute', top: '-10px', left: '10px', backgroundColor: 'white', padding: '0 5px', fontWeight: 'bold' }}>📊 Levels</Box>
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
                                label={isNewMode ? "🌐 Process by Domain" : "📦 Process All Together"}
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
            case 'experiments':
                return (
                    <Box sx={{ width: '100%', maxWidth: '1400px', margin: '0 auto', p: 3 }}>
                        <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
                            🧪 Experiment Management - Thesis Data Collection
                        </Typography>

                        {/* Experiment Configuration Display */}
                        {experimentConfig && (
                            <Accordion sx={{ mb: 3 }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                    <Typography variant="h6">📋 Experiment Configuration</Typography>
                                </AccordionSummary>
                                <AccordionDetails>
                                    <Grid container spacing={2}>
                                        <Grid item xs={12} md={6}>
                                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Available URLs:</Typography>
                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                                                {experimentConfig.test_configuration.available_urls.map((url, index) => (
                                                    <Chip key={index} label={url} size="small" color="primary" />
                                                ))}
                                            </Box>
                                        </Grid>
                                        <Grid item xs={12} md={6}>
                                            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>Test Parameters:</Typography>
                                            <Typography variant="body2">Modes: {experimentConfig.test_configuration.test_parameters.modes.join(', ')}</Typography>
                                            <Typography variant="body2">Max URLs per test: {experimentConfig.test_configuration.max_urls_per_test}</Typography>
                                            <Typography variant="body2">URL Set Sizes: {Object.values(experimentConfig.test_configuration.url_combinations).flat().join(', ')}</Typography>
                                        </Grid>
                                    </Grid>
                                </AccordionDetails>
                            </Accordion>
                        )}

                        {/* Experiment Controls */}
                        <Card sx={{ mb: 3, p: 3 }}>
                            <Typography variant="h6" gutterBottom>🚀 Experiment Controls</Typography>
                            <Grid container spacing={3} alignItems="center">
                                <Grid item xs={12} md={4}>
                                    <TextField
                                        fullWidth
                                        label="Experiment Name"
                                        value={experimentName}
                                        onChange={(e) => setExperimentName(e.target.value)}
                                        placeholder="e.g., Thesis_Mode_Comparison_2024"
                                    />
                                </Grid>
                                <Grid item xs={12} md={8}>
                                    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                                        <Button 
                                            variant="outlined" 
                                            onClick={loadTestCases}
                                            disabled={experimentLoading}
                                        >
                                            📊 Load All Test Cases
                                        </Button>
                                        <Button 
                                            variant="outlined" 
                                            onClick={() => filterTestCases({ priority: ['high', 'medium'] })}
                                            disabled={experimentLoading}
                                        >
                                            🔍 Filter High/Medium Priority
                                        </Button>
                                        <Button 
                                            variant="outlined" 
                                            onClick={() => filterTestCases({ max_url_count: 5 })}
                                            disabled={experimentLoading}
                                        >
                                            📱 Small Tests (≤5 URLs)
                                        </Button>
                                        <Button 
                                            variant="outlined" 
                                            onClick={loadGnuplotGuide}
                                            sx={{ backgroundColor: 'info.light', color: 'info.contrastText' }}
                                        >
                                            📊 Gnuplot Guide
                                        </Button>
                                    </Box>
                                </Grid>
                            </Grid>
                        </Card>

                        {/* Test Cases Selection */}
                        {experimentTestCases.length > 0 && (
                            <Card sx={{ mb: 3 }}>
                                <CardHeader 
                                    title={`📝 Test Cases (${experimentTestCases.length} available)`}
                                    action={
                                        <Box>
                                            <FormControlLabel
                                                control={
                                                    <Switch
                                                        checked={selectedTestCases.length === experimentTestCases.length}
                                                        onChange={(e) => handleSelectAllTestCases(e.target.checked)}
                                                    />
                                                }
                                                label="Select All"
                                            />
                                            <Typography variant="caption" sx={{ ml: 2 }}>
                                                Selected: {selectedTestCases.length}
                                            </Typography>
                                        </Box>
                                    }
                                />
                                <CardContent sx={{ maxHeight: '400px', overflow: 'auto' }}>
                                    <Grid container spacing={2}>
                                        {experimentTestCases.map((testCase, index) => (
                                            <Grid item xs={12} sm={6} md={4} key={testCase.id}>
                                                <Card 
                                                    sx={{ 
                                                        border: selectedTestCases.some(tc => tc.id === testCase.id) ? '2px solid' : '1px solid',
                                                        borderColor: selectedTestCases.some(tc => tc.id === testCase.id) ? 'primary.main' : 'divider',
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s'
                                                    }}
                                                    onClick={() => handleTestCaseSelection(testCase, !selectedTestCases.some(tc => tc.id === testCase.id))}
                                                >
                                                    <CardContent sx={{ p: 2 }}>
                                                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                            {testCase.name}
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                                            {testCase.id}
                                                        </Typography>
                                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
                                                            <Chip label={`Mode ${testCase.mode}`} size="small" color={testCase.mode === 0 ? 'primary' : 'secondary'} />
                                                            <Chip label={`${testCase.url_count} URLs`} size="small" />
                                                            <Chip label={testCase.priority} size="small" color={testCase.priority === 'high' ? 'error' : testCase.priority === 'medium' ? 'warning' : 'default'} />
                                                        </Box>
                                                        <Typography variant="caption" color="text.secondary">
                                                            Est. {testCase.estimated_duration.toFixed(1)} min
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                                                            Levels: {Array.isArray(testCase.levels) ? testCase.levels.join(', ') : testCase.levels}
                                                        </Typography>
                                                    </CardContent>
                                                </Card>
                                            </Grid>
                                        ))}
                                    </Grid>
                                </CardContent>
                            </Card>
                        )}

                        {/* Run Experiment Button */}
                        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
                            <Button
                                variant="contained"
                                color="primary"
                                size="large"
                                onClick={runExperimentBatch}
                                disabled={experimentLoading || selectedTestCases.length === 0}
                                sx={{ 
                                    borderRadius: '20px',
                                    px: 4,
                                    py: 1.5,
                                    fontSize: '1.1rem'
                                }}
                            >
                                {experimentLoading ? (
                                    <>
                                        <CircularProgress size={20} sx={{ mr: 2 }} />
                                        Running Experiments...
                                    </>
                                ) : (
                                    <>
                                        🚀 Run {selectedTestCases.length} Selected Tests
                                    </>
                                )}
                            </Button>
                        </Box>

                        {/* Experiment Results */}
                        {experimentResults && (
                            <Box sx={{ width: '100%', mt: theme.spacing(4), maxWidth: '1200px', mx: 'auto' }}>
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
                                            <Grid item xs={12} md={6}>
                                                <Typography variant="h6" gutterBottom>📊 Gnuplot Data Generated</Typography>
                                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                                    Data files for thesis analysis have been created and are ready for gnuplot visualization.
                                                    Check the experiment results folder for:
                                                </Typography>
                                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                    <Chip label="📊 processing_times.dat" size="small" />
                                                    <Chip label="🎯 cluster_counts.dat" size="small" />
                                                    <Chip label="📄 html_file_counts.dat" size="small" />
                                                    <Chip label="📈 *.gnuplot scripts" size="small" />
                                                </Box>
                                                <Box sx={{ mt: 2 }}>
                                                    <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                        To generate plots:
                                                    </Typography>
                                                    <Typography variant="caption" sx={{ 
                                                        fontFamily: 'monospace',
                                                        fontSize: '0.75rem',
                                                        display: 'block',
                                                        backgroundColor: 'grey.100',
                                                        p: 1,
                                                        borderRadius: 1
                                                    }}>
                                                        cd experiment_results/[timestamp]_[name]/gnuplot_data<br/>
                                                        gnuplot processing_time_plot.gnuplot<br/>
                                                        gnuplot cluster_count_plot.gnuplot
                                                    </Typography>
                                                </Box>
                                            </Grid>
                                        </Grid>
                                    </CardContent>
                                </Card>

                                {/* Process each result with better visual separation */}
                                {experimentResults.results && experimentResults.results.map((result, index) => {
                                    const cardId = `experiment-result-${index}`;
                                    const collapsed = isCardCollapsed(cardId);
                                    
                                    return result.status === 'success' && (
                                        <Card key={index} sx={{ 
                                            mb: 4, 
                                            border: '2px solid',
                                            borderColor: 'success.light',
                                            borderRadius: 3,
                                            overflow: 'hidden',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
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
                                                <CardContent sx={{ p: 3 }}>

                                                {/* Use the same renderUnifiedHtmlFilesSection function */}
                                                {(() => {
                                                    const collectAllHtmlFiles = (resultData) => {
                                                        let allFiles = [];
                                                        
                                                        if (resultData.html_files) {
                                                            allFiles = allFiles.concat(resultData.html_files);
                                                        }
                                                        
                                                        if (resultData.domain_results) {
                                                            resultData.domain_results.forEach((domainResult) => {
                                                                if (domainResult.html_files) {
                                                                    allFiles = allFiles.concat(domainResult.html_files);
                                                                }
                                                            });
                                                        }
                                                        
                                                        const uniqueFiles = allFiles.filter((file, index, self) => 
                                                            index === self.findIndex(f => f.filename === file.filename)
                                                        );
                                                        
                                                        return uniqueFiles;
                                                    };

                                                    const allHtmlFiles = collectAllHtmlFiles(result);
                                                    if (allHtmlFiles.length === 0) return null;

                                                    const filesByLevel = allHtmlFiles.reduce((acc, file) => {
                                                        const level = file.level || 'unknown';
                                                        if (!acc[level]) acc[level] = [];
                                                        acc[level].push(file);
                                                        return acc;
                                                    }, {});

                                                    const sortedLevels = Object.keys(filesByLevel).sort((a, b) => {
                                                        if (a === 'unknown') return 1;
                                                        if (b === 'unknown') return -1;
                                                        return parseInt(a) - parseInt(b);
                                                    });

                                                    return (
                                                        <Accordion 
                                                            sx={{ 
                                                                mb: theme.spacing(2),
                                                                '&:before': { display: 'none' },
                                                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
                                                                borderRadius: '8px !important',
                                                                overflow: 'hidden'
                                                            }}
                                                        >
                                                            <AccordionSummary 
                                                                expandIcon={<ExpandMoreIcon />}
                                                                sx={{
                                                                    backgroundColor: 'grey.200',
                                                                    '&:hover': {
                                                                        backgroundColor: 'grey.300',
                                                                    },
                                                                }}
                                                            >
                                                                <Typography sx={{ fontWeight: 'bold' }}>
                                                                    📁 Generated Files ({allHtmlFiles.length} files)
                                                                </Typography>
                                                            </AccordionSummary>
                                                            <AccordionDetails sx={{ p: 2 }}>
                                                                {sortedLevels.map(level => (
                                                                    <Box key={level} sx={{ mb: 2 }}>
                                                                        <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1, color: 'primary.main' }}>
                                                                            📊 Level {level} ({filesByLevel[level].length} files)
                                                                        </Typography>
                                                                        <Grid container spacing={1}>
                                                                            {filesByLevel[level].map((file, fileIndex) => (
                                                                                <Grid item xs={12} sm={6} md={4} key={fileIndex}>
                                                                                    <Card 
                                                                                        sx={{ 
                                                                                            cursor: 'pointer',
                                                                                            transition: 'all 0.2s ease-in-out',
                                                                                            '&:hover': {
                                                                                                transform: 'translateY(-1px)',
                                                                                                boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                                                                                            }
                                                                                        }}
                                                                                        onClick={() => window.open(`http://localhost:5000/${file.path}`, '_blank')}
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
                                                                                                    whiteSpace: 'nowrap'
                                                                                                }}
                                                                                                title={file.title || file.filename}
                                                                                            >
                                                                                                {file.title || file.filename}
                                                                                            </Typography>
                                                                                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>
                                                                                                {file.file_size_kb ? `${file.file_size_kb.toFixed(1)} KB` : ''}
                                                                                            </Typography>
                                                                                        </CardContent>
                                                                                    </Card>
                                                                                </Grid>
                                                                            ))}
                                                                        </Grid>
                                                                    </Box>
                                                                ))}
                                                            </AccordionDetails>
                                                        </Accordion>
                                                    );
                                                })()}

                                                {/* Site Similarity Results */}
                                                {result.processed_clusters && result.processed_clusters.map((processedCluster, clusterIndex) => (
                                                    processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                                    <div key={`similarity-${clusterIndex}`}>
                                                        <Typography variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
                                                            🔍 Site Similarity Analysis - Level {processedCluster.level}
                                                        </Typography>
                                                        {renderSiteSimilarityResults(processedCluster.processed_data.site_similarity, processedCluster.level)}
                                                    </div>
                                                ))}

                                                {/* Clustering Results Summary */}
                                                {result.clustering_results && result.clustering_results.map((clusterResult, clusterIndex) => (
                                                    <Accordion 
                                                        key={`cluster-${clusterIndex}`} 
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
                                                                backgroundColor: clusterResult.status === 'error' ? 'error.light' : 'grey.100',
                                                                '&:hover': {
                                                                    backgroundColor: clusterResult.status === 'error' ? 'error.main' : 'grey.200',
                                                                }
                                                            }}
                                                        >
                                                            <Typography sx={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                                                                🧮 Level {clusterResult.level} - {clusterResult.status === 'error' ? '❌' : '✅'} {clusterResult.message}
                                                            </Typography>
                                                        </AccordionSummary>
                                                        <AccordionDetails sx={{ p: 2 }}>
                                                            {clusterResult.status === 'error' ? (
                                                                <Typography variant="body2" color="error">
                                                                    {clusterResult.message}
                                                                </Typography>
                                                            ) : (
                                                                clusterResult.cluster_info && (
                                                                    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1 }}>
                                                                        <Box>
                                                                            <Typography variant="caption" color="text.secondary">Clusters</Typography>
                                                                            <Typography variant="subtitle2">{clusterResult.cluster_info.num_clusters}</Typography>
                                                                        </Box>
                                                                        <Box>
                                                                            <Typography variant="caption" color="text.secondary">DBCV Score</Typography>
                                                                            <Typography variant="subtitle2">{clusterResult.cluster_info.dbcv_score?.toFixed(3)}</Typography>
                                                                        </Box>
                                                                        <Box>
                                                                            <Typography variant="caption" color="text.secondary">Attributes</Typography>
                                                                            <Typography variant="subtitle2">{clusterResult.cluster_info.useful_attributes?.length || 0}</Typography>
                                                                        </Box>
                                                                    </Box>
                                                                )
                                                            )}
                                                        </AccordionDetails>
                                                    </Accordion>
                                                ))}
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
                    <Box sx={{ width: '100%', maxWidth: '1400px', margin: '0 auto', p: 3 }}>
                        <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
                            📊 Results Archive - Previous Experiments
                        </Typography>

                        {/* Archive Controls */}
                        <Card sx={{ mb: 3 }}>
                            <CardHeader title="🗂️ Experiment Archive Controls" />
                            <CardContent sx={{ p: 3 }}>
                                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
                                    <Button 
                                        variant="outlined" 
                                        onClick={loadArchiveExperiments}
                                        disabled={archiveLoading}
                                        sx={{ borderRadius: '20px' }}
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
                                            sx={{ borderRadius: '20px' }}
                                        >
                                            ⬅️ Back to List
                                        </Button>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>

                        {/* Experiment Selection */}
                        {!selectedExperiment && archiveExperiments.length > 0 && (
                            <Card sx={{ mb: 3 }}>
                                <CardHeader title={`📚 Available Experiments (${archiveExperiments.length})`} />
                                <CardContent sx={{ maxHeight: '500px', overflow: 'auto' }}>
                                    <Grid container spacing={3}>
                                        {archiveExperiments.map((experiment, index) => (
                                            <Grid item xs={12} sm={6} md={4} key={experiment.id}>
                                                <Card 
                                                    sx={{ 
                                                        cursor: 'pointer',
                                                        transition: 'all 0.2s',
                                                        '&:hover': {
                                                            transform: 'translateY(-2px)',
                                                            boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
                                                        },
                                                        border: '1px solid',
                                                        borderColor: 'divider'
                                                    }}
                                                    onClick={() => loadExperimentDetails(experiment.id)}
                                                >
                                                    <CardContent sx={{ p: 2 }}>
                                                        <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1, fontSize: '1rem' }}>
                                                            {experiment.name}
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                                            {experiment.timestamp}
                                                        </Typography>
                                                        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1, mb: 1 }}>
                                                            <Box>
                                                                <Typography variant="caption" color="text.secondary">Tests</Typography>
                                                                <Typography variant="subtitle2">{experiment.total_tests}</Typography>
                                                            </Box>
                                                            <Box>
                                                                <Typography variant="caption" color="text.secondary">Success Rate</Typography>
                                                                <Typography variant="subtitle2" color="success.main">
                                                                    {experiment.success_rate.toFixed(1)}%
                                                                </Typography>
                                                            </Box>
                                                        </Box>
                                                        <Typography variant="caption" color="text.secondary">
                                                            Duration: {formatDuration(experiment.duration)}
                                                        </Typography>
                                                    </CardContent>
                                                </Card>
                                            </Grid>
                                        ))}
                                    </Grid>
                                </CardContent>
                            </Card>
                        )}

                        {/* Selected Experiment Details */}
                        {selectedExperiment && (
                            <Box sx={{ width: '100%', mt: theme.spacing(2), maxWidth: '1200px', mx: 'auto' }}>
                                {/* Experiment Summary */}
                                <Card sx={{ mb: 3 }}>
                                    <CardHeader 
                                        title={`📊 ${selectedExperiment.experiment_info.name}`}
                                        subheader={`Experiment ID: ${selectedExperiment.id}`}
                                    />
                                    <CardContent>
                                        <Grid container spacing={3}>
                                            <Grid item xs={12} md={6}>
                                                <Typography variant="h6" gutterBottom>📈 Performance Summary</Typography>
                                                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Total Tests</Typography>
                                                        <Typography variant="h6">{selectedExperiment.experiment_info.total_tests}</Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Success Rate</Typography>
                                                        <Typography variant="h6" color="success.main">
                                                            {selectedExperiment.experiment_info.success_rate.toFixed(1)}%
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Successful</Typography>
                                                        <Typography variant="h6" color="success.main">
                                                            {selectedExperiment.experiment_info.successful_tests}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Failed</Typography>
                                                        <Typography variant="h6" color="error.main">
                                                            {selectedExperiment.experiment_info.failed_tests}
                                                        </Typography>
                                                    </Box>
                                                    <Box>
                                                        <Typography variant="caption" color="text.secondary">Duration</Typography>
                                                        <Typography variant="h6">
                                                            {formatDuration(selectedExperiment.experiment_info.duration)}
                                                        </Typography>
                                                    </Box>
                                                </Box>
                                            </Grid>
                                            <Grid item xs={12} md={6}>
                                                <Typography variant="h6" gutterBottom>📁 Generated Files</Typography>
                                                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                                    {/* Gnuplot Files */}
                                                    {selectedExperiment.gnuplot_files && selectedExperiment.gnuplot_files.length > 0 && (
                                                        <Box>
                                                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                                📊 Gnuplot Data Files ({selectedExperiment.gnuplot_files.length})
                                                            </Typography>
                                                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                                                {selectedExperiment.gnuplot_files.map((file, index) => (
                                                                    <Chip
                                                                        key={index}
                                                                        label={file.filename}
                                                                        size="small"
                                                                        onClick={(e) => {
                                                                            if (e.ctrlKey || e.metaKey) {
                                                                                handleGnuplotFileClick(selectedExperiment.id, file.filename, 'preview');
                                                                            } else {
                                                                                handleGnuplotFileClick(selectedExperiment.id, file.filename, 'download');
                                                                            }
                                                                        }}
                                                                        sx={{ 
                                                                            cursor: 'pointer',
                                                                            '&:hover': {
                                                                                backgroundColor: 'primary.light',
                                                                                color: 'primary.contrastText'
                                                                            }
                                                                        }}
                                                                        title="Left-click to download, Ctrl+click to copy content"
                                                                    />
                                                                ))}
                                                            </Box>
                                                            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                                                                💡 Left-click to download, Ctrl+click to copy content
                                                            </Typography>
                                                        </Box>
                                                    )}

                                                    {/* Generated Images */}
                                                    {selectedExperiment.generated_images && selectedExperiment.generated_images.length > 0 && (
                                                        <Box sx={{ mt: 2 }}>
                                                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                                🖼️ Generated Images ({selectedExperiment.generated_images.length})
                                                            </Typography>
                                                            <Grid container spacing={2}>
                                                                {selectedExperiment.generated_images.map((image, index) => (
                                                                    <Grid item xs={12} sm={6} md={4} key={index}>
                                                                        <Card sx={{ 
                                                                            cursor: 'pointer',
                                                                            transition: 'all 0.2s',
                                                                            '&:hover': {
                                                                                transform: 'translateY(-2px)',
                                                                                boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
                                                                            }
                                                                        }}>
                                                                            <CardContent sx={{ p: 2 }}>
                                                                                {/* Image Preview for PNG files */}
                                                                                {image.format === 'PNG' && (
                                                                                    <Box sx={{ mb: 1, textAlign: 'center' }}>
                                                                                        <img 
                                                                                            src={`http://localhost:5000/experiments/results/${selectedExperiment.id}/images/${image.filename}`}
                                                                                            alt={image.chart_type}
                                                                                            style={{ 
                                                                                                maxWidth: '100%', 
                                                                                                maxHeight: '120px',
                                                                                                objectFit: 'contain',
                                                                                                border: '1px solid #ddd',
                                                                                                borderRadius: '4px'
                                                                                            }}
                                                                                            onError={(e) => {
                                                                                                e.target.style.display = 'none';
                                                                                            }}
                                                                                        />
                                                                                    </Box>
                                                                                )}
                                                                                <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                                                                                    {image.chart_type}
                                                                                </Typography>
                                                                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                                                                                    Format: {image.format} • {image.size_kb.toFixed(1)} KB
                                                                                </Typography>
                                                                                <Button
                                                                                    variant="outlined"
                                                                                    size="small"
                                                                                    fullWidth
                                                                                    onClick={() => {
                                                                                        const url = `http://localhost:5000/experiments/results/${selectedExperiment.id}/images/${image.filename}`;
                                                                                        window.open(url, '_blank');
                                                                                        setSuccess(`Opened ${image.filename} in new tab`);
                                                                                    }}
                                                                                >
                                                                                    🔗 Open
                                                                                </Button>
                                                                            </CardContent>
                                                                        </Card>
                                                                    </Grid>
                                                                ))}
                                                            </Grid>
                                                        </Box>
                                                    )}
                                                </Box>
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
                                            borderColor: 'primary.light',
                                            borderRadius: 3,
                                            overflow: 'hidden',
                                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
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
                                                    backgroundColor: 'primary.main',
                                                    color: 'white',
                                                    py: 2,
                                                    cursor: 'pointer',
                                                    '&:hover': {
                                                        backgroundColor: 'primary.dark'
                                                    }
                                                }}
                                            />
                                            <Collapse in={!collapsed} timeout="auto" unmountOnExit>
                                                <CardContent sx={{ p: 3 }}>
                                                    {/* Handle Mode 0 results (processed_clusters) */}
                                                    {result.processed_clusters && result.processed_clusters.map((processedCluster, clusterIndex) => (
                                                        processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                                        <div key={`similarity-${clusterIndex}`}>
                                                            <Typography variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
                                                                🔍 Site Similarity Analysis - Level {processedCluster.level}
                                                            </Typography>
                                                            {renderSiteSimilarityResults(processedCluster.processed_data.site_similarity, processedCluster.level)}
                                                        </div>
                                                    ))}

                                                    {/* Handle Mode 1 results (domain_results) */}
                                                    {result.domain_results && result.domain_results.map((domainResult, domainIndex) => (
                                                        domainResult.processed_clusters && domainResult.processed_clusters.map((processedCluster, clusterIndex) => (
                                                            processedCluster.processed_data && processedCluster.processed_data.site_similarity &&
                                                            <div key={`domain-${domainIndex}-similarity-${clusterIndex}`}>
                                                                <Typography variant="h6" sx={{ mt: 2, mb: 1, fontWeight: 'bold' }}>
                                                                    🔍 Site Similarity Analysis - {domainResult.domain} - Level {processedCluster.level}
                                                                </Typography>
                                                                {renderSiteSimilarityResults(processedCluster.processed_data.site_similarity, processedCluster.level)}
                                                            </div>
                                                        ))
                                                    ))}

                                                    {/* Clustering Results Summary for Mode 0 */}
                                                    {result.clustering_results && result.clustering_results.map((clusterResult, clusterIndex) => (
                                                        <Accordion 
                                                            key={`cluster-${clusterIndex}`} 
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
                                                                    backgroundColor: clusterResult.status === 'error' ? 'error.light' : 'grey.100',
                                                                    '&:hover': {
                                                                        backgroundColor: clusterResult.status === 'error' ? 'error.main' : 'grey.200',
                                                                    }
                                                                }}
                                                            >
                                                                <Typography sx={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                                                                    🧮 Level {clusterResult.level} - {clusterResult.status === 'error' ? '❌' : '✅'} {clusterResult.message}
                                                                </Typography>
                                                            </AccordionSummary>
                                                            <AccordionDetails sx={{ p: 2 }}>
                                                                {clusterResult.status === 'error' ? (
                                                                    <Typography variant="body2" color="error">
                                                                        {clusterResult.message}
                                                                    </Typography>
                                                                ) : (
                                                                    clusterResult.cluster_info && (
                                                                        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1 }}>
                                                                            <Box>
                                                                                <Typography variant="caption" color="text.secondary">Clusters</Typography>
                                                                                <Typography variant="subtitle2">{clusterResult.cluster_info.num_clusters}</Typography>
                                                                            </Box>
                                                                            <Box>
                                                                                <Typography variant="caption" color="text.secondary">DBCV Score</Typography>
                                                                                <Typography variant="subtitle2">{clusterResult.cluster_info.dbcv_score?.toFixed(3)}</Typography>
                                                                            </Box>
                                                                            <Box>
                                                                                <Typography variant="caption" color="text.secondary">Attributes</Typography>
                                                                                <Typography variant="subtitle2">{clusterResult.cluster_info.useful_attributes?.length || 0}</Typography>
                                                                            </Box>
                                                                        </Box>
                                                                    )
                                                                )}
                                                            </AccordionDetails>
                                                        </Accordion>
                                                    ))}

                                                    {/* Clustering Results Summary for Mode 1 */}
                                                    {result.domain_results && result.domain_results.map((domainResult, domainIndex) => (
                                                        domainResult.clustering_results && domainResult.clustering_results.map((clusterResult, clusterIndex) => (
                                                            <Accordion 
                                                                key={`domain-${domainIndex}-cluster-${clusterIndex}`} 
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
                                                                        backgroundColor: clusterResult.status === 'error' ? 'error.light' : 'grey.100',
                                                                        '&:hover': {
                                                                            backgroundColor: clusterResult.status === 'error' ? 'error.main' : 'grey.200',
                                                                        }
                                                                    }}
                                                                >
                                                                    <Typography sx={{ fontWeight: 'bold', fontSize: '0.9rem' }}>
                                                                        🧮 {domainResult.domain} - Level {clusterResult.level} - {clusterResult.status === 'error' ? '❌' : '✅'} {clusterResult.message}
                                                                    </Typography>
                                                                </AccordionSummary>
                                                                <AccordionDetails sx={{ p: 2 }}>
                                                                    {clusterResult.status === 'error' ? (
                                                                        <Typography variant="body2" color="error">
                                                                            {clusterResult.message}
                                                                        </Typography>
                                                                    ) : (
                                                                        clusterResult.cluster_info && (
                                                                            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 1 }}>
                                                                                <Box>
                                                                                    <Typography variant="caption" color="text.secondary">Clusters</Typography>
                                                                                    <Typography variant="subtitle2">{clusterResult.cluster_info.num_clusters}</Typography>
                                                                                </Box>
                                                                                <Box>
                                                                                    <Typography variant="caption" color="text.secondary">DBCV Score</Typography>
                                                                                    <Typography variant="subtitle2">{clusterResult.cluster_info.dbcv_score?.toFixed(3)}</Typography>
                                                                                </Box>
                                                                                <Box>
                                                                                    <Typography variant="caption" color="text.secondary">Attributes</Typography>
                                                                                    <Typography variant="subtitle2">{clusterResult.cluster_info.useful_attributes?.length || 0}</Typography>
                                                                                </Box>
                                                                            </Box>
                                                                        )
                                                                    )}
                                                                </AccordionDetails>
                                                            </Accordion>
                                                        ))
                                                    ))}
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
                            <Card sx={{ textAlign: 'center', py: 4 }}>
                                <CardContent>
                                    <Typography variant="h6" color="text.secondary" gutterBottom>
                                        📭 No experiments found
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Run some experiments first to see results here.
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}
                    </Box>
                );
            case 'config':
                return (
                    <Box sx={{ width: '100%', maxWidth: '1200px', margin: '0 auto', p: 3 }}>
                        <Typography variant="h4" gutterBottom sx={{ textAlign: 'center', mb: 4 }}>
                            ⚙️ Custom Experiment Configuration Builder
                        </Typography>

                        {/* Configuration Form */}
                        <Card sx={{ mb: 3 }}>
                            <CardHeader title="🛠️ Build Your Custom Experiment" />
                            <CardContent sx={{ p: 3 }}>
                                <Grid container spacing={3}>
                                    {/* Experiment Name */}
                                    <Grid item xs={12}>
                                        <TextField
                                            fullWidth
                                            label="Experiment Name"
                                            value={customConfig.experiment_name}
                                            onChange={(e) => setCustomConfig(prev => ({ ...prev, experiment_name: e.target.value }))}
                                            placeholder="e.g., My Custom Thesis Experiment"
                                        />
                                    </Grid>

                                    {/* URLs Section */}
                                    <Grid item xs={12}>
                                        <Typography variant="h6" gutterBottom>🌐 URLs to Test</Typography>
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
                                            />
                                            <Button variant="contained" onClick={addConfigUrl}>
                                                Add
                                            </Button>
                                        </Box>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                            {customConfig.available_urls.map((url, index) => (
                                                <Chip
                                                    key={index}
                                                    label={url}
                                                    onDelete={() => removeConfigUrl(index)}
                                                    color="primary"
                                                />
                                            ))}
                                        </Box>
                                        <Typography variant="caption" color="text.secondary">
                                            Added {customConfig.available_urls.length} URLs
                                        </Typography>
                                    </Grid>

                                    {/* Processing Modes */}
                                    <Grid item xs={12} md={6}>
                                        <Typography variant="h6" gutterBottom>🔄 Processing Modes</Typography>
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                            <FormControlLabel
                                                control={
                                                    <Switch
                                                        checked={customConfig.modes.includes(0)}
                                                        onChange={(e) => {
                                                            const newModes = e.target.checked 
                                                                ? [...customConfig.modes, 0].filter((v, i, arr) => arr.indexOf(v) === i)
                                                                : customConfig.modes.filter(m => m !== 0);
                                                            setCustomConfig(prev => ({ ...prev, modes: newModes }));
                                                        }}
                                                    />
                                                }
                                                label="Mode 0: Process All URLs Together"
                                            />
                                            <FormControlLabel
                                                control={
                                                    <Switch
                                                        checked={customConfig.modes.includes(1)}
                                                        onChange={(e) => {
                                                            const newModes = e.target.checked 
                                                                ? [...customConfig.modes, 1].filter((v, i, arr) => arr.indexOf(v) === i)
                                                                : customConfig.modes.filter(m => m !== 1);
                                                            setCustomConfig(prev => ({ ...prev, modes: newModes }));
                                                        }}
                                                    />
                                                }
                                                label="Mode 1: Process by Domain"
                                            />
                                        </Box>
                                    </Grid>

                                    {/* DOM Levels */}
                                    <Grid item xs={12} md={6}>
                                        <Typography variant="h6" gutterBottom>📊 DOM Levels</Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
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
                                                />
                                            ))}
                                        </Box>
                                        <Typography variant="caption" color="text.secondary">
                                            Selected levels: {customConfig.levels.join(', ')}
                                        </Typography>
                                    </Grid>

                                    {/* URL Combinations */}
                                    <Grid item xs={12} md={6}>
                                        <Typography variant="h6" gutterBottom>🔢 URLs per Test</Typography>
                                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                            {Array.from({ length: Math.min(10, customConfig.available_urls.length) }, (_, i) => i + 2).map(count => (
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
                                                    disabled={count > customConfig.available_urls.length}
                                                />
                                            ))}
                                        </Box>
                                        <Typography variant="caption" color="text.secondary">
                                            Test combinations: {customConfig.url_combinations.join(', ')} URLs per test
                                        </Typography>
                                    </Grid>

                                    {/* Max Combinations */}
                                    <Grid item xs={12} md={6}>
                                        <Typography variant="h6" gutterBottom>⚡ Test Limits</Typography>
                                        <TextField
                                            type="number"
                                            label="Max Test Combinations"
                                            value={customConfig.max_combinations}
                                            onChange={(e) => setCustomConfig(prev => ({ 
                                                ...prev, 
                                                max_combinations: Math.max(1, Math.min(100, parseInt(e.target.value) || 25))
                                            }))}
                                            inputProps={{ min: 1, max: 100 }}
                                            fullWidth
                                        />
                                        <Typography variant="caption" color="text.secondary">
                                            Will generate up to {customConfig.max_combinations} test combinations
                                        </Typography>
                                    </Grid>
                                </Grid>

                                {/* Estimated Tests Preview */}
                                <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                                    <Typography variant="h6" gutterBottom>📋 Experiment Preview</Typography>
                                    <Grid container spacing={2}>
                                        <Grid item xs={6} sm={3}>
                                            <Typography variant="subtitle2">URLs:</Typography>
                                            <Typography variant="h6" color="primary">{customConfig.available_urls.length}</Typography>
                                        </Grid>
                                        <Grid item xs={6} sm={3}>
                                            <Typography variant="subtitle2">Modes:</Typography>
                                            <Typography variant="h6" color="primary">{customConfig.modes.length}</Typography>
                                        </Grid>
                                        <Grid item xs={6} sm={3}>
                                            <Typography variant="subtitle2">Levels:</Typography>
                                            <Typography variant="h6" color="primary">{customConfig.levels.length}</Typography>
                                        </Grid>
                                        <Grid item xs={6} sm={3}>
                                            <Typography variant="subtitle2">Est. Tests:</Typography>
                                            <Typography variant="h6" color="primary">
                                                {Math.min(
                                                    customConfig.max_combinations, 
                                                    customConfig.modes.length * customConfig.url_combinations.length
                                                )}
                                            </Typography>
                                        </Grid>
                                    </Grid>
                                </Box>

                                {/* Run Button */}
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
                                    <Button
                                        variant="contained"
                                        color="primary"
                                        size="large"
                                        onClick={runCustomExperiment}
                                        disabled={
                                            experimentLoading || 
                                            customConfig.available_urls.length === 0 || 
                                            customConfig.levels.length === 0 ||
                                            customConfig.modes.length === 0 ||
                                            customConfig.url_combinations.length === 0
                                        }
                                        sx={{ 
                                            borderRadius: '20px',
                                            px: 4,
                                            py: 1.5,
                                            fontSize: '1.1rem'
                                        }}
                                    >
                                        {experimentLoading ? (
                                            <>
                                                <CircularProgress size={20} sx={{ mr: 2 }} />
                                                Running Custom Experiment...
                                            </>
                                        ) : (
                                            <>
                                                🚀 Run Custom Experiment
                                            </>
                                        )}
                                    </Button>
                                </Box>
                            </CardContent>
                        </Card>
                    </Box>
                );
            case 'view3':
                return <div>View 3 Content</div>;
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
                    <Button variant="contained" onClick={() => setCurrentView('home')}>🏠 Home</Button>
                    <Button variant="contained" onClick={() => setCurrentView('clusters')}>🎯 Clusters</Button>
                    <Button variant="contained" onClick={() => setCurrentView('experiments')}>🧪 Experiments</Button>
                    <Button variant="contained" onClick={() => setCurrentView('results')}>📊 Results Archive</Button>
                    <Button variant="contained" onClick={() => setCurrentView('config')}>⚙️ Config Builder</Button>
                    <Button variant="contained" onClick={() => setCurrentView('view3')}>👁️ View 3</Button>
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

            {/* Scroll to Top Button */}
            {showScrollTop && (
                <Fab
                    color="primary"
                    size="small"
                    onClick={handleScrollToTop}
                    sx={{
                        position: 'fixed',
                        bottom: 16,
                        right: 16,
                        zIndex: 1000,
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
        </Grid>
    );
};

export default URLChipForm;