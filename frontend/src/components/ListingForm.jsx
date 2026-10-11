import { useState } from 'react';
import BlockedDatesCalendar from './BlockedDatesCalendar';

export default function ListingForm({ onSubmit }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');

  // Rental Settings State
  const [isRentable, setIsRentable] = useState(false);
  const [pricePerDay, setPricePerDay] = useState('');
  const [rentalError, setRentalError] = useState('');

  // New State for SCRUM-189: Blocked Dates Calendar
  const [blockedDates, setBlockedDates] = useState([]);

  const handleSubmit = (e) => {
    e.preventDefault();

    if (isRentable && (Number(pricePerDay) <= 0 || pricePerDay === '')) {
      setRentalError("Price per day must be greater than zero.");
      return;
    }

    setRentalError('');

    const formData = {
      title,
      description,
      isRentable,
      pricePerDay: isRentable ? Number(pricePerDay) : null,
      blockedDates: isRentable ? blockedDates : [], // Attach blocked dates to payload
    };

    if (onSubmit) {
      onSubmit(formData);
    } else {
      console.log("Form Submitted:", formData);
      alert("Listing saved successfully!");
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white shadow-md rounded-lg mt-8">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">Create New Listing</h2>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="Item name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            required
            rows="3"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            placeholder="Describe your item"
          />
        </div>

        {/* --- Rental Settings Section --- */}
        <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Rental Options</h3>

          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={isRentable}
              onChange={(e) => {
                setIsRentable(e.target.checked);
                if (!e.target.checked) setRentalError('');
              }}
              className="w-5 h-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
            />
            <span className="font-medium text-gray-700">Available for rent</span>
          </label>

          {isRentable && (
            <div className="mt-4 ml-8 animate-fade-in">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Price per day ($)
              </label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={pricePerDay}
                onChange={(e) => setPricePerDay(e.target.value)}
                className={`w-full max-w-[200px] p-2 border rounded-md shadow-sm ${
                  rentalError ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-blue-500'
                }`}
                placeholder="0.00"
              />
              {rentalError && (
                <p className="text-red-500 text-sm mt-1">{rentalError}</p>
              )}

              {/* Inject the SCRUM-189 Calendar Component here */}
              <BlockedDatesCalendar
                blockedDates={blockedDates}
                setBlockedDates={setBlockedDates}
              />

            </div>
          )}
        </div>

        <button
          type="submit"
          className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors"
        >
          Save Listing
        </button>
      </form>
    </div>
  );
}