// import React, { useState } from 'react';
// import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
// import { 
//   faSyncAlt, 
//   faPlayCircle, 
//   faPauseCircle,
//   faChartLine,
//   faUsers,
//   faServer,
//   faClock,
//   faCheckCircle,
//   faExclamationTriangle
// } from '@fortawesome/free-solid-svg-icons';

// const FederatedRounds = () => {
//   const [activeRound, setActiveRound] = useState(1);
//   const [isTraining, setIsTraining] = useState(false);
//   const [rounds] = useState([
//     { id: 1, status: 'completed', accuracy: '92.3%', participants: 12, duration: '2h 15m' },
//     { id: 2, status: 'completed', accuracy: '94.1%', participants: 15, duration: '1h 45m' },
//     { id: 3, status: 'completed', accuracy: '95.7%', participants: 18, duration: '2h 30m' },
//     { id: 4, status: 'in-progress', accuracy: 'processing...', participants: 20, duration: '45m' },
//     { id: 5, status: 'pending', accuracy: '-', participants: 22, duration: '-' }
//   ]);

//   const startTraining = () => {
//     setIsTraining(true);
//     // Simulate training process
//     setTimeout(() => {
//       setIsTraining(false);
//     }, 5000);
//   };

//   return (
//     <div className="min-h-screen bg-gradient-to-br from-white to-gray-50 p-6 w-full">
//       <div className="max-w-7xl mx-auto">
//         {/* Header Section */}
//         <div className="text-center mb-12 mt-5">
//           <h1 className="text-6xl font-bold text-[#0098B0] mb-2">Federated Rounds</h1>
//           <div className="w-24 h-1 bg-[#0098B0]/30 mx-auto mb-4"></div>
//           <p className="text-gray-600 text-lg max-w-3xl mx-auto">
//             Monitor and manage distributed training rounds across multiple participants
//           </p>
//         </div>

//         {/* Stats Overview */}
//         <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
//           <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 text-center">
//             <div className="bg-[#0098B0]/10 p-3 rounded-full inline-flex items-center justify-center mb-4">
//               <FontAwesomeIcon icon={faSyncAlt} className="text-2xl text-[#0098B0]" />
//             </div>
//             <h3 className="text-2xl font-bold text-[#0098B0] mb-2">4</h3>
//             <p className="text-gray-600">Total Rounds</p>
//           </div>

//           <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 text-center">
//             <div className="bg-[#0098B0]/10 p-3 rounded-full inline-flex items-center justify-center mb-4">
//               <FontAwesomeIcon icon={faUsers} className="text-2xl text-[#0098B0]" />
//             </div>
//             <h3 className="text-2xl font-bold text-[#0098B0] mb-2">20</h3>
//             <p className="text-gray-600">Active Participants</p>
//           </div>

//           <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 text-center">
//             <div className="bg-[#0098B0]/10 p-3 rounded-full inline-flex items-center justify-center mb-4">
//               <FontAwesomeIcon icon={faChartLine} className="text-2xl text-[#0098B0]" />
//             </div>
//             <h3 className="text-2xl font-bold text-[#0098B0] mb-2">95.7%</h3>
//             <p className="text-gray-600">Best Accuracy</p>
//           </div>

//           <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 text-center">
//             <div className="bg-[#0098B0]/10 p-3 rounded-full inline-flex items-center justify-center mb-4">
//               <FontAwesomeIcon icon={faServer} className="text-2xl text-[#0098B0]" />
//             </div>
//             <h3 className="text-2xl font-bold text-[#0098B0] mb-2">12</h3>
//             <p className="text-gray-600">Nodes Online</p>
//           </div>
//         </div>

//         {/* Control Section */}
//         <div className="bg-white p-8 rounded-2xl shadow-md border border-gray-100 mb-12">
//           <div className="flex flex-col md:flex-row items-center justify-between gap-6">
//             <div className="flex-1">
//               <h2 className="text-2xl font-semibold text-gray-800 mb-2">Round Control</h2>
//               <p className="text-gray-600">Manage current federated learning round</p>
//             </div>
            
//             <div className="flex gap-4">
//               <button
//                 onClick={startTraining}
//                 disabled={isTraining}
//                 className={`px-8 py-3 rounded-xl font-medium transition-all ${
//                   isTraining
//                     ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
//                     : 'bg-[#0098B0] text-white hover:bg-[#007a96] hover:scale-[1.02]'
//                 } flex items-center justify-center`}
//               >
//                 {isTraining ? (
//                   <>
//                     <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
//                       <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
//                       <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
//                     </svg>
//                     Running...
//                   </>
//                 ) : (
//                   <>
//                     <FontAwesomeIcon icon={faPlayCircle} className="mr-2" />
//                     Start Round
//                   </>
//                 )}
//               </button>

