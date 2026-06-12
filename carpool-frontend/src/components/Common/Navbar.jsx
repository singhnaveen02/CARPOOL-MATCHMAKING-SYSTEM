export default function Navbar() {
  return (
    <nav className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-blue-600">🚗 Carpool</h1>
        <div className="space-x-4">
          <a href="/" className="text-gray-700 hover:text-blue-600">Home</a>
          <a href="/search" className="text-gray-700 hover:text-blue-600">Search</a>
          <a href="/dashboard" className="text-gray-700 hover:text-blue-600">Dashboard</a>
          <a href="/profile" className="text-gray-700 hover:text-blue-600">Profile</a>
        </div>
      </div>
    </nav>
  );
}
