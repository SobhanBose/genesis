import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCheckCircle, faClock } from '@fortawesome/free-solid-svg-icons';

const RoundMetrics = ({ round, activeRound, onSelect }) => {
  // Determine display based on status
  const displayAccuracy =
    round.status === 'in-progress'
      ? `${(round.accuracy * 100 || 0).toFixed(2)}%`
      : round.status === 'completed'
      ? `${(round.accuracy * 100 || 0).toFixed(2)}%`
      : '-';

  const displayEpoch = round.epoch || '-';

  const displayDuration =
    round.status === 'completed' && round.timeTakenSec
      ? `${(round.timeTakenSec / 60).toFixed(1)}m`
      : round.status === 'in-progress'
      ? 'Running...'
      : '-';

  return (
    <div
      className={`p-6 rounded-xl border-2 transition-all duration-300 cursor-pointer ${
        round.status === 'in-progress'
          ? 'border-[#0098B0] bg-[#0098B0]/5'
          : round.status === 'completed'
          ? 'border-green-200 bg-green-50'
          : 'border-gray-200 bg-gray-50'
      } ${activeRound === round.round ? 'ring-2 ring-[#0098B0]' : ''}`}
      onClick={() => onSelect(round.round)}
    >
      <div className="flex items-center justify-between">
        {/* Round Info */}
        <div className="flex items-center space-x-4">
          <div
            className={`w-12 h-12 rounded-full flex items-center justify-center ${
              round.status === 'in-progress'
                ? 'bg-[#0098B0] text-white'
                : round.status === 'completed'
                ? 'bg-green-500 text-white'
                : 'bg-gray-300 text-gray-600'
            }`}
          >
            {round.status === 'in-progress' && (
              <svg
                className="animate-spin h-6 w-6"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
              </svg>
            )}
            {round.status === 'completed' && <FontAwesomeIcon icon={faCheckCircle} />}
            {round.status === 'pending' && <FontAwesomeIcon icon={faClock} />}
          </div>

          <div>
            <h3 className="text-lg font-semibold text-gray-800">Round {round.round}</h3>
            <p
              className={`text-sm ${
                round.status === 'in-progress'
                  ? 'text-[#0098B0]'
                  : round.status === 'completed'
                  ? 'text-green-600'
                  : 'text-gray-500'
              }`}
            >
              {round.status === 'in-progress' && 'In Progress'}
              {round.status === 'completed' && 'Completed'}
              {round.status === 'pending' && 'Pending'}
            </p>
          </div>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-4 gap-8 text-center">
          <div>
            <p className="text-sm text-gray-600">Accuracy</p>
            <p className="font-semibold text-[#0098B0]">{displayAccuracy}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Loss</p>
            <p className="font-semibold text-[#0098B0]">
              {round.loss ? round.loss.toFixed(4) : '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Epoch</p>
            <p className="font-semibold text-[#0098B0]">{displayEpoch}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Duration</p>
            <p className="font-semibold text-[#0098B0]">{displayDuration}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoundMetrics;
