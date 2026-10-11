// Helper to format dates as YYYY-MM-DD for consistent comparison
const formatDate = (date) => {
  const d = new Date(date);
  // Adjust for local timezone offset to avoid date shifting
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().split('T')[0];
};

export default function BlockedDatesCalendar({ blockedDates, setBlockedDates }) {
  // Hard-coded already-booked dates as requested in SCRUM-189
  const today = new Date();
  const bookedDates = [
    formatDate(new Date(today.getFullYear(), today.getMonth(), 15)),
    formatDate(new Date(today.getFullYear(), today.getMonth(), 16)),
    formatDate(new Date(today.getFullYear(), today.getMonth(), 17))
  ];

  const year = today.getFullYear();
  const month = today.getMonth();

  // Calculate days for the grid
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfMonth = new Date(year, month, 1).getDay();

  const handleDateClick = (dateStr) => {
    // Prevent interaction with already booked dates
    if (bookedDates.includes(dateStr)) return;

    // Toggle block/unblock
    if (blockedDates.includes(dateStr)) {
      setBlockedDates(blockedDates.filter(d => d !== dateStr));
    } else {
      setBlockedDates([...blockedDates, dateStr]);
    }
  };

  const days = [];
  // Empty slots for days before the 1st of the month
  for (let i = 0; i < firstDayOfMonth; i++) {
    days.push(<div key={`empty-${i}`} className="p-2"></div>);
  }

  // Fill in the actual days
  for (let d = 1; d <= daysInMonth; d++) {
    const currentDate = new Date(year, month, d);
    const dateStr = formatDate(currentDate);

    const isBooked = bookedDates.includes(dateStr);
    const isBlocked = blockedDates.includes(dateStr);

    let baseClass = "p-2 border rounded-md text-center text-sm transition-colors ";

    if (isBooked) {
      baseClass += "bg-gray-200 text-gray-400 cursor-not-allowed border-gray-200";
    } else if (isBlocked) {
      baseClass += "bg-red-500 text-white cursor-pointer hover:bg-red-600 border-red-500 shadow-sm";
    } else {
      baseClass += "bg-white text-gray-700 cursor-pointer hover:bg-blue-50 border-gray-300";
    }

    days.push(
      <div
        key={dateStr}
        onClick={() => handleDateClick(dateStr)}
        className={baseClass}
        title={isBooked ? "Already booked by a user" : isBlocked ? "Blocked by you" : "Available"}
      >
        {d}
      </div>
    );
  }

  const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

  return (
    <div className="mt-6 bg-white p-5 border border-gray-200 rounded-lg shadow-sm">
      <h4 className="text-md font-semibold text-gray-800 mb-1">Manage Availability</h4>
      <p className="text-sm text-gray-500 mb-4">
        Click dates to block or unblock them. Gray dates are already booked by shoppers.
      </p>

      <div className="text-center font-medium text-gray-700 mb-4">
        {monthNames[month]} {year}
      </div>

      <div className="grid grid-cols-7 gap-2 mb-2 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">
        <div>Sun</div><div>Mon</div><div>Tue</div><div>Wed</div><div>Thu</div><div>Fri</div><div>Sat</div>
      </div>

      <div className="grid grid-cols-7 gap-2">
        {days}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 mt-6 text-xs text-gray-600">
        <div className="flex items-center"><div className="w-3 h-3 bg-white border border-gray-300 mr-2 rounded-sm"></div> Available</div>
        <div className="flex items-center"><div className="w-3 h-3 bg-red-500 mr-2 rounded-sm"></div> Blocked</div>
        <div className="flex items-center"><div className="w-3 h-3 bg-gray-200 mr-2 rounded-sm"></div> Booked</div>
      </div>
    </div>
  );
}
