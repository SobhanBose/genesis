import React, { useState, useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { 
  faCloudUploadAlt, 
  faCheckCircle, 
  faBrain,
  faFile,
  faChartLine,
  faSpinner
} from '@fortawesome/free-solid-svg-icons';

const Inference = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [fileInfo, setFileInfo] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [isInferencing, setIsInferencing] = useState(false);
  const [validationComplete, setValidationComplete] = useState(false);
  const [inferenceResults, setInferenceResults] = useState(null);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
      const randomEntries = Math.floor(Math.random() * 5000) + 500;
      
      setFileInfo({
        name: file.name,
        size: sizeInMB,
        entries: randomEntries
      });
    }
  }, []);

  const handleValidateData = () => {
    setIsValidating(true);
    // Simulate validation process
    setTimeout(() => {
      setIsValidating(false);
      setValidationComplete(true);
    }, 2000);
  };

  const handleMakeInference = () => {
    setIsInferencing(true);
    // Simulate inference process
    setTimeout(() => {
      setIsInferencing(false);
      // Generate sample inference results
      setInferenceResults({
        accuracy: (Math.random() * 30 + 70).toFixed(1),
        predictions: Math.floor(Math.random() * 500 + 500),
        confidence: (Math.random() * 20 + 75).toFixed(1),
        processingTime: (Math.random() * 2 + 1.5).toFixed(2)
      });
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-gray-50 p-6 w-full">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-10 mt-5">
          <h1 className="text-6xl font-bold text-[#0098B0] mb-2">Inference Window</h1>
          <div className="w-24 h-1 bg-[#0098B0]/30 mx-auto"></div>
          <p className="text-gray-600 mt-4">Upload test data and generate predictions</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Upload Section */}
          <div 
            className={`p-8 rounded-2xl border-2 border-dashed transition-all duration-300 ${
              isDragging 
                ? 'border-[#0098B0] bg-[#0098B0]/5' 
                : 'border-gray-300 hover:border-[#0098B0]/50'
            } flex flex-col items-center justify-center`}
            onDragEnter={handleDragEnter}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <div className="bg-[#0098B0] p-4 rounded-full mb-4">
              <FontAwesomeIcon 
                icon={faCloudUploadAlt} 
                className="text-2xl text-white" 
              />
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">Upload test data file</h3>
            <p className="text-gray-600 text-center mb-6">
              Drag and drop your test dataset file here
            </p>
            
            {fileInfo ? (
              <div className="w-full bg-[#0098B0]/5 p-4 rounded-xl border border-[#0098B0]/20">
                <div className="flex items-center mb-3">
                  <FontAwesomeIcon icon={faFile} className="mr-3 text-[#0098B0]" />
                  <span className="font-medium text-gray-800">{fileInfo.name}</span>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Dataset Size</p>
                    <p className="font-medium text-gray-800">{fileInfo.size} MB</p>
                  </div>
                  <div>
                    <p className="text-gray-600">No of entries</p>
                    <p className="font-medium text-gray-800">{fileInfo.entries.toLocaleString()}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-sm mt-2">
                Supported formats: CSV, JSON, XML
              </p>
            )}
          </div>

          {/* Actions Section */}
          <div className="flex flex-col space-y-6">
            {/* Check Data Validity */}
            <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
              <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                <FontAwesomeIcon icon={faCheckCircle} className="mr-3 text-[#0098B0]" />
                Check Data Validity
              </h3>
              <p className="text-gray-600 mb-4">
                Validate your test data for inference compatibility
              </p>
              <button
                onClick={handleValidateData}
                disabled={!fileInfo || isValidating}
                className={`w-full py-3 rounded-xl font-medium transition-all ${
                  !fileInfo || isValidating
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-[#0098B0] text-white hover:bg-[#007a96] hover:scale-[1.02] shadow-md'
                }`}
              >
                {isValidating ? (
                  <>
                    <FontAwesomeIcon icon={faSpinner} className="animate-spin mr-2" />
                    Validating...
                  </>
                ) : (
                  'Validate Data'
                )}
              </button>
              
              {validationComplete && (
                <div className="mt-4 p-3 bg-green-50 rounded-lg flex items-center border border-green-200">
                  <FontAwesomeIcon 
                    icon={faCheckCircle} 
                    className="text-green-600 mr-2" 
                  />
                  <span className="text-green-800">Data validation successful!</span>
                </div>
              )}
            </div>

            {/* Make Inference */}
            <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
              <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                <FontAwesomeIcon icon={faBrain} className="mr-3 text-[#0098B0]" />
                Make Inference
              </h3>
              <p className="text-gray-600 mb-4">
                Generate predictions using your trained model
              </p>
              <button
                onClick={handleMakeInference}
                disabled={!validationComplete || isInferencing}
                className={`w-full py-3 rounded-xl font-medium transition-all ${
                  !validationComplete || isInferencing
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-[#00b4d8] text-white hover:bg-[#0098B0] hover:scale-[1.02] shadow-md'
                }`}
              >
                {isInferencing ? (
                  <>
                    <FontAwesomeIcon icon={faSpinner} className="animate-spin mr-2" />
                    Processing...
                  </>
                ) : (
                  'Make Inference'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Inference Results Section */}
        <div className="bg-white rounded-2xl shadow-md p-8 border border-gray-100">
          <div className="flex items-center mb-6">
            <FontAwesomeIcon icon={faChartLine} className="text-2xl text-[#0098B0] mr-3" />
            <h2 className="text-2xl font-bold text-gray-800">Inference Results</h2>
          </div>
          
          {inferenceResults ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-[#0098B0]/5 p-6 rounded-xl border border-[#0098B0]/20">
                <p className="text-gray-600 mb-2">Accuracy</p>
                <p className="text-3xl font-bold text-[#0098B0]">{inferenceResults.accuracy}%</p>
              </div>
              <div className="bg-[#0098B0]/5 p-6 rounded-xl border border-[#0098B0]/20">
                <p className="text-gray-600 mb-2">Predictions</p>
                <p className="text-3xl font-bold text-[#0098B0]">{inferenceResults.predictions.toLocaleString()}</p>
              </div>
              <div className="bg-[#0098B0]/5 p-6 rounded-xl border border-[#0098B0]/20">
                <p className="text-gray-600 mb-2">Confidence</p>
                <p className="text-3xl font-bold text-[#0098B0]">{inferenceResults.confidence}%</p>
              </div>
              <div className="bg-[#0098B0]/5 p-6 rounded-xl border border-[#0098B0]/20">
                <p className="text-gray-600 mb-2">Processing Time</p>
                <p className="text-3xl font-bold text-[#0098B0]">{inferenceResults.processingTime}s</p>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="bg-gray-100 p-6 rounded-xl inline-block">
                <FontAwesomeIcon icon={faChartLine} className="text-4xl text-gray-400 mb-4" />
                <p className="text-gray-600">Inference results will appear here after processing</p>
              </div>
            </div>
          )}
        </div>

        {/* Progress indicators */}
        {(isValidating || isInferencing) && (
          <div className="fixed bottom-6 right-6 bg-[#0098B0] text-white px-4 py-3 rounded-xl shadow-lg flex items-center">
            <FontAwesomeIcon icon={faSpinner} className="animate-spin mr-2" />
            <span>
              {isValidating ? 'Validating data...' : 'Running inference...'}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default Inference;