import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../services/api';

export default function SearchRidesForm() {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const onSubmit = async (data) => {
    setLoading(true);

    try {
      const response = await api.post('/rides/search', {
        source_lat: parseFloat(data.source_lat),
        source_lng: parseFloat(data.source_lng),
        destination_lat: parseFloat(data.destination_lat),
        destination_lng: parseFloat(data.destination_lng),
        departure_date: data.departure_date,
        time_window_minutes: 120,
      });

      if (response.data.success) {
        setResults(response.data.data.rides);
      }
    } catch (err) {
      alert('Search failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h2 className="text-2xl font-bold mb-6">Find a Ride</h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                From *
              </label>
              <input
                type="text"
                {...register('source_lat', { required: true })}
                placeholder="Source Latitude"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Longitude
              </label>
              <input
                type="text"
                {...register('source_lng', { required: true })}
                placeholder="Source Longitude"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                To Latitude *
              </label>
              <input
                type="text"
                {...register('destination_lat', { required: true })}
                placeholder="Destination Latitude"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                To Longitude
              </label>
              <input
                type="text"
                {...register('destination_lng', { required: true })}
                placeholder="Destination Longitude"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date *
            </label>
            <input
              type="date"
              {...register('departure_date', { required: true })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search Rides'}
          </button>
        </form>
      </div>

      {results && (
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h3 className="text-xl font-bold mb-4">Found {results.length} Rides</h3>
          <div className="space-y-4">
            {results.map(ride => (
              <div key={ride.id} className="border border-gray-300 rounded-lg p-4 hover:shadow-lg transition">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-bold">{ride.source_address} → {ride.destination_address}</h4>
                    <p className="text-sm text-gray-600">{new Date(ride.departure_datetime).toLocaleString()}</p>
                  </div>
                  <span className="text-lg font-bold text-blue-600">{ride.seats_available} seats</span>
                </div>
                <button className="mt-3 bg-green-500 text-white px-4 py-1 rounded hover:bg-green-600">
                  View Details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
