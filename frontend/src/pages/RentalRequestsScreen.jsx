import { useState } from 'react';

const initialRequests = [
  {
    id: 1,
    itemName: "Camping Tent",
    shopperName: "Alice Smith",
    requestedDates: "2026-10-15 to 2026-10-17",
    totalPrice: 45.00,
    status: "Pending"
  },
  {
    id: 2,
    itemName: "Power Drill",
    shopperName: "Bob Jones",
    requestedDates: "2026-10-20 to 2026-10-21",
    totalPrice: 15.00,
    status: "Accepted"
  }
];

export default function RentalRequestsScreen() {
  const [requests, setRequests] = useState(initialRequests);

  const handleStatusChange = (id, newStatus) => {
    setRequests(requests.map(req =>
      req.id === id ? { ...req, status: newStatus } : req
    ));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 mt-8">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Rental Requests</h2>

      <div className="bg-white shadow-md rounded-lg overflow-hidden border border-gray-200">
        {requests.length === 0 ? (
          <p className="p-6 text-gray-500 text-center">No rental requests at this time.</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {requests.map((request) => (
              <li key={request.id} className="p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center hover:bg-gray-50 transition-colors">

                <div className="mb-4 sm:mb-0">
                  <h3 className="text-lg font-semibold text-gray-900">{request.itemName}</h3>
                  <p className="text-sm text-gray-600 mt-1">Requested by: <span className="font-medium text-gray-800">{request.shopperName}</span></p>
                  <p className="text-sm text-gray-600 mt-1">Dates: <span className="font-medium text-gray-800">{request.requestedDates}</span></p>
                  <p className="text-sm text-gray-600 mt-1">
                    Total: <span className="font-semibold text-green-600">${request.totalPrice.toFixed(2)}</span>
                  </p>

                  <div className="mt-3">
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-full ${
                      request.status === 'Pending' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
                      request.status === 'Accepted' ? 'bg-green-100 text-green-800 border border-green-200' :
                      'bg-red-100 text-red-800 border border-red-200'
                    }`}>
                      {request.status}
                    </span>
                  </div>
                </div>

                {request.status === 'Pending' && (
                  <div className="flex space-x-3">
                    <button
                      onClick={() => handleStatusChange(request.id, 'Accepted')}
                      className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition shadow-sm"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleStatusChange(request.id, 'Declined')}
                      className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 transition shadow-sm"
                    >
                      Decline
                    </button>
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}