//               <button className="px-8 py-3 rounded-xl font-medium bg-gray-100 text-gray-700 hover:bg-gray-200 transition-all flex items-center justify-center">
//                 <FontAwesomeIcon icon={faPauseCircle} className="mr-2" />
//                 Pause
//               </button>
//             </div>
//           </div>
//         </div>

//         {/* Rounds Timeline */}
//         <div className="bg-white p-8 rounded-2xl shadow-md border border-gray-100 mb-12">
//           <h2 className="text-2xl font-semibold text-gray-800 mb-6">Training Rounds</h2>
          
//           <div className="space-y-6">
//             {rounds.map((round) => (
//               <div
//                 key={round.id}
//                 className={`p-6 rounded-xl border-2 transition-all duration-300 ${
//                   round.status === 'in-progress'
//                     ? 'border-[#0098B0] bg-[#0098B0]/5'
//                     : round.status === 'completed'
//                     ? 'border-green-200 bg-green-50'
//                     : 'border-gray-200 bg-gray-50'
//                 } ${activeRound === round.id ? 'ring-2 ring-[#0098B0]' : ''}`}
//                 onClick={() => setActiveRound(round.id)}
//               >
//                 <div className="flex items-center justify-between">
//                   <div className="flex items-center space-x-4">
//                     <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
//                       round.status === 'in-progress'
//                         ? 'bg-[#0098B0] text-white'
//                         : round.status === 'completed'
//                         ? 'bg-green-500 text-white'
//                         : 'bg-gray-300 text-gray-600'
//                     }`}>
//                       {round.status === 'in-progress' && (
//                         <svg className="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
//                           <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
//                           <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
//                         </svg>
//                       )}
//                       {round.status === 'completed' && <FontAwesomeIcon icon={faCheckCircle} />}
//                       {round.status === 'pending' && <FontAwesomeIcon icon={faClock} />}
//                     </div>
                    
//                     <div>
//                       <h3 className="text-lg font-semibold text-gray-800">Round {round.id}</h3>
//                       <p className={`text-sm ${
//                         round.status === 'in-progress'
//                           ? 'text-[#0098B0]'
//                           : round.status === 'completed'
//                           ? 'text-green-600'
//                           : 'text-gray-500'
//                       }`}>
//                         {round.status === 'in-progress' && 'In Progress'}
//                         {round.status === 'completed' && 'Completed'}
//                         {round.status === 'pending' && 'Pending'}
//                       </p>
//                     </div>
//                   </div>

//                   <div className="grid grid-cols-3 gap-8 text-center">
//                     <div>
//                       <p className="text-sm text-gray-600">Accuracy</p>
//                       <p className="font-semibold text-[#0098B0]">{round.accuracy}</p>
//                     </div>
//                     <div>
//                       <p className="text-sm text-gray-600">Participants</p>
//                       <p className="font-semibold text-[#0098B0]">{round.participants}</p>
//                     </div>
//                     <div>
//                       <p className="text-sm text-gray-600">Duration</p>
//                       <p className="font-semibold text-[#0098B0]">{round.duration}</p>
//                     </div>
//                   </div>
//                 </div>
//               </div>
//             ))}
//           </div>
//         </div>

//         {/* Current Round Details */}
//         <div className="bg-white p-8 rounded-2xl shadow-md border border-gray-100">
//           <h2 className="text-2xl font-semibold text-gray-800 mb-6">Round {activeRound} Details</h2>
          
//           <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
//             <div>
//               <h3 className="text-lg font-semibold text-gray-800 mb-4">Performance Metrics</h3>
//               <div className="space-y-4">
//                 <div className="flex justify-between items-center p-4 bg-[#0098B0]/5 rounded-xl">
//                   <span className="text-gray-600">Global Accuracy</span>
//                   <span className="font-semibold text-[#0098B0]">94.2%</span>
//                 </div>
//                 <div className="flex justify-between items-center p-4 bg-[#0098B0]/5 rounded-xl">
//                   <span className="text-gray-600">Loss</span>
//                   <span className="font-semibold text-[#0098B0]">0.124</span>
//                 </div>
//                 <div className="flex justify-between items-center p-4 bg-[#0098B0]/5 rounded-xl">
//                   <span className="text-gray-600">Convergence Rate</span>
//                   <span className="font-semibold text-[#0098B0]">87%</span>
//                 </div>
//               </div>
//             </div>

//             <div>
//               <h3 className="text-lg font-semibold text-gray-800 mb-4">Participant Statistics</h3>
//               <div className="space-y-4">
//                 <div className="flex justify-between items-center p-4 bg-[#0098B0]/5 rounded-xl">
//                   <span className="text-gray-600">Active Nodes</span>
//                   <span className="font-semibold text-[#0098B0]">18/20</span>
//                 </div>
//                 <div className="flex justify-between items-center p-4 bg-[#0098B0]/5 rounded-xl">
//                   <span className="text-gray-600">Avg. Data Size</span>
//                   <span className="font-semibold text-[#0098B0]">2.4 GB</span>
//                 </div>
//                 <div className="flex justify-between items-center p-4 bg-[#0098B0]/5 rounded-xl">
//                   <span className="text-gray-600">Completion Rate</span>
//                   <span className="font-semibold text-[#0098B0]">92%</span>
//                 </div>
//               </div>
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default FederatedRounds;

