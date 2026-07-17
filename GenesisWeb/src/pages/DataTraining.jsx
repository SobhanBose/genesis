// DataTraining.jsx
import React, { useState, useEffect, useRef } from 'react';
import { LogContext } from '../context/LogContext';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faSyncAlt, faPlayCircle, faPauseCircle, faChartLine, faUsers, faServer, faClock, faCheckCircle, faStopCircle, faCog, faDatabase, faNetworkWired, faExclamationTriangle, faInfoCircle, } from '@fortawesome/free-solid-svg-icons';

import formatTime from '../utilities/FormatTime';

const DataTraining = () => {

  // Dynamic states for rounds
  const [activeRound, setActiveRound] = useState(4);
  const [totalRounds, setTotalRounds] = useState(0);
  const [trainingStatus, setTrainingStatus] = useState('idle'); // idle, server_started, running, completed
  const [isClicked, setIsClicked] = useState(false);
  const [port, setPort] = useState(null);

  const [traininglogs, setTrainingLogs] = useState([]);
  const [shouldCheckLogs, setShouldCheckLogs] = useState(false);
  const pollingRef = useRef(false);
  const offsetRef = useRef(0);

  const [metrics, setMetrics] = useState([]);
  const roundTimersRef = useRef({});
  const completedRoundsRef = useRef(0);

  const [trainingStartTime, setTrainingStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState('00:00:00');
  const trainingTimerRef = useRef(null);

  
  const [connectedClients, setConnectedClients] = useState([]);


  // all variables for old training runs
  const [showCurrentTraining, setShowCurrentTraining] = useState(false);
  const [runList, setRunList] = useState([]);
  const [selectedRun, setSelectedRun] = useState('');
  const [runMetadata, setRunMetadata] = useState(null);
  const [oldLogs, setOldLogs] = useState([]);
  const [oldMetrics, setOldMetrics] = useState([]);
  // old metrics format
  // [
  //   {
  //     round : 1,
  //     loss : 0.5,
  //     accuracy : 0.8,
  //     startTime : '2024-06-01T12:00:00Z',
  //     endTime : '2024-06-01T12:05:00Z'
  //   }
  // ]

  const startServer = async () => {

    // reset states
    setMetrics([]);
    setTrainingLogs([]);
    setElapsedTime('00:00:00');
    setTrainingStartTime(null);

    completedRoundsRef.current = 0;
    roundTimersRef.current = {};
    pollingRef.current = false;
    offsetRef.current = 0;
    trainingTimerRef.current = null;

    setIsClicked(true);

    const res = await fetch('http://localhost:3000/web/startServer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const serverData = await res.json();
    setPort(serverData.port);

    if (res.ok) {
      setTrainingStatus('server_started');

      const res = await fetch('http://127.0.0.1:8000/api/v1/training/status');
      const data = await res.json();
      setTotalRounds(data.total_rounds);
      setShouldCheckLogs(true);
    }
    else {
      setTrainingStatusError('Failed to start server');
      console.error('Failed to start server:', res.statusText);
      setShouldCheckLogs(false);
    }
    setIsClicked(false);
  }

  const sendStartTrainingCommand = async (run_id, total_rounds) => {
    setIsClicked(true);
    const res = await fetch('http://localhost:3000/startTraining', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        run_id,
        total_rounds,
        port: port
      })
    });

    if (res.ok) {
      setTrainingStatus('running');
    }
    else {
      setTrainingStatusError('Failed to start training');
      console.error('Failed to start training:', res.statusText);
      setShouldCheckLogs(false);
    }
    setIsClicked(false);
  };

  const stopTraining = async () => {
    setIsClicked(true);

    const res = await fetch('http://localhost:3000/web/stopServer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (res.ok) {

      await fetch('http://localhost:3000/stopTraining', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      setTrainingStatus('idle');
      setMetrics([]);
      setTrainingLogs([]);
      setElapsedTime('00:00:00');
      setTrainingStartTime(null);
      setShouldCheckLogs(false);

      completedRoundsRef.current = 0;
      roundTimersRef.current = {};
      pollingRef.current = false;
      offsetRef.current = 0;
      if (trainingTimerRef.current) {
        clearInterval(trainingTimerRef.current);
        trainingTimerRef.current = null;
      }

    }

    setIsClicked(false);
  };

  // parsing live logs and updating metrics accordingly
  const parseLogLine = (log, totalRounds, stopPolling) => {
    const { message, timestamp } = log;
    const time = new Date(timestamp);

    console.log(message);

    // ROUND START
    const startMatch = message.match(/^Round (\d+): Sampled \d+ clients out of/);
    if (startMatch) {
      const round = Number(startMatch[1]);

      roundTimersRef.current[round] = time;

      setMetrics(prev => {
        if (prev.some(r => r.round === round)) return prev;
        return [...prev, { round, loss: null, accuracy: null, duration: null }];
      });

      return;
    }

    // ROUND END (FIXED)
    if (message.includes('Aggregated client evaluation metrics')) {
      const roundMatch = message.match(/Round (\d+)/);
      const lossMatch = message.match(/loss:\s*([\d.]+)/);
      const accMatch = message.match(/accuracy:\s*([\d.]+)/);

      if (!roundMatch || !lossMatch || !accMatch) return;

      const round = Number(roundMatch[1]);
      const loss = Number(lossMatch[1]);
      const accuracy = Number(accMatch[1]);

      const startTime = roundTimersRef.current[round];
      if (!startTime) return;

      const duration = Math.round((time - startTime) / 1000);

      delete roundTimersRef.current[round];
      completedRoundsRef.current += 1;

      setMetrics(prev =>
        prev.map(r =>
          r.round === round
            ? { ...r, loss, accuracy, duration }
            : r
        )
      );

      if (totalRounds > 0 && completedRoundsRef.current >= totalRounds) {
        stopPolling();
        setTrainingStatus('completed');
        setShouldCheckLogs(false);
      }
    }

  };

  // parsing old logs for selected run and updating metrics accordingly
  const parseOldLogLine = (log) => {
    const { message, timestamp } = log;
    const time = new Date(timestamp);

    // ROUND START
    const startMatch = message.match(/^Round (\d+): Sampled \d+ clients out of/);
    if (startMatch) {
      const round = Number(startMatch[1]);

      setOldMetrics(prev => [
        ...prev,
        {
          round: round,
          loss: null,
          accuracy: null,
          startTime: timestamp,
          endTime: null
        }
      ]);

      return;
    }

    // ROUND END (FIXED)
    if (message.includes('Aggregated client evaluation metrics')) {
      const roundMatch = message.match(/Round (\d+)/);
      const lossMatch = message.match(/loss:\s*([\d.]+)/);
      const accMatch = message.match(/accuracy:\s*([\d.]+)/);

      if (!roundMatch || !lossMatch || !accMatch) return;

      const round = Number(roundMatch[1]);
      const loss = Number(lossMatch[1]);
      const accuracy = Number(accMatch[1]);

      setOldMetrics(prev =>
        prev.map(r =>
          r.round === round
            ? { ...r, loss, accuracy, endTime: timestamp }
            : r
        )
      );
    }

  };

  // transfer live logs/metrics to old logs/metrics when training completes or it is stopped
  const transferLiveToStored = async () => {

    const res = await fetch('http://127.0.0.1:8000/api/v1/training/runs');
    const data = res.ok ? await res.json() : [];

    setRunList(data.runs || []);

    console.log('Fetched training runs:', data);

    const run = data.runs[0]?.run_id;

    if (run) {
      setSelectedRun(run);
    }
    setShowCurrentTraining(false);

  }

  // effect to transfer live logs/metrics to old logs/metrics when training completes or it is stopped
  useEffect(() => {
    const handleTrainingCompletion = async () => {
      if (trainingStatus === 'completed' || trainingStatus === 'idle') {
        transferLiveToStored();
      }
    }
    handleTrainingCompletion();
  }, [trainingStatus]);

  // for fetching run lists
  useEffect(() => {
    const fetchList = async () => {
      const res = await fetch('http://127.0.0.1:8000/api/v1/training/runs');
      const data = res.ok ? await res.json() : [];

      setRunList(data.runs || []);

      console.log('Fetched training runs:', data);
    }
    fetchList();
  }, []);

  // fetch metadata, metrics and logs when a run is selected
  useEffect(() => {
    if (!selectedRun) return;

    setShowCurrentTraining(false);
    setOldMetrics([]);
    setOldLogs([]);
    setRunMetadata(null);

    const fetchRunMetaData = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/training/runs/${selectedRun}`);
        const data = await res.json();
        console.log('Fetched run metadata:', data);
        setRunMetadata(data);
      }
      catch (err) {
        console.error('Failed to fetch run metadata:', err);
      }
    };

    const fetchRunMetrics = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/training/runs/${selectedRun}/metrics`);
        const data = await res.json();
        console.log('Fetched run metrics:', data);
        setRunMetadata(data);
      }
      catch (err) {
        console.error('Failed to fetch run metrics:', err);
      }
    }

    const fetchRunLogs = async () => {
      try {
        const res = await fetch(`http://127.0.0.1:8000/api/v1/training/runs/${selectedRun}/logs`);
        const data = await res.json();
        console.log('Fetched run logs:', data);

        for (let logLine of data) {
          parseOldLogLine(logLine);
        }

        setOldLogs(data || []);
        console.log('Parsed old logs and updated metrics:', oldLogs);
      }
      catch (err) {
        console.error('Failed to fetch run logs:', err);
      }
    }

    fetchRunMetaData();
    fetchRunLogs();
    // fetchRunMetrics();


  }, [selectedRun])

  // for elapsed time tracking
  useEffect(() => {
    if (trainingStatus !== 'running') {
      if (trainingTimerRef.current) {
        clearInterval(trainingTimerRef.current);
        trainingTimerRef.current = null;
      }
      return;
    }

    const start = Date.now();
    setTrainingStartTime(start);

    trainingTimerRef.current = setInterval(() => {
      const diff = Date.now() - start;
      setElapsedTime(formatTime(diff));
    }, 1000);

    return () => {
      clearInterval(trainingTimerRef.current);
      trainingTimerRef.current = null;
    };
  }, [trainingStatus]);


  // Log Polling Effect
  useEffect(() => {
    if (!shouldCheckLogs) {
      pollingRef.current = false;
      return;
    }

    pollingRef.current = true;
    offsetRef.current = 0; // reset when starting

    const poll = async () => {
      while (pollingRef.current) {
        try {
          const res = await fetch(
            `http://127.0.0.1:8000/api/v1/training/logs?lines=100&offset=${offsetRef.current}&tail=false`
          );

          if (res.ok) {
            const data = await res.json();
            console.log('Polled logs:', data);

            if (data.length > 0) {
              setTrainingLogs(prev => [...prev, ...data]);
              offsetRef.current += data.length;
              data.forEach(logLine => {
                parseLogLine(
                  logLine,
                  totalRounds,
                  () => {
                    pollingRef.current = false;
                    console.log('All rounds completed. Stopping log polling.');
                  }
                );
              });
            }
          }
        } catch (err) {
          console.error('Log polling failed:', err);
        }
        await new Promise(r => setTimeout(r, 5000));
      }
    };

    poll();

    return () => {
      pollingRef.current = false;
    };
  }, [shouldCheckLogs]);

  // Client Polling Effect
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(
          'http://localhost:3000/clients'
        );

        if (res.ok) {
          const data = await res.json();
          console.log('Polled clients:', data.clients);
          setConnectedClients(data.clients);

        }
      } catch (err) {
        console.error('Client polling failed:', err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);


  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 p-6 w-full">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="text-center mb-10 mt-5">
          <h1 className="text-5xl font-bold text-[#0098B0] mb-4">Data Training Dashboard</h1>
          <div className="w-32 h-1.5 bg-gradient-to-r from-[#0098B0]/20 to-[#0098B0]/70 mx-auto mb-4 rounded-full"></div>
          <p className="text-gray-600 text-lg max-w-2xl mx-auto">
            Monitor and manage federated learning training rounds with real-time insights and control
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300">
            <div className="flex items-center">
              <div className="bg-[#0098B0]/10 p-3 rounded-xl mr-4">
                <FontAwesomeIcon icon={faSyncAlt} className="text-xl text-[#0098B0]" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-1">{metrics.length}</h3>
                <p className="text-gray-600 text-sm">Completed Rounds</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300">
            <div className="flex items-center">
              <div className="bg-[#0098B0]/10 p-3 rounded-xl mr-4">
                <FontAwesomeIcon icon={faUsers} className="text-xl text-[#0098B0]" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-1">{connectedClients.length}</h3>
                <p className="text-gray-600 text-sm">Active Participants</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300">
            <div className="flex items-center">
              <div className="bg-[#0098B0]/10 p-3 rounded-xl mr-4">
                <FontAwesomeIcon icon={faChartLine} className="text-xl text-[#0098B0]" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-1">92.3%</h3>
                <p className="text-gray-600 text-sm">Best Accuracy</p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition-all duration-300">
            <div className="flex items-center">
              <div className="bg-[#0098B0]/10 p-3 rounded-xl mr-4">
                <FontAwesomeIcon icon={faServer} className="text-xl text-[#0098B0]" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-800 mb-1">{connectedClients.length}</h3>
                <p className="text-gray-600 text-sm">Nodes Online</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Training Control & Connected Clients */}
          <div className="lg:col-span-1 space-y-8">
            {/* Training Control Card */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <div className="flex items-center mb-6">
                <div className="bg-[#0098B0]/10 p-2 rounded-lg mr-3">
                  <FontAwesomeIcon icon={faCog} className="text-[#0098B0]" />
                </div>
                <h2 className="text-xl font-semibold text-gray-800">Training Control</h2>
              </div>

              <div className="space-y-4">
                <div className="bg-gray-50 p-4 rounded-xl">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-gray-600 font-medium">Current Status</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${trainingStatus === 'running' || trainingStatus === 'server_started' ? 'bg-green-100 text-green-800' :
                      trainingStatus === 'completed' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                      {trainingStatus === 'running' ? 'Running' :
                        trainingStatus === 'server_started' ? 'Server Started' :
                          trainingStatus === 'completed' ? 'Completed' : 'Idle'}
                    </span>
                  </div>

                  {/* Progress Bar for Active Training */}
                  {(trainingStatus === 'running' || trainingStatus === 'completed') && (
                    <div className="mt-3">

                      <div className="flex justify-between text-sm text-gray-600 mb-1">
                        <span>Round {metrics.length}</span>
                        <span>{metrics.length}/{totalRounds} rounds</span>
                      </div>

                      <div className="w-full bg-gray-200 rounded-full h-2.5">
                        <div
                          className="bg-gradient-to-r from-[#0098B0] to-[#00C2E0] h-2.5 rounded-full transition-all duration-500"
                          style={{ width: `${(metrics.length / totalRounds) * 100}%` }}
                        ></div>
                      </div>

                      <div className="flex justify-between text-xs text-gray-500 mt-1">
                        <span>
                          Start: {trainingStartTime
                            ? new Date(trainingStartTime).toLocaleTimeString()
                            : 'N/A'}
                        </span>

                        <span>
                          Elapsed: {elapsedTime}
                        </span>

                      </div>

                    </div>
                  )}
                </div>

                {/* Start/Stop Button Control */}
                <div className="flex gap-3">
                  {trainingStatus === 'running' ? (
                    <>
                      <button
                        onClick={stopTraining}
                        disabled={isClicked}
                        className={`flex-1 py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${isClicked
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : 'bg-gradient-to-r from-[#b00000] to-[#dd252e] text-white hover:shadow-md hover:scale-[1.02]'
                          }`}
                      >
                        <FontAwesomeIcon icon={faStopCircle} />
                        Stop
                      </button>
                    </>
                  ) : (trainingStatus === 'idle' || trainingStatus === 'completed' ? (
                    <>
                      <button
                        onClick={startServer}
                        disabled={isClicked}
                        className={`w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${isClicked
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : 'bg-gradient-to-r from-[#0098B0] to-[#00C2E0] text-white hover:shadow-md hover:scale-[1.02]'
                          }`}
                      >
                        <FontAwesomeIcon icon={faPlayCircle} />
                        Start Training
                      </button>
                    </>) : (
                    <button
                      onClick={() => sendStartTrainingCommand(1, 12)}
                      disabled={isClicked}
                      className={`w-full py-3 rounded-xl font-medium transition-all flex items-center justify-center gap-2 ${isClicked
                        ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        : 'bg-gradient-to-r from-[#0098B0] to-[#00C2E0] text-white hover:shadow-md hover:scale-[1.02]'
                        }`}
                    >
                      <FontAwesomeIcon icon={faPlayCircle} />
                      Send Signal to Clients
                    </button>
                  )
                  )}
                </div>
              </div>
            </div>

            {/* Connected Clients Card */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="bg-[#0098B0]/10 p-2 rounded-lg mr-3">
                    <FontAwesomeIcon icon={faNetworkWired} className="text-[#0098B0]" />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-800">Connected Clients</h2>
                </div>
                <span className="bg-[#0098B0]/10 text-[#0098B0] text-sm font-medium px-2 py-1 rounded-full">
                  {connectedClients.length} Active
                </span>
              </div>

              <div className="space-y-4 max-h-80 overflow-y-auto pr-2">
                {connectedClients.map((client, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors">
                    <div className="flex items-center">
                      <div className="w-3 h-3 rounded-full mr-3 bg-green-500"></div>
                      <div>
                        <h3 className="font-medium text-gray-800">{client}</h3>
                        <p className="text-xs text-gray-500">1 min</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-700">0.5 GB</p>
                      <p className="text-xs text-gray-500">Data</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Middle Column - Rounds Timeline & Select Run */}
          <div className="lg:col-span-2 space-y-8">

            {/* Run Selection Card */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
              {/* Header */}
              <div className="flex items-center mb-6">
                <div className="bg-[#0098B0]/10 p-2 rounded-lg mr-3">
                  <FontAwesomeIcon icon={faDatabase} className="text-[#0098B0]" />
                </div>
                <h2 className="text-xl font-semibold text-gray-800">
                  Select Training Run
                </h2>
              </div>

              {/* Dropdown + Button */}
              <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
                <select
                  className="w-full sm:w-80 px-4 py-2 text-[#078295] bg-[#0098B0]/10 font-semibold text-[16px] border-[1px] border-[#078295]-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#0098B0]"
                  defaultValue=""
                  value={selectedRun}
                  onChange={(e) => setSelectedRun(e.target.value)}
                >
                  <option value="" disabled>
                    Select a training run
                  </option>
                  {runList?.map((run, idx) => {
                    return (
                      <option value={run.run_id} key={idx}>
                        {run.run_id}
                      </option>
                    )
                  })}
                </select>

                <button
                  className={` font-semibold text-[16px]  px-5 py-2 rounded-xl transition-colors duration-200
                    ${trainingStatus !== 'running' ? 'bg-gray-300 text-gray-700 cursor-not-allowed' : 'text-white bg-gradient-to-r from-[#0098B0] to-[#00C2E0] hover:shadow-md hover:scale-[1.02]'}`}
                  onClick={() => setShowCurrentTraining(true)}
                  disabled={trainingStatus !== 'running'}
                >
                  Show Current Training Run
                </button>
              </div>
            </div>

            {/* Rounds Timeline */}
            {/* showing old training rounds */}
            {!showCurrentTraining ?
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <div className="flex items-center mb-6">
                  <div className="bg-[#0098B0]/10 p-2 rounded-lg mr-3">
                    <FontAwesomeIcon icon={faDatabase} className="text-[#0098B0]" />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-800">Training Rounds</h2>
                </div>
                <div className='px-2 pb-4 '>
                  {selectedRun && !showCurrentTraining &&
                    <div className='flex flex-col gap-1'>
                      <p className="text-[16px] text-gray-600 font-semibold">Run ID: <span className="font-medium text-gray-800">{runMetadata?.run_id || 'N/A'}</span></p>
                      <p className="text-[16px] text-gray-600 font-semibold">Status: <span className="font-medium text-gray-800">{runMetadata?.error_message === null ? 'COMPLETED' : 'ADMIN TERMINATED THE TRAINING PROCESS'}</span></p>
                      <p className="text-[16px] text-gray-600 font-semibold">Total Rounds: <span className="font-medium text-gray-800">{runMetadata?.total_rounds || 'N/A'}</span></p>
                      <p className="text-[16px] text-gray-600 font-semibold">Rounds Completed: <span className="font-medium text-gray-800">{runMetadata?.error_message === null ? runMetadata?.total_rounds : oldMetrics.length-1}</span></p>
                    </div>
                  }
                </div>
                <div className="space-y-4">
                  {oldMetrics?.map((round, idx) => {
                    let status = round.endTime == null ? 'failed' : 'completed';
                    return (
                      <div
                        key={idx}
                        className={`p-5 rounded-xl border-2 transition-all duration-300 cursor-pointer hover:shadow-md ${status === 'completed'
                          ? 'border-green-200 bg-green-50'
                          : 'border-red-200 bg-red-50'
                          }`}
                        onClick={() => setActiveRound(idx + 1)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${status === 'completed'
                              ? 'bg-green-500 text-white'
                              : 'bg-red-300 text-red-600'
                              }`}>
                              {status === 'completed' && <FontAwesomeIcon icon={faCheckCircle} />}
                              {status === 'failed' && <FontAwesomeIcon icon={faExclamationTriangle} />}
                            </div>

                            <div>
                              <h3 className="text-lg font-semibold text-gray-800">Round {idx + 1}</h3>
                            </div>
                          </div>

                          <div className="grid grid-cols-3 gap-6 text-center">
                            <div>
                              <p className="text-sm text-gray-600">Accuracy</p>
                              <p className="font-semibold text-[#0098B0]">
                                {round.accuracy || '-'}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Loss</p>
                              <p className="font-semibold text-[#0098B0]">{round.loss || '-'}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Duration</p>
                              <p className="font-semibold text-[#0098B0]">
                                {new Date(round.endTime).getTime() - new Date(round.startTime).getTime() > 0 ? (
                                  <span>
                                    {Math.floor((new Date(round.endTime).getTime() - new Date(round.startTime).getTime()) / 1000)} seconds
                                  </span>
                                ) : (
                                  '-'
                                )}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              :
              // {/* Show current training rounds with live updates */}
              <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <div className="flex items-center mb-6">
                  <div className="bg-[#0098B0]/10 p-2 rounded-lg mr-3">
                    <FontAwesomeIcon icon={faDatabase} className="text-[#0098B0]" />
                  </div>
                  <h2 className="text-xl font-semibold text-gray-800">Training Rounds</h2>
                </div>

                <div className="space-y-4">
                  {metrics.map((round, idx) => {
                    let status = round.accuracy == null ? 'in-progress' : 'completed';
                    return (
                      <div
                        key={idx}
                        className={`p-5 rounded-xl border-2 transition-all duration-300 cursor-pointer hover:shadow-md ${status === 'in-progress'
                          ? 'border-[#0098B0] bg-gradient-to-r from-[#0098B0]/5 to-[#0098B0]/10'
                          : status === 'completed'
                            ? 'border-green-200 bg-green-50'
                            : 'border-gray-200 bg-gray-50'
                          } ${activeRound === idx + 1 ? 'ring-2 ring-[#0098B0] ring-opacity-50' : ''}`}
                        onClick={() => setActiveRound(idx + 1)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-4">
                            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${status === 'in-progress'
                              ? 'bg-[#0098B0] text-white'
                              : status === 'completed'
                                ? 'bg-green-500 text-white'
                                : 'bg-gray-300 text-gray-600'
                              }`}>
                              {status === 'in-progress' && (
                                <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                                </svg>
                              )}
                              {status === 'completed' && <FontAwesomeIcon icon={faCheckCircle} />}
                            </div>

                            <div>
                              <h3 className="text-lg font-semibold text-gray-800">Round {idx + 1}</h3>
                            </div>
                          </div>

                          <div className="grid grid-cols-3 gap-6 text-center">
                            <div>
                              <p className="text-sm text-gray-600">Accuracy</p>
                              <p className="font-semibold text-[#0098B0]">
                                {round.accuracy || '-'}
                              </p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Loss</p>
                              <p className="font-semibold text-[#0098B0]">{round.loss || '-'}</p>
                            </div>
                            <div>
                              <p className="text-sm text-gray-600">Duration</p>
                              <p className="font-semibold text-[#0098B0]">
                                {round.duration || '-'} seconds
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            }
          </div>
        </div>

        {/* Logs Section */}
        {/* showing old logs */}
        {!showCurrentTraining ?
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mt-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-4">
              <div className="flex items-center">
                <div className="bg-gradient-to-br from-[#0098AF] to-[#00B4D8] p-2 rounded-xl mr-3 shadow-sm">
                  <FontAwesomeIcon icon={faExclamationTriangle} className="text-white text-sm" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-800">Training Logs</h2>
                </div>
              </div>
            </div>

            {/* Enhanced Console for logs */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 text-white p-4 rounded-xl h-80 overflow-hidden font-mono">
              {/* Console Header */}
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded-lg">
                    {oldLogs.length} entries
                  </span>
                </div>
              </div>

              {/* Logs Content */}
              <div className="h-60 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800 pr-2">
                <>
                  <div className="text-gray-400 text-sm mb-3 flex items-center gap-2">
                    <FontAwesomeIcon icon={faInfoCircle} className="text-[#0098AF]" />
                    Showing training logs for run: {selectedRun}
                  </div>
                  {oldLogs.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      <FontAwesomeIcon icon={faDatabase} className="text-2xl mb-2 opacity-50" />
                      <p>No training run selected</p>
                      <p className="text-sm mt-1">Logs will appear here when training run is selected or when live training begins</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {oldLogs?.map((log, index) => (
                        <div key={index} className="flex items-start gap-3 group hover:bg-gray-700/50 px-2 py-1 rounded transition-colors">
                          <span className="text-gray-500 text-xs mt-0.5 flex-shrink-0">[{index + 1}]</span>
                          <span className="text-[#00d4ff] flex-1">{log.timestamp + ' UTC - ' + log.level + ' - [RUN: ' + log.run_id + '] - ' + log.message}</span>
                          <span className="text-gray-600 text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                            {new Date().toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </>

              </div>
            </div>
          </div>
          :
          // {/* Show current training logs with live updates */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mt-8">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-4">
              <div className="flex items-center">
                <div className="bg-gradient-to-br from-[#0098AF] to-[#00B4D8] p-2 rounded-xl mr-3 shadow-sm">
                  <FontAwesomeIcon icon={faExclamationTriangle} className="text-white text-sm" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-800">Training Logs</h2>
                </div>
              </div>
            </div>

            {/* Enhanced Console for logs */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 border border-gray-700 text-white p-4 rounded-xl h-80 overflow-hidden font-mono">
              {/* Console Header */}
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-700">
                <div className="flex items-center gap-3">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 bg-gray-700 px-2 py-1 rounded-lg">
                    {traininglogs.length} entries
                  </span>
                </div>
              </div>

              {/* Logs Content */}
              <div className="h-60 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800 pr-2">
                <>
                  <div className="text-gray-400 text-sm mb-3 flex items-center gap-2">
                    <FontAwesomeIcon icon={faInfoCircle} className="text-[#0098AF]" />
                    Showing current training logs
                  </div>
                  {traininglogs.length === 0 ? (
                    <div className="text-center text-gray-500 py-8">
                      <FontAwesomeIcon icon={faDatabase} className="text-2xl mb-2 opacity-50" />
                      <p>No current training logs available</p>
                      <p className="text-sm mt-1">Logs will appear here when training starts</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {traininglogs.map((log, index) => (
                        <div key={`current-log-${index}`} className="flex items-start gap-3 group hover:bg-gray-700/50 px-2 py-1 rounded transition-colors">
                          <span className="text-gray-500 text-xs mt-0.5 flex-shrink-0">[{index + 1}]</span>
                          <span className="text-[#00d4ff] flex-1">{log.timestamp + ' UTC - ' + log.level + ' - [RUN: ' + log.run_id + '] - ' + log.message}</span>
                          <span className="text-gray-600 text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                            {new Date().toLocaleTimeString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </>

              </div>
            </div>
          </div>
        }
      </div>
    </div>
  );
};

export default DataTraining;