import React from 'react';

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-5xl font-bold text-gray-900">
          Smart Carpool Matching
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Find reliable ride partners with AI-powered route matching. Save money, save the environment.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-3xl mb-4">🚗</div>
          <h3 className="text-xl font-bold mb-2">Post a Ride</h3>
          <p className="text-gray-600">Share your commute and split costs with verified travelers.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-3xl mb-4">🤖</div>
          <h3 className="text-xl font-bold mb-2">AI Matching</h3>
          <p className="text-gray-600">Get matched with riders based on route, timing, and preferences.</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-3xl mb-4">⭐</div>
          <h3 className="text-xl font-bold mb-2">Trust System</h3>
          <p className="text-gray-600">Rate and build a reputation in our verified community.</p>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 p-8 rounded-lg text-center">
        <h2 className="text-2xl font-bold mb-4">Ready to get started?</h2>
        <div className="space-x-4">
          <a href="/signup" className="inline-block bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">
            Create Account
          </a>
          <a href="/login" className="inline-block border border-blue-600 text-blue-600 px-6 py-2 rounded-lg hover:bg-blue-50">
            Sign In
          </a>
        </div>
      </div>
    </div>
  );
}