import React, { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faCheckCircle,
  faUsers,
  faClock,
  faChartLine,
} from '@fortawesome/free-solid-svg-icons';

const FederatedRounds = () => {
  const [selectedModel, setSelectedModel] = useState('v01_2026_05_17_18_30');

  const models = [
    {
      id: 'v01_2026_05_17_18_30',
      name: 'Model v01 • 17 May 2026 • 6:30 PM',
      rounds: [
        {
          id: 1,
          accuracy: '91.8%',
          participants: 2,
          duration: '149s',
          loss: '0.241',
        },
        {
          id: 2,
          accuracy: '93.6%',
          participants: 2,
          duration: '147s',
          loss: '0.189',
        }
      ],
    },
  ];

  const selectedModelData = models.find(
    (model) => model.id === selectedModel
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-gray-50 p-6 w-full">
      <div className="max-w-6xl mx-auto">

        {/* Page Header */}
        <div className="text-center mb-12 mt-5">
          <h1 className="text-5xl font-bold text-[#0098B0] mb-3">
            Model Training History
          </h1>

          <div className="w-24 h-1 bg-[#0098B0]/30 mx-auto mb-4"></div>

          <p className="text-gray-600 text-lg">
            View completed federated learning rounds for trained models
          </p>
        </div>

        {/* Model Selector */}
        <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100 mb-10">
          <div className="flex flex-col gap-3">
            <label className="text-lg font-semibold text-gray-800">
              Select Trained Model
            </label>

            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full md:w-[420px] px-4 py-3 rounded-xl border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#0098B0] text-gray-700"
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Training Rounds */}
        <div className="bg-white p-8 rounded-2xl shadow-md border border-gray-100">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-semibold text-gray-800">
                Completed Training Rounds
              </h2>

              <p className="text-gray-500 mt-1">
                Aggregated round performance for the selected model
              </p>
            </div>

            <div className="hidden md:flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-xl">
              <FontAwesomeIcon icon={faCheckCircle} />
              <span className="font-medium">Training Completed</span>
            </div>
          </div>

          <div className="space-y-6">
            {selectedModelData.rounds.map((round) => (
              <div
                key={round.id}
                className="p-6 rounded-2xl border border-green-200 bg-green-50 hover:shadow-md transition-all duration-300"
              >
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">

                  {/* Left Side */}
                  <div className="flex items-center gap-5">
                    <div className="w-14 h-14 rounded-full bg-green-500 text-white flex items-center justify-center text-xl">
                      <FontAwesomeIcon icon={faCheckCircle} />
                    </div>

                    <div>
                      <h3 className="text-xl font-semibold text-gray-800">
                        Round {round.id}
                      </h3>

                      <p className="text-green-700 font-medium">
                        Completed Successfully
                      </p>
                    </div>
                  </div>

                  {/* Right Side Stats */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-5">

                    <div className="bg-white px-5 py-4 rounded-xl min-w-[120px] text-center border border-gray-100">
                      <div className="flex items-center justify-center mb-2 text-[#0098B0]">
                        <FontAwesomeIcon icon={faChartLine} />
                      </div>

                      <p className="text-sm text-gray-500">Accuracy</p>

                      <p className="font-semibold text-[#0098B0]">
                        {round.accuracy}
                      </p>
                    </div>

                    <div className="bg-white px-5 py-4 rounded-xl min-w-[120px] text-center border border-gray-100">
                      <div className="flex items-center justify-center mb-2 text-[#0098B0]">
                        <FontAwesomeIcon icon={faUsers} />
                      </div>

                      <p className="text-sm text-gray-500">Participants</p>

                      <p className="font-semibold text-[#0098B0]">
                        {round.participants}
                      </p>
                    </div>

                    <div className="bg-white px-5 py-4 rounded-xl min-w-[120px] text-center border border-gray-100">
                      <div className="flex items-center justify-center mb-2 text-[#0098B0]">
                        <FontAwesomeIcon icon={faClock} />
                      </div>

                      <p className="text-sm text-gray-500">Duration</p>

                      <p className="font-semibold text-[#0098B0]">
                        {round.duration}
                      </p>
                    </div>

                    <div className="bg-white px-5 py-4 rounded-xl min-w-[120px] text-center border border-gray-100">
                      <div className="flex items-center justify-center mb-2 text-[#0098B0]">
                        <FontAwesomeIcon icon={faChartLine} />
                      </div>

                      <p className="text-sm text-gray-500">Loss</p>

                      <p className="font-semibold text-[#0098B0]">
                        {round.loss}
                      </p>
                    </div>

                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default FederatedRounds;