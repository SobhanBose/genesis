import React, { useState, useEffect, useContext } from 'react';
import { LogContext } from '../../context/LogContext';
import RoundMetrics from './TrainingRounds';

import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faDatabase, faVial, faFileLines } from '@fortawesome/free-solid-svg-icons';


const DataTraining = () => {
  const { logs, errors, metrics, isTraining } = useContext(LogContext);

  const [logLists, setLogLists] = useState([]);
  const [namedLog, setNamedLog] = useState(null);
  const [logSelected, setLogSelected] = useState(null);
  const [showCurrentTraining, setShowCurrentTraining] = useState(false);
  const [metricsData, setMetricsData] = useState(null);

  const [activeRound, setActiveRound] = useState(1);



  // request all the logs list
  useEffect(() => {
    window.electron.ipcRenderer.send("get-all-logs-list");
  }, []);

  useEffect(() => {
    if (!isTraining) {
      setShowCurrentTraining(false);

      // refresh log list
      window.electron.ipcRenderer.send("get-all-logs-list");

      // fetch latest backed-up log
      window.electron.ipcRenderer.send("get-most-recent-log-file");

      // fetch latest backed-up metrics
      window.electron.ipcRenderer.send("get-most-recent-metrics-file");

      // reset selection
      setLogSelected(null);
    }
  }, [isTraining]); // refresh current training display when training status changes

  // request log file when selection changes
  useEffect(() => {
    if (logSelected) {
      window.electron.ipcRenderer.send("get-log-file-by-name", logSelected);
    } else {
      window.electron.ipcRenderer.send("get-most-recent-log-file");
    }
  }, [logSelected]);


  useEffect(() => {
    // get all the log lists
    window.electron.ipcRenderer.on("listed-all-logs", (_, msg) => {
      setLogLists(msg.logs);
    });

    // get the most recent log file
    window.electron.ipcRenderer.on("fetched-most-recent-log-file", (_, msg) => {
      setNamedLog(msg.log);
    });

    // get the most recent metrics file
    window.electron.ipcRenderer.on("fetched-most-recent-metrics-file", (_, msg) => {
      setMetricsData(msg.metrics);
    });

    // get log file by name
    window.electron.ipcRenderer.on("fetched-log-file-by-name", (_, msg) => {
      setNamedLog(msg.log);
    });

    // get metrics file by name
    window.electron.ipcRenderer.on("fetched-metrics-file-by-name", (_, msg) => {
      setMetricsData(msg.metrics);
    });

    return () => {
      window.electron.ipcRenderer.removeAllListeners("listed-all-logs");
      window.electron.ipcRenderer.removeAllListeners("fetched-most-recent-log-file");
      window.electron.ipcRenderer.removeAllListeners("fetched-most-recent-metrics-file");
      window.electron.ipcRenderer.removeAllListeners("fetched-log-file-by-name");
      window.electron.ipcRenderer.removeAllListeners("fetched-metrics-file-by-name");
    }
  }, []);


  // Utility: Clean up and format logs
  const formatLogText = (text) => {
    if (!text) return "";

    // Remove ANSI escape sequences (like \x1B[92m)
    const ansiRegex = /\x1B\[[0-9;]*m/g;
    let clean = text.replace(ansiRegex, "");

    // Replace \r and \n with <br /> for HTML
    clean = clean.replace(/\r\n|\n|\r/g, "<br />");

    // Optionally replace tabs with spaces
    clean = clean.replace(/\t/g, "&nbsp;&nbsp;");

    return clean;
  };


  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-gray-50 p-6 w-full">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-10 mt-5">
          <h1 className="text-6xl font-bold text-[#0098B0] mb-2">Data Training</h1>
          <div className="w-24 h-1 bg-[#0098B0]/30 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Upload and train your datasets easily</p>
        </div>

        {/* 🟢 Status Bar */}
        <div className="flex justify-end items-center mt-6">
          <div
            className={`w-3 h-3 rounded-full mr-2 ${isTraining ? "bg-green-500 animate-pulse" : "bg-gray-400"
              }`}
          ></div>
          <span
            className={`text-[16px] font-medium ${isTraining ? "text-green-600" : "text-gray-600"
              }`}
          >
            {isTraining ? "Training in progress..." : "Idle — no training currently running"}
          </span>
        </div>

        {/* Logs Section */}
        <div className="mb-6">
          {/* Dropdown for selecting log files */}
          {logLists.length > 0 && (
            <div className="mb-4 flex items-center justify-between">
              {/* Selector */}
              <div className="flex-1 mr-4">
                <label className="block text-gray-700 font-medium mb-2">
                  Select a Log File
                </label>
                <select
                  value={logSelected || ""}
                  onChange={(e) => {
                    setLogSelected(e.target.value);
                    setShowCurrentTraining(false);
                  }}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#0098B0] focus:outline-none"
                >
                  <option value="">Most Recent</option>
                  {logLists.map((file, idx) => (
                    <option key={idx} value={file}>
                      {file}
                    </option>
                  ))}
                </select>
              </div>

              {/* Show Current Training Button */}
              <div className="mt-7">
                <button
                  onClick={() => {
                    setShowCurrentTraining(true);
                    // setLogSelected(null); // reset selection to most recent
                    // setMetricsData(null); // reset metrics data to fetch current training metrics
                    // setNamedLog(null); // reset named log to fetch current training log
                  }}
                  disabled={!isTraining}
                  className={`px-4 py-2 rounded-lg font-medium transition-all ${isTraining
                    ? "bg-[#0098B0] text-white hover:bg-[#007a91]"
                    : "bg-gray-300 text-gray-600 cursor-not-allowed"
                    }`}
                >
                  Show Current Training
                </button>
              </div>
            </div>
          )}

          {/* Conditional Console Rendering */}
          {showCurrentTraining ? (
            // ✅ Live Training Console
            <div className="bg-gray-800 text-white p-4 rounded-xl h-64 overflow-y-auto font-mono text-sm">
              <p className="text-gray-400 mb-2">
                Showing <span className="text-[#00d4ff] font-medium">Current Training Logs</span>
              </p>
              {logs.length === 0 && errors.length === 0 && (
                <p className="text-gray-400">No live logs yet...</p>
              )}

              {logs.map((log, index) => (
                <div
                  key={`live-log-${index}`}
                  className="text-green-400 mb-2"
                  dangerouslySetInnerHTML={{ __html: formatLogText(log) }}
                />
              ))}

              {errors.map((err, index) => (
                <div
                  key={`live-err-${index}`}
                  className="text-red-500 mb-2"
                  dangerouslySetInnerHTML={{ __html: formatLogText(err) }}
                />
              ))}
            </div>
          ) : (
            // ✅ Named or Most Recent Log Console
            namedLog && (
              <div className="bg-gray-800 text-white p-4 rounded-xl h-64 overflow-y-auto font-mono text-sm">
                <p className="text-gray-400 mb-2">
                  Showing log:{" "}
                  <span className="text-[#00d4ff] font-medium">
                    {logSelected || "Most Recent"}
                  </span>
                </p>
                <div
                  className="text-green-400"
                  dangerouslySetInnerHTML={{ __html: formatLogText(namedLog) }}
                ></div>

              </div>
            )
          )}
        </div>

        {/* Metrics Cards: Training Samples, Testing Samples, Input Size */}
        {!showCurrentTraining && metricsData?.isAborted ? (
          <h2 className='text-2xl text-red-600'>
            Training was aborted by Admin. No metrics available. Please start a new training session to see metrics.
          </h2>
        ) : (
          <>
            <h2 className="text-2xl font-semibold text-gray-800 mb-4">
              {showCurrentTraining ? "Current Training Data" : "Previous Training Data"}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Training Samples */}
              <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 text-center">
                <div className="bg-[#0098B0]/10 p-3 rounded-full inline-flex items-center justify-center mb-4">
                  <FontAwesomeIcon icon={faDatabase} className="text-2xl text-[#0098B0]" />
                </div>
                <h3 className="text-2xl font-bold text-[#0098B0] mb-2">
                  {showCurrentTraining && isTraining ? metrics?.trainingSamples || "-" : metricsData?.trainingSamples || "-"}
                </h3>
                <p className="text-gray-600">Training Samples</p>
              </div>

              {/* Testing Samples */}
              <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 text-center">
                <div className="bg-[#0098B0]/10 p-3 rounded-full inline-flex items-center justify-center mb-4">
                  <FontAwesomeIcon icon={faVial} className="text-2xl text-[#0098B0]" />
                </div>
                <h3 className="text-2xl font-bold text-[#0098B0] mb-2">
                  {showCurrentTraining && isTraining ? metrics?.testingSamples || "-" : metricsData?.testingSamples || "-"}
                </h3>
                <p className="text-gray-600">Testing Samples</p>
              </div>

              {/* Input Size */}
              <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 text-center">
                <div className="bg-[#0098B0]/10 p-3 rounded-full inline-flex items-center justify-center mb-4">
                  <FontAwesomeIcon icon={faFileLines} className="text-2xl text-[#0098B0]" />
                </div>
                <h3 className="text-2xl font-bold text-[#0098B0] mb-2">
                  {showCurrentTraining && isTraining ? metrics?.inputSize || "-" : metricsData?.inputSize || "-"}
                </h3>
                <p className="text-gray-600">Input Size</p>
              </div>
            </div>

            {/* 🧠 Rounds Timeline */}
            <div className="space-y-6 mt-10">
              <h2 className="text-2xl font-semibold text-gray-800 mb-4">
                {showCurrentTraining ? "Current Training Rounds" : "Previous Training Rounds"}
              </h2>

              {/* ✅ When showing current training */}
              {showCurrentTraining ? (
                metrics?.rounds?.length > 0 ? (
                  metrics.rounds.map((round) => (
                    <RoundMetrics
                      key={round.round || round.id}
                      round={round}
                      activeRound={activeRound}
                      onSelect={setActiveRound}
                      currentRoundProgress={
                        round.status === "in-progress" ? metrics.currentRoundProgress : null
                      }
                    />
                  ))
                ) : (
                  <p className="text-gray-500 text-center mt-8">
                    No active training rounds yet.
                  </p>
                )
              ) : (
                // ✅ When showing old training
                metricsData?.rounds?.length > 0 ? (
                  metricsData.rounds.map((round) => (
                    <RoundMetrics
                      key={round.round || round.id}
                      round={round}
                      activeRound={activeRound}
                      onSelect={setActiveRound}
                    />
                  ))
                ) : (
                  <p className="text-gray-500 text-center mt-8">
                    No recorded metrics found for this training.
                  </p>
                )
              )}
            </div>
          </>
        )}

      </div>
    </div>
  );
};

export default DataTraining;