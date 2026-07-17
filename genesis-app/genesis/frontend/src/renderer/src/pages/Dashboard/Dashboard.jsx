import React, { useEffect, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faBrain,
  faDatabase,
  faFileAlt,
  faUsers,
  faClock,
  faArrowUpRightFromSquare,
  faXmark,
  faSyncAlt,
  faChartLine,
} from "@fortawesome/free-solid-svg-icons";

function Dashboard() {
  const [clientData, setClientData] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // Fetch client info
  useEffect(() => {
    const handleFetchedData = (_, data) => {
      if (data.success) setClientData(data.client);
      else console.error("Error fetching client data:", data.error);
    };

    window.electron.ipcRenderer.on("fetched-client-data", handleFetchedData);
    window.electron.ipcRenderer.send("get-client-data", "satirtha");

    return () => {
      window.electron.ipcRenderer.removeAllListeners("fetched-client-data");
    };
  }, []);

  if (!clientData) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500">
        Loading Dashboard...
      </div>
    );
  }

  // Sort activities by time (newest first)
  const sortedActivities = [...clientData.recent_activity].sort(
    (a, b) => new Date(b.time) - new Date(a.time)
  );

  const topActivities = sortedActivities.slice(0, 5);

  const statusColor = (status) => {
    switch (status) {
      case "green":
        return "bg-green-500";
      case "red":
        return "bg-red-500";
      case "blue":
        return "bg-blue-500";
      default:
        return "bg-gray-400";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-gray-50 p-6 w-full">
      <div className="max-w-7xl mx-auto">
        {/* Welcome Header */}
        <div className="text-center mb-10 mt-5">
          <h1 className="text-4xl font-bold text-[#0098B0] mb-2">
            Welcome, {clientData.name || clientData.userid} 👋
          </h1>
          <p className="text-gray-600">
            Here's an overview of your recent activity and contributions
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="bg-[#0098B0]/10 p-3 rounded-full mr-3">
                <FontAwesomeIcon icon={faBrain} className="text-2xl text-[#0098B0]" />
              </div>
              <h3 className="text-gray-800 font-semibold text-lg">Inferences</h3>
            </div>
            <p className="text-3xl font-bold text-gray-900">{clientData.inference_count}</p>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="bg-[#0098B0]/10 p-3 rounded-full mr-3">
                <FontAwesomeIcon icon={faUsers} className="text-2xl text-[#0098B0]" />
              </div>
              <h3 className="text-gray-800 font-semibold text-lg">Contributions</h3>
            </div>
            <p className="text-3xl font-bold text-gray-900">{clientData.contribution_count}</p>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="bg-[#0098B0]/10 p-3 rounded-full mr-3">
                <FontAwesomeIcon icon={faDatabase} className="text-2xl text-[#0098B0]" />
              </div>
              <h3 className="text-gray-800 font-semibold text-lg">Data Size</h3>
            </div>
            <p className="text-3xl font-bold text-gray-900">{(clientData.total_datasize_contributed / (1024 * 1024)).toFixed(2)} MB</p>
          </div>

          <div className="bg-white p-6 rounded-2xl shadow-md border border-gray-100">
            <div className="flex items-center mb-4">
              <div className="bg-[#0098B0]/10 p-3 rounded-full mr-3">
                <FontAwesomeIcon icon={faFileAlt} className="text-2xl text-[#0098B0]" />
              </div>
              <h3 className="text-gray-800 font-semibold text-lg">Data Rows</h3>
            </div>
            <p className="text-3xl font-bold text-gray-900">{clientData.total_datarows_contributed}</p>
          </div>
        </div>
<div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-4">
        {/* Recent Activity */}
        <div className="bg-white p-8 rounded-2xl shadow-md border border-gray-100 mb-12">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center">
              <FontAwesomeIcon icon={faClock} className="text-2xl text-[#0098B0] mr-3" />
              <h2 className="text-2xl font-bold text-gray-800">Recent Activity</h2>
            </div>
            <button
              onClick={() => setShowModal(true)}
              className="text-[#0098B0] hover:underline flex items-center"
            >
              Show All
              <FontAwesomeIcon icon={faArrowUpRightFromSquare} className="ml-2 text-sm" />
            </button>
          </div>

          <div className="space-y-4">
            {topActivities.map((activity) => (
              <div
                key={activity._id}
                className="flex items-start p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors"
              >
                <div className={`w-3 h-3 rounded-full ${statusColor(activity.status)} mt-1 mr-4`} />
                <div className="flex-1">
                  <p className="font-medium text-gray-800">{activity.title}</p>
                  <p className="text-sm text-gray-600">{activity.description}</p>
                </div>
                <p className="text-sm text-gray-500">
                  {new Date(activity.time).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white p-8 rounded-2xl shadow-md border border-gray-100 mb-12">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Quick Actions</h2>
          <div className="grid grid-cols-1 gap-4">
            <button className="flex items-center p-4 bg-[#0098B0]/5 rounded-xl border border-[#0098B0]/20 hover:bg-[#0098B0]/10 transition-all">
              <div className="bg-[#0098B0] p-3 rounded-full mr-4">
                <FontAwesomeIcon icon={faBrain} className="text-white text-lg" />
              </div>
              <div className="text-left">
                <p className="font-medium text-gray-800">Start New Inference</p>
                <p className="text-sm text-gray-600">Process new data with your models</p>
              </div>
            </button>

            <button className="flex items-center p-4 bg-[#0098B0]/5 rounded-xl border border-[#0098B0]/20 hover:bg-[#0098B0]/10 transition-all">
              <div className="bg-[#0098B0] p-3 rounded-full mr-4">
                <FontAwesomeIcon icon={faSyncAlt} className="text-white text-lg" />
              </div>
              <div className="text-left">
                <p className="font-medium text-gray-800">Initiate Federated Round</p>
                <p className="text-sm text-gray-600">Start a new training round</p>
              </div>
            </button>

            <button className="flex items-center p-4 bg-[#0098B0]/5 rounded-xl border border-[#0098B0]/20 hover:bg-[#0098B0]/10 transition-all">
              <div className="bg-[#0098B0] p-3 rounded-full mr-4">
                <FontAwesomeIcon icon={faUsers} className="text-white text-lg" />
              </div>
              <div className="text-left">
                <p className="font-medium text-gray-800">Manage Participants</p>
                <p className="text-sm text-gray-600">View and manage node access</p>
              </div>
            </button>

            <button className="flex items-center p-4 bg-[#0098B0]/5 rounded-xl border border-[#0098B0]/20 hover:bg-[#0098B0]/10 transition-all">
              <div className="bg-[#0098B0] p-3 rounded-full mr-4">
                <FontAwesomeIcon icon={faChartLine} className="text-white text-lg" />
              </div>
              <div className="text-left">
                <p className="font-medium text-gray-800">View Analytics</p>
                <p className="text-sm text-gray-600">Explore performance metrics</p>
              </div>
            </button>
          </div>
        </div>
</div>
        {/* System Status */}
        <div className="bg-white p-8 rounded-2xl shadow-md border border-gray-100 mb-12">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="flex items-center mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                <span className="font-medium text-gray-800">Federated Learning</span>
              </div>
              <p className="text-sm text-gray-600">All systems operational</p>
            </div>

            <div className="p-4 bg-green-50 rounded-xl border border-green-200">
              <div className="flex items-center mb-2">
                <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                <span className="font-medium text-gray-800">Inference Engine</span>
              </div>
              <p className="text-sm text-gray-600">Running normally</p>
            </div>

            <div className="p-4 bg-yellow-50 rounded-xl border border-yellow-200">
              <div className="flex items-center mb-2">
                <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                <span className="font-medium text-gray-800">Data Storage</span>
              </div>
              <p className="text-sm text-gray-600">85% capacity used</p>
            </div>
          </div>
        </div>
      </div>

      {/* Modal for All Activities */}
      {showModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-2xl shadow-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
            >
              <FontAwesomeIcon icon={faXmark} className="text-xl" />
            </button>
            <h2 className="text-2xl font-bold text-gray-800 mb-6">
              All Activities
            </h2>
            <div className="space-y-4">
              {sortedActivities.map((activity) => (
                <div
                  key={activity._id}
                  className="flex items-start p-4 border border-gray-100 rounded-xl hover:bg-gray-50 transition-colors"
                >
                  <div
                    className={`w-3 h-3 rounded-full ${statusColor(activity.status)} mt-1 mr-4`}
                  />
                  <div className="flex-1">
                    <p className="font-medium text-gray-800">{activity.title}</p>
                    <p className="text-sm text-gray-600">{activity.description}</p>
                  </div>
                  <p className="text-sm text-gray-500">
                    {new Date(activity.time).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
