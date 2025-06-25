import React, { useEffect, useState } from 'react';

const OAuthCallback: React.FC = () => {
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing Gmail Authorization...');

  useEffect(() => {
    // Get URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const oauthSuccess = urlParams.get('oauth_success');
    const oauthError = urlParams.get('oauth_error');
    const email = urlParams.get('email');

    // Handle OAuth result
    if (oauthSuccess === 'true') {
      setStatus('success');
      setMessage(`Successfully connected ${email || 'Gmail account'}!`);

      // Set flag for the main app to detect successful OAuth
      sessionStorage.setItem('oauth_in_progress', 'true');
      sessionStorage.setItem('oauth_success', 'true');
      if (email) {
        sessionStorage.setItem('oauth_email', email);
      }

      // Redirect back to the original page after a short delay
      setTimeout(() => {
        const returnPage = sessionStorage.getItem('oauth_return_page') || '/settings';
        sessionStorage.removeItem('oauth_return_page');
        window.location.href = returnPage;
      }, 2000);

    } else if (oauthError) {
      setStatus('error');
      setMessage(`Connection failed: ${oauthError}`);

      // Set error flag
      sessionStorage.setItem('oauth_error', oauthError);

      // Redirect back after delay
      setTimeout(() => {
        const returnPage = sessionStorage.getItem('oauth_return_page') || '/settings';
        sessionStorage.removeItem('oauth_return_page');
        window.location.href = returnPage;
      }, 3000);

    } else {
      // No clear success or error - might be processing
      setStatus('processing');
      setMessage('Processing authorization...');

      // Redirect after timeout
      setTimeout(() => {
        const returnPage = sessionStorage.getItem('oauth_return_page') || '/settings';
        sessionStorage.removeItem('oauth_return_page');
        window.location.href = returnPage;
      }, 5000);
    }
  }, []);

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <div className="text-center max-w-md mx-auto p-6">
        {status === 'processing' && (
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        )}
        {status === 'success' && (
          <div className="rounded-full h-12 w-12 bg-green-100 flex items-center justify-center mx-auto mb-4">
            <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )}
        {status === 'error' && (
          <div className="rounded-full h-12 w-12 bg-red-100 flex items-center justify-center mx-auto mb-4">
            <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        )}

        <h2 className={`text-lg font-semibold mb-2 ${
          status === 'success' ? 'text-green-900' :
          status === 'error' ? 'text-red-900' : 'text-gray-900'
        }`}>
          {status === 'success' ? 'Authorization Successful!' :
           status === 'error' ? 'Authorization Failed' :
           'Processing Gmail Authorization...'}
        </h2>

        <p className="text-gray-600 mb-4">
          {message}
        </p>

        <p className="text-sm text-gray-500">
          {status === 'processing' ? 'Please wait...' : 'Redirecting you back...'}
        </p>
      </div>
    </div>
  );
};

export default OAuthCallback;
