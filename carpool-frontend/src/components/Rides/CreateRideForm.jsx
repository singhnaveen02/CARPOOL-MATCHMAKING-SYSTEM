import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import api from '../services/api';

export default function CreateRideForm({ onSuccess }) {
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const onSubmit = async (data) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/rides', {
        source_address: data.source_address,
        destination_address: data.destination_address,
        departure_datetime: `${data.departure_date}T${data.departure_time}:00`,
        seats_available: parseInt(data.seats_available),
        vehicle_type: data.vehicle_type,
        vehicle_name: data.vehicle_name,
        vehicle_plate: data.vehicle_plate,
        ride_details: {
          smoking: data.smoking,
          gender: data.gender,
          music: data.music,
          luggage: data.luggage,
          ac_preference: data.ac_preference,
          price_per_seat: parseFloat(data.price_per_seat),
          notes: data.notes,
        },
      });

      if (response.data.success) {
        alert('Ride posted successfully!');
        if (onSuccess) onSuccess(response.data.data);
      }
    } catch (err) {
      const message = err.response?.data?.detail || 'Failed to create ride. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-8 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Post a Ride</h2>

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From *
            </label>
            <input
              type="text"
              {...register('source_address', { required: 'Source is required' })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., IIT Roorkee"
            />
            {errors.source_address && <p className="text-red-500 text-sm mt-1">{errors.source_address.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To *
            </label>
            <input
              type="text"
              {...register('destination_address', { required: 'Destination is required' })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Haridwar"
            />
            {errors.destination_address && <p className="text-red-500 text-sm mt-1">{errors.destination_address.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Departure Date *
            </label>
            <input
              type="date"
              {...register('departure_date', { required: 'Date is required' })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            {errors.departure_date && <p className="text-red-500 text-sm mt-1">{errors.departure_date.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Departure Time *
            </label>
            <input
              type="time"
              {...register('departure_time', { required: 'Time is required' })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            {errors.departure_time && <p className="text-red-500 text-sm mt-1">{errors.departure_time.message}</p>}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Seats Available *
            </label>
            <select
              {...register('seats_available', { required: 'Seats required' })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              {[1, 2, 3, 4, 5, 6].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Vehicle Type
            </label>
            <select
              {...register('vehicle_type')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="car">Car</option>
              <option value="auto">Auto</option>
              <option value="van">Van</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Price per Seat (₹)
            </label>
            <input
              type="number"
              {...register('price_per_seat')}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="100"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Smoking
            </label>
            <select {...register('smoking')} className="w-full px-4 py-2 border border-gray-300 rounded-lg">
              <option value="no_preference">No Preference</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              AC
            </label>
            <select {...register('ac_preference')} className="w-full px-4 py-2 border border-gray-300 rounded-lg">
              <option value="no_preference">No Preference</option>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes
          </label>
          <textarea
            {...register('notes')}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Any additional details about the ride..."
            rows="3"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? 'Posting...' : 'Post Ride'}
        </button>
      </form>
    </div>
  );
}